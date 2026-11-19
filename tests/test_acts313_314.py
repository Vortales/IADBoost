# -*- coding: utf-8 -*-
"""Форма, источники и ключевые гарантии проектов ACT. 313-314."""
import re
import sys
import unittest
import zipfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import billkit
import build_acts302_312 as earlier
import build_acts313_314 as drafts
import check_docx

TOKEN = re.compile(r"\[\[/?(?:R|G|B)\]\]")


def plain(text):
    return TOKEN.sub("", text)


def rows_for(number):
    found = [(folder, bill) for folder, bill in drafts.specs() if bill["num"] == number]
    if len(found) != 1:
        raise AssertionError(number)
    folder, bill = found[0]
    doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
    return {row.cells[1].paragraphs[1].text: row.cells[1].text
            for row in doc.tables[0].rows[1:]}


class NewBillStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bills = drafts.specs()

    def test_separate_docx_and_explanations(self):
        self.assertEqual([bill["num"] for _, bill in self.bills], [313, 314])
        for folder, bill in self.bills:
            path = ROOT / "Законопроекты" / folder / bill["file"]
            with self.subTest(number=bill["num"]):
                self.assertTrue(path.is_file())
                self.assertTrue((path.parent / "ПОЯСНЕНИЕ К ПАПКЕ.md").is_file())
                self.assertEqual(list(path.parent.glob("*.docx")), [path])
                self.assertTrue(path.name.startswith(f"ACT.{bill['num']}."))
                self.assertNotRegex(path.name, r"[()]")
                self.assertEqual(check_docx.check(str(path)), [])
                doc = Document(path)
                self.assertEqual(doc.paragraphs[0].text, f"ACT. {bill['num']}")
                self.assertEqual(doc.paragraphs[3].text, drafts.DATE)
                self.assertIn("IN THE SENATE OF THE STATE OF SAN ANDREAS",
                              [p.text for p in doc.paragraphs])
                self.assertIn("SECTION 1. СУТЬ ПРАВКИ.", [p.text for p in doc.paragraphs])
                self.assertEqual([c.text for c in doc.tables[0].rows[0].cells],
                                 ["настоящая редакция", "предложенный вариант"])
                self.assertIn("Attest: Marcus Nomad", doc.sections[0].footer.paragraphs[1].text)
                with zipfile.ZipFile(path) as package:
                    self.assertFalse(any(name.startswith("word/fonts/") for name in package.namelist()))

    def test_comparisons_match_sources_and_color_changes(self):
        sources = {
            drafts.PC_TITLE: [drafts.clean(text) for text in billkit.load(drafts.PC).values()],
            drafts.APP_TITLE: [drafts.clean(text) for text in billkit.load(drafts.APP).values()],
        }
        for folder, bill in self.bills:
            doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
            self.assertEqual(len(doc.tables[0].rows), len(bill["rows"]) + 1)
            for row, (left, right) in zip(doc.tables[0].rows[1:], bill["rows"]):
                with self.subTest(number=bill["num"], locator=plain(left).split("\n")[1]):
                    self.assertEqual(row.cells[0].text, plain(left))
                    self.assertEqual(row.cells[1].text, plain(right))
                    title, locator, body = row.cells[0].text.split("\n", 2)
                    self.assertIn(title, sources)
                    if body != "В действующей редакции отсутствует.":
                        self.assertTrue(any(body in source for source in sources[title]), locator)
                    for cell in row.cells:
                        self.assertTrue(cell.paragraphs[0].runs[0].bold)
                        self.assertTrue(all(p.paragraph_format.widow_control for p in cell.paragraphs))
                    fills = lambda cell: [item.get(qn("w:fill")) for item in cell._tc.iter(qn("w:shd"))]
                    self.assertIn("D9EAD3", fills(row.cells[1]))
                    if "[[R]]" in left:
                        self.assertIn("F4CCCC", fills(row.cells[0]))

    def test_fonts_bold_titles_and_no_formatting_leaks(self):
        for folder, bill in self.bills:
            doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
            roots = [doc.element.body, doc.styles.element]
            for section in doc.sections:
                roots.extend((section.header._element, section.footer._element))
            for root in roots:
                for fonts in root.iter(qn("w:rFonts")):
                    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                        self.assertEqual(fonts.get(qn(attr)), "Times New Roman", (bill["num"], attr))
                    self.assertFalse(any(key.endswith("Theme") for key in fonts.attrib))
            all_cells = [cell for row in doc.tables[0].rows for cell in row.cells]
            all_text = "\n".join([p.text for p in doc.paragraphs] + [cell.text for cell in all_cells])
            for forbidden in ("—", "–", "[[", "]]", "ПГО", "Discord", "ChatGPT"):
                self.assertNotIn(forbidden, all_text, bill["num"])
            self.assertNotRegex(all_text, r"\bID\b")
            for cell in all_cells[2:]:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if ("Процессуального кодекса штата Сан-Андреас" in run.text
                                or "Приложения № 1 к Уголовному кодексу штата Сан-Андреас" in run.text):
                            self.assertTrue(run.bold, run.text)

    def test_short_comparison_rows_do_not_split(self):
        folder, bill = self.bills[1]
        doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
        self.assertEqual(set(bill["keep_rows_together"]), {
            "Статья 18, часть 1, пункт «е»",
            "Статья 4, пункт «в», доступ начальства",
            "Статья 4, пункт «д», доступ начальства",
        })
        for row, (left, right) in zip(doc.tables[0].rows[1:], bill["rows"]):
            locator = plain(left).split("\n")[1]
            if locator in bill["keep_rows_together"]:
                self.assertLess(max(len(left), len(right)), 1200)
                self.assertIsNotNone(row._tr.trPr.find(qn("w:cantSplit")), locator)

    def test_new_provisions_absent_and_no_duplicate_article_heading(self):
        pc = billkit.load(drafts.PC)
        app = billkit.load(drafts.APP)
        self.assertNotIn("ч. 3.", pc[33])
        self.assertNotRegex("\n".join(app.values()), r"Статья\s+4\.1(?:\D|$)")
        provision = rows_for(313)["Статья 4.1. Выход после освобождения"]
        self.assertEqual(provision.count("Статья 4.1"), 1)

    def test_rebuild_isolated_and_reproducible(self):
        with TemporaryDirectory() as temp, patch.object(drafts, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                drafts.main()
            for folder, bill in self.bills:
                original = ROOT / "Законопроекты" / folder / bill["file"]
                rebuilt = Path(temp) / folder / bill["file"]
                with self.subTest(number=bill["num"]), zipfile.ZipFile(original) as a, zipfile.ZipFile(rebuilt) as b:
                    self.assertEqual(set(a.namelist()), set(b.namelist()))
                    for name in a.namelist():
                        self.assertEqual(a.read(name), b.read(name), name)
        with TemporaryDirectory() as temp, patch.object(drafts, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                drafts.main(only=314)
            self.assertEqual(len(list(Path(temp).rglob("*.docx"))), 1)
            self.assertTrue(next(Path(temp).rglob("*.docx")).name.startswith("ACT.314."))
            with self.assertRaises(ValueError):
                drafts.main(only=999)

    def test_projects_do_not_edit_the_same_provisions_as_each_other_or_act302(self):
        def locators(bill):
            return {tuple(plain(left).split("\n", 2)[:2]) for left, _ in bill["rows"]}
        first, second = [bill for _, bill in self.bills]
        original302 = earlier.specs()[0][1]
        self.assertFalse(locators(first) & locators(second))
        self.assertFalse(locators(first) & locators(original302))
        self.assertFalse(locators(second) & locators(original302))
        for folder, _ in self.bills:
            explanation = (ROOT / "Законопроекты" / folder / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")
            self.assertIn("предварительный", explanation)
            self.assertIn("20.10.2026", explanation)
            self.assertIn("ноябрю 2026", explanation)
            self.assertIn("необходимо уточнить до подачи", explanation)


class NewBillSubstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r313 = rows_for(313)
        cls.r314 = rows_for(314)

    def test_release_escorting_and_transfer(self):
        text = self.r313["Статья 20, часть 3"]
        for expected in ("предусмотренного законом основания для освобождения",
                         "решения уполномоченного лица об освобождении задержанного",
                         "инициатор задержания", "передачи задержания", "сотрудник, принявший задержанного",
                         "незамедлительно освободить задержанного: снять примененные наручники", "прекратить ограничение свободы",
                         "сообщить об освобождении", "присутствующему представителю его начальства",
                         "сообщить им маршрут выхода", "сопроводить освобожденного до выхода с объекта",
                         "объективной невозможности личного сопровождения",
                         "сопровождение другим уполномоченным сотрудником", "статьей 4.1"):
            self.assertIn(expected, text)

    def test_five_minutes_both_people_and_real_opportunity(self):
        text = self.r313["Статья 4.1. Выход после освобождения"]
        for expected in ("одному представителю его начальства", "в связи с этим задержанием",
                         "по 5 минут", "Для каждого лица срок исчисляется", "уведомления об освобождении",
                         "сообщения маршрута выхода", "предоставления фактической возможности",
                         "ожидания сопровождения", "не зависящих от лица препятствий",
                         "в срок не засчитывается", "не является незаконным",
                         "по иным предусмотренным законом основаниям"):
            self.assertIn(expected, text)
        self.assertIn("При отсутствии иного законного основания пребывания", text)
        self.assertNotIn("по истечении 5 минут подлежит задержанию", text)

    def test_confirmed_supervisor_is_subject_and_unconfirmed_is_not(self):
        text = self.r314["Статья 18, часть 1, пункт «е»"]
        for expected in ("Один представитель", "непосредственный либо вышестоящий руководитель",
                         "которому он подчинен", "сотрудника Weazel News", "Глава Коллегии адвокатов",
                         "с момента подтверждения на месте задержания", "своей личности и полномочий",
                         "служебным документам", "государственной базы данных", "служебной связи",
                         "другой представитель начальства не участвует",
                         "без промедления обеспечивает проверку личности и полномочий",
                         "сопровождение к месту задержания", "До окончания проверки",
                         "не удаляется как постороннее", "отсутствия вызова",
                         "При неподтверждении полномочий участие не допускается"):
            self.assertIn(expected, text)

    def test_initiator_calls_phone_or_radio_without_consuming_detainee_call(self):
        text = self.r314["Статья 19, часть 1"]
        for expected in ("сотрудником, проводящим задержание, по рации департамента",
                         "телефонным звонком с его телефона непосредственно начальству",
                         "личность задержанного, основание и место задержания",
                         "телефонный вызов не принят или номер начальства неизвестен",
                         "без промедления вызывает начальство по рации департамента",
                         "Изменение способа вызова не начинает срок ожидания заново",
                         "не расходует телефонный звонок задержанного",
                         "подтвердило полномочия", "отдельный вызов этого лица не требуется",
                         "обязанность вызвать прокурора сохраняется",
                         "не более, чем на 15 минут", "время задержания замораживается до его приезда"):
            self.assertIn(expected, text)
        note = self.r314["Статья 19, часть 1, примечание 4"]
        self.assertIn("через служебную рацию", note)
        self.assertIn("подтверждения направления вызова", note)
        self.assertIn("не более чем на 15 минут", note)

    def test_entry_and_already_lawful_presence_in_both_facilities(self):
        fib = self.r314["Статья 4, пункт «в», доступ начальства"]
        district = self.r314["Статья 4, пункт «д», доступ начальства"]
        self.assertEqual(fib.split("\n", 2)[2].removesuffix("; а также"), district.split("\n", 2)[2])
        for text in (fib, district):
            for expected in ("один представитель начальства задержанного", "по вызову сотрудника",
                             "законно находившееся на объекте на момент обращения к сотруднику",
                             "непосредственно до следования к месту задержания",
                             "для следования к месту задержания, сообщения о полномочиях начальства",
                             "их проверки и участия при подтверждении",
                             "если другой представитель начальства задержанного не участвует"):
                self.assertIn(expected, text)
        self.assertNotIn("Форт Занкудо", fib + district)
        self.assertNotIn("авианосец", (fib + district).lower())


if __name__ == "__main__":
    unittest.main()
