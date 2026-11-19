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
                self.assertEqual(doc.paragraphs[3].text, "")
                self.assertEqual(drafts.DATE, "")
                self.assertEqual(doc.core_properties.last_modified_by, "")
                self.assertIsNone(doc.core_properties.created)
                self.assertIsNone(doc.core_properties.modified)
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
            for forbidden in ("—", "–", "[[", "]]", "ПГО", "Discord", "ChatGPT",
                              "Правила проекта", "правила проекта", "правила сервера", "коллиз"):
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
            "Статья 19, часть 1",
            "Статья 19, часть 1, примечание 1",
            "Статья 19, часть 1, примечание 4",
            "Статья 4, пункт «в», фрагмент о доступе начальства",
            "Статья 4, пункт «д», фрагмент о доступе начальства",
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

    def test_projects_do_not_edit_the_same_provisions_as_each_other(self):
        def locators(bill):
            return {tuple(plain(left).split("\n", 2)[:2]) for left, _ in bill["rows"]}
        first, second = [bill for _, bill in self.bills]
        self.assertFalse(locators(first) & locators(second))
        for folder, _ in self.bills:
            explanation = (ROOT / "Законопроекты" / folder / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")
            self.assertIn("предварительный", explanation)
            self.assertIn("Дата в шапке оставлена пустой", explanation)
            self.assertNotIn("20.10.2026", explanation)
            self.assertIn("**Конституции**", explanation)
            self.assertIn("предварительного одобрения Федерального суда", explanation)
            for forbidden in ("Правила проекта", "правила проекта", "правила сервера", "коллиз"):
                self.assertNotIn(forbidden, explanation)


class NewBillSubstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r313 = rows_for(313)
        cls.r314 = rows_for(314)

    def test_release_escorting_and_transfer(self):
        text = self.r313["Статья 20, часть 3"]
        for expected in ("основания для освобождения", "решения уполномоченного лица об освобождении",
                         "инициатор задержания", "после передачи задержания",
                         "принявший задержанного сотрудник", "незамедлительно снять примененные наручники",
                         "освободить задержанного", "уведомляет освобожденного",
                         "присутствующего представителя его начальства", "указывает им путь к выходу",
                         "сопровождает освобожденного до выхода с объекта без ограничения его свободы",
                         "объективной невозможности личного сопровождения",
                         "сопровождение другим уполномоченным сотрудником",
                         "Приложением № 1 к Уголовному кодексу штата Сан-Андреас"):
            self.assertIn(expected, text)
        self.assertNotIn("статьей 4.1", text)

    def test_five_minutes_both_people_and_real_opportunity(self):
        text = self.r313["Статья 4.1. Выход после освобождения"]
        for expected in ("одному представителю его начальства", "в связи с задержанием",
                         "по 5 минут", "Для каждого срок начинается", "уведомления об освобождении",
                         "сообщения маршрута", "предоставления фактической возможности выхода",
                         "Время ожидания сопровождения", "препятствий, не зависящих от лица",
                         "в срок не входит", "Нахождение для выхода",
                         "является законным", "по иным законным основаниям"):
            self.assertIn(expected, text)
        self.assertIn("При отсутствии иного законного основания пребывания", text)
        self.assertNotIn("по истечении 5 минут подлежит задержанию", text)

    def test_confirmed_supervisor_is_subject_and_unconfirmed_is_not(self):
        text = self.r314["Статья 18, часть 1, пункт «е»"]
        for expected in ("Один представитель", "непосредственный или вышестоящий руководитель",
                         "сотрудника Weazel News", "Глава Коллегии адвокатов",
                         "для государственных и частных адвокатов, а также государственных юристов",
                         "при отсутствии обоих в штате для государственных адвокатов и государственных юристов - Старший адвокат",
                         "На месте задержания он подтверждает личность и полномочия сотруднику, проводящему задержание",
                         "После подтверждения он становится субъектом задержания в порядке части 2 настоящей статьи",
                         "служебным документам", "государственной базе данных", "служебной связи",
                         "Если лицо, законно находящееся на объекте, заявило, что является начальством задержанного, "
                         "то сотрудник без промедления проверяет его личность и полномочия.",
                         "сотрудник сопровождает его к месту задержания", "До окончания проверки",
                         "не удаляется с объекта только из-за отсутствия вызова или подтвержденных полномочий"):
            self.assertIn(expected, text)
        self.assertNotIn("другой представитель начальства в задержании не участвует", text)
        self.assertNotIn("обеспечивает проверку", text)
        from legal_sources import AD
        source = drafts.clean(billkit.load(AD)[4])
        self.assertIn("В случае отсутствия в штате Главы Коллегии Адвокатов и его заместителя", source)
        self.assertIn("Старший адвокат выступает в качестве руководства для задержанных государственных адвокатов и юристов", source)

    def test_initiator_calls_both_and_radio_restriction_is_only_for_supervisor(self):
        text = self.r314["Статья 19, часть 1"]
        self.assertIn("государственный служащий, государственный адвокат, сотрудник Weazel News "
                      "или частный адвокат с действующей лицензией", text)
        self.assertIn(
            "инициатор задержания обязан вызвать начальство задержанного, определяемое "
            "по пункту «е» части 1 статьи 18 настоящего Кодекса, и сотрудника Офиса Генерального "
            "прокурора штата Сан-Андреас.", text)
        self.assertNotIn("а сотрудник, проводящий задержание, - сотрудника", text)
        for expected in ("Инициатор вызывает начальство только по рации департамента",
                         "запрашивает вызов по служебной рации в порядке примечания 4",
                         "начальство уже находится на месте задержания", "подтвердило личность и полномочия",
                         "вызывать его не требуется", "не более, чем на 15 минут",
                         "время задержания замораживается до его приезда"):
            self.assertIn(expected, text)
        note = self.r314["Статья 19, часть 1, примечание 4"]
        for expected in ("у инициатора задержания нет доступа", "запрашивает вызов начальства по служебной рации",
                         "ожидает подтверждения от сотрудника, имеющего доступ к рации департамента",
                         "время задержания замораживается", "не более чем на 15 минут",
                         "включая ожидание ответа прокурора"):
            self.assertIn(expected, note)
        self.assertNotRegex((text + note).lower(), r"телефон|звон")
        release = self.r314["Статья 19, часть 1, примечание 1"]
        self.assertIn("не ответил на вызов в течение 15 минут", release)
        self.assertIn("в случае невозможности прибытия", release)
        self.assertIn("задержанный, указанный в настоящей части, подлежит освобождению", release)
        self.assertNotIn(",,", release)

    def test_entry_and_already_lawful_presence_in_both_facilities(self):
        fib = self.r314["Статья 4, пункт «в», фрагмент о доступе начальства"]
        district = self.r314["Статья 4, пункт «д», фрагмент о доступе начальства"]
        fib_body, district_body = fib.split("\n", 2)[2], district.split("\n", 2)[2]
        continuation = ", а также служащие органов правопорядка и военных органов в сопровождении руководства ФРБ;"
        self.assertTrue(fib_body.endswith(continuation))
        self.assertTrue(district_body.endswith(";"))
        self.assertEqual(fib_body.removesuffix(continuation), district_body.removesuffix(";"))
        for text in (fib, district):
            for expected in ("одно лицо, вызванное как начальство задержанного",
                             "законно находящееся на объекте", "заявившее о полномочиях начальства",
                             "для следования к месту задержания", "участия в задержании после подтверждения",
                             "личности и полномочий в порядке Процессуального кодекса штата Сан-Андреас"):
                self.assertIn(expected, text)
            self.assertNotRegex(text, r"(?:а также|или|и)\s*[;,.]?\s*$")
        self.assertNotIn("Форт Занкудо", fib + district)
        self.assertNotIn("авианосец", (fib + district).lower())

    def test_fib_continuation_is_unmodified_in_both_columns(self):
        folder, bill = next((folder, bill) for folder, bill in drafts.specs() if bill["num"] == 314)
        doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
        row = next(row for row in doc.tables[0].rows[1:]
                   if row.cells[0].paragraphs[1].text == "Статья 4, пункт «в», фрагмент о доступе начальства")
        continuation = ", а также служащие органов правопорядка и военных органов в сопровождении руководства ФРБ;"
        for cell in row.cells:
            self.assertTrue(cell.text.endswith(continuation))
            continuation_run = next(run for paragraph in cell.paragraphs for run in paragraph.runs
                                    if run.text == continuation)
            self.assertIsNone(continuation_run._r.rPr.find(qn("w:shd")))
        source = drafts.clean(billkit.load(drafts.APP)[7])
        old = row.cells[0].text.split("\n", 2)[2]
        new = row.cells[1].text.split("\n", 2)[2]
        self.assertEqual(source.count(old), 1)
        amended = source.replace(old, new, 1)
        self.assertIn(new, amended)
        self.assertEqual(amended.count(continuation), source.count(continuation))


if __name__ == "__main__":
    unittest.main()
