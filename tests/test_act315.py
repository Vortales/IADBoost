# -*- coding: utf-8 -*-
"""Адресность, форма и правовые гарантии ACT. 315."""
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
import build_act315 as draft
import build_acts302_312 as earlier
import build_acts313_314 as prior
import build_sang_299_300 as sang
import check_docx


def plain(value):
    return draft.plain(value)


class Act315Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bill, cls.patches, cls.documents = draft.specs()
        cls.final = draft.apply_patches(cls.patches, cls.documents)
        cls.path = draft.OUT / cls.bill["file"]
        cls.doc = Document(cls.path)
        cls.proposed = {p.locator: p.new for p in cls.patches}
        cls.notes = (draft.OUT / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")

    def test_form_dates_provenance_and_footer(self):
        self.assertTrue(self.path.name.startswith("ACT.315."))
        self.assertEqual(check_docx.check(str(self.path)), [])
        self.assertEqual(list(draft.OUT.glob("*.docx")), [self.path])
        self.assertEqual(self.doc.paragraphs[0].text, "ACT. 315")
        self.assertEqual(self.doc.paragraphs[3].text, "")
        self.assertEqual(self.doc.core_properties.author, "")
        self.assertEqual(self.doc.core_properties.last_modified_by, "")
        self.assertIsNone(self.doc.core_properties.created)
        self.assertIsNone(self.doc.core_properties.modified)
        paragraphs = [p.text for p in self.doc.paragraphs]
        self.assertIn("IN THE SENATE OF THE STATE OF SAN ANDREAS", paragraphs)
        self.assertIn("SECTION 1. СУТЬ ПРАВКИ.", paragraphs)
        table = self.doc.tables[0]
        self.assertEqual([c.text for c in table.rows[0].cells],
                         ["настоящая редакция", "предложенный вариант"])
        half = (self.doc.sections[0].page_width.twips - 864) // 2
        self.assertEqual([col.width.twips for col in table.columns], [half, half])
        self.assertEqual(int(table._tbl.tblPr.find(qn("w:tblInd")).get(qn("w:w"))),
                         432 - self.doc.sections[0].left_margin.twips)
        self.assertEqual(table._tbl.getnext().tag, qn("w:sectPr"))
        footer = self.doc.sections[0].footer.paragraphs[1]
        self.assertIn("Attest: __________________", footer.text)
        self.assertNotIn("Marcus Nomad", footer.text)
        self.assertLessEqual(footer.text.count("\t"), 6)
        self.assertEqual([e.text for e in footer._element.iter(qn("w:instrText"))], ["PAGE"])
        for expected in ("предварительный", "11.11.2026", "15.11.2026", "позднее даты проверки 20.10.2026",
                         "хронология среза требуют проверки",
                         "защитную страницу", "части 1-2 статьи 2", "не вправе применять противоречащий ему закон",
                         "Поправка 8", "ACT. 313", "ACT. 314",
                         "ACT. 302", "SANG ACT. 299", "SANG ACT. 300"):
            self.assertIn(expected, self.notes)

    def test_every_comparison_is_source_exact_and_changes_are_colored(self):
        self.assertEqual(len(self.bill["rows"]), len(self.patches))
        self.assertEqual(len(self.doc.tables[0].rows), len(self.patches) + 1)
        for row, (left, right), item in zip(self.doc.tables[0].rows[1:], self.bill["rows"], self.patches):
            with self.subTest(locator=item.locator):
                self.assertEqual(row.cells[0].text, plain(left))
                self.assertEqual(row.cells[1].text, plain(right))
                header, locator, body = row.cells[0].text.split("\n", 2)
                self.assertEqual(locator, item.locator)
                self.assertTrue(all(cell.paragraphs[0].runs[0].bold for cell in row.cells))
                self.assertTrue(all(p.paragraph_format.keep_with_next is False for cell in row.cells
                                    for p in cell.paragraphs[:2]))
                self.assertTrue(all(p.paragraph_format.widow_control for cell in row.cells for p in cell.paragraphs))
                fills = lambda cell: [el.get(qn("w:fill")) for el in cell._tc.iter(qn("w:shd"))]
                self.assertIn("D9EAD3", fills(row.cells[1]))
                if item.old:
                    self.assertEqual(body, item.old)
                    self.assertEqual(draft.clean(self.documents[item.source][item.section]).count(body), 1)
                    self.assertIn("F4CCCC", fills(row.cells[0]))
                    if item.new:
                        self.assertEqual(row.cells[1].text.split("\n", 2)[2], item.new)
                else:
                    self.assertEqual(body, "В действующей редакции отсутствует.")
                    self.assertEqual(row.cells[1].text.split("\n", 2)[2], item.new)
                if item.locator in self.bill["keep_rows_together"]:
                    self.assertIsNotNone(row._tr.trPr.find(qn("w:cantSplit")))

    def test_font_bold_titles_balanced_quotes_and_no_forbidden_content(self):
        roots = [self.doc.element.body, self.doc.styles.element]
        for section in self.doc.sections:
            roots.extend([section.header._element, section.footer._element])
        for root in roots:
            for fonts in root.iter(qn("w:rFonts")):
                for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                    self.assertEqual(fonts.get(qn(attr)), "Times New Roman")
                self.assertFalse(any(key.endswith("Theme") for key in fonts.attrib))
        text = "\n".join([p.text for p in self.doc.paragraphs] +
                         [cell.text for row in self.doc.tables[0].rows for cell in row.cells])
        for forbidden in ("—", "–", "[[", "]]", "ПГО", "ChatGPT", "Discord", "Правила проекта",
                          "правила проекта", "правила сервера"):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"\bID\b")
        for row in self.doc.tables[0].rows[1:]:
            proposal = row.cells[1].text.split("\n", 2)[2]
            self.assertEqual(proposal.count("«"), proposal.count("»"), proposal)
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if any(x in run.text for x in (
                            "Процессуального кодекса штата Сан-Андреас",
                            "Закона «Об Экстренной Медицинской Службе",
                            "Законом «Об адвокатской деятельности",
                            "Конституционного закона «О судебной системе",
                            "Приложением № 1 к Уголовному кодексу штата San-Andreas",
                        )):
                            self.assertTrue(run.bold, run.text)
        for forbidden in ("Правила проекта", "правила проекта", "правила сервера", "коллиз"):
            self.assertNotIn(forbidden, self.notes)
        with zipfile.ZipFile(self.path) as package:
            self.assertFalse(any(n.startswith("word/fonts/") for n in package.namelist()))

    def test_rebuild_isolated_and_deterministic(self):
        with TemporaryDirectory() as temp, patch.object(draft, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                draft.main()
            rebuilt = Path(temp) / self.bill["file"]
            with zipfile.ZipFile(self.path) as original, zipfile.ZipFile(rebuilt) as new:
                self.assertEqual(set(original.namelist()), set(new.namelist()))
                for name in original.namelist():
                    self.assertEqual(original.read(name), new.read(name), name)

    def test_whole_appendix_scope_and_existing_special_objects(self):
        touched = {p.section for p in self.patches if p.source == draft.APP}
        self.assertEqual(touched, {1, 3, 4, 5, 7, 8, 9, 10, 11})
        original = draft.clean(self.documents[draft.APP][4])
        changed = self.final[draft.APP, 4]
        examples = original[original.index("- LSPD/LSCSD"):original.index("\nПримечание 1.")]
        self.assertIn(examples, changed)
        article3 = self.final[draft.APP, 5]
        for expected in ("Форт Занкудо", "Офис Федерального Расследовательского Бюро",
                         "Авианосец и воды в радиусе 1 мили", "за исключением территории аэропорта"):
            self.assertIn(expected, article3)
        self.assertNotIn("Аэропорт на территории острова является открытой", self.final[draft.APP, 7])
        definitions = self.final[draft.APP, 3]
        self.assertIn("иным законом", definitions)
        self.assertIn("Прилегающая территория для целей настоящего Приложения", definitions)
        self.assertIn("независимо от его обозначения на схемах", definitions)
        self.assertIn("Земельные участки, здания, сооружения и акватории, находящиеся", changed)
        self.assertIn("ведении или на балансе государственных структур штата, относятся к охраняемым объектам", changed)
        self.assertNotIn("Объекты, определенные статьей 1", changed)
        halls = self.proposed["Статья 6, режим визуализации и прилегающих территорий"]
        self.assertIn("входные холлы охраняемых объектов, не отнесенных к особо охраняемым", halls)
        self.assertIn("холлы особо охраняемых объектов, обозначенные на схемах белым цветом", halls)
        self.assertIn("Иные помещения объекта сохраняют установленный для них режим", halls)

    def test_fort_white_zone_is_free_but_independent_measures_survive(self):
        note = self.proposed["Статья 4, пункт «а», примечание 1"]
        for expected in ("до линий КПП", "примыкающие к ним подъезды", "свободна для посещения",
                         "обозначение белым цветом не является условием", "не требуются цель визита, пропуск или сопровождение",
                         "без законного основания, в том числе в обход КПП", "зафиксировано нарушение уголовного законодательства",
                         "указав основание и путь выхода", "достаточное время", "самостоятельным законным основаниям"):
            self.assertIn(expected, note)
        self.assertNotIn("2 км", note)
        visual = self.proposed["Статья 6, режим визуализации и прилегающих территорий"]
        self.assertIn("перечень целей", visual.lower())
        self.assertIn("является открытым", visual)
        self.assertIn("На прилегающей территории Форта-Занкудо цель посещения не требуется", visual)
        self.assertIn("Кроме прилегающей территории Форта", visual)
        self.assertIn("достаточное время", visual)
        rights = self.proposed["Статья 7, права сотрудников"]
        self.assertIn("само по себе не является основанием", rights)
        self.assertIn("в случаях, предусмотренных законодательством", rights)
        self.assertIn("в порядке Процессуального кодекса", rights)
        part6 = self.proposed["Статья 2, часть 6"]
        self.assertIn("окрестности Форта-Занкудо являются местом государственной охраны", part6)
        self.assertIn("при пересечении границы территории Форта и на самой территории", part6)

    def test_numbering_subjects_and_no_unlimited_oversight(self):
        app = self.final[draft.APP, 7]
        self.assertEqual([int(x) for x in re.findall(r"(?m)^Примечание (\d+):", app)], list(range(1, 9)))
        self.assertNotIn("Примечание 4: Частные адвокаты", app)
        self.assertNotIn("Примечание 5: Сотрудники Экстренной", app)
        self.assertNotIn("посетители допускаются на территорию холла WN", app)
        for phrase in ("К КПЗ не относятся раздевалка и оружейный склад", "самостоятельного законного основания",
                       "субъекты задержания в случаях и пределах статьи 18", "не предоставляет доступа в иные помещения",
                       "права надзора вне конкретного задержания", "части 11 статьи 18", "сотрудники Новостного агентства"):
            self.assertIn(phrase, app)
        pc18 = billkit.load("Процессуальный кодекс штата Сан-Андреас")[31]
        self.assertIn("IAD (Internal Affairs Division) соответствующего ведомства", pc18)
        self.assertIn("на территории своего департамента", pc18)
        for locator in ("Статья 4, пункт «в», доступ начальства и сопровождаемых служащих",
                        "Статья 4, пункт «д», доступ начальства"):
            self.assertIn("один представитель начальства задержанного", self.proposed[locator])
        continuation = "а также служащие органов правопорядка и военных органов в сопровождении руководства ФРБ;"
        self.assertTrue(self.proposed["Статья 4, пункт «в», доступ начальства и сопровождаемых служащих"].endswith(continuation))
        for text in (self.proposed["Статья 4, примечание 2"], self.proposed["Статья 4, примечание 3"]):
            self.assertIn("5 минут", text)
            self.assertIn("иного законного основания", text)
        self.assertIn("Порядок исчисления срока определяется примечанием 3", self.proposed["Статья 4, примечание 2"])
        shared = self.proposed["Статья 4, примечание 3"]
        self.assertIn("примечанию 2 и настоящему примечанию", shared)
        self.assertIn("фактической возможности выхода", shared)
        self.assertIn("ожидания необходимого сопровождения", shared)
        self.assertIn("не зависящих от лица препятствий", shared)

    def test_access_ems_lawyers_and_court_process(self):
        lawyer = self.proposed["Статья 4, примечание 2"]
        self.assertIn("Государственные и частные адвокаты", lawyer)
        self.assertIn("статьями 17, 18 и 22 Процессуального кодекса", lawyer)
        self.assertNotIn("только в рамках вызова через телефон", lawyer)
        advocate_law = self.proposed["Статья 4, часть 2, пункт «ж»"]
        self.assertIn("примечанием 2 статьи 4 Приложения", advocate_law)
        self.assertIn("КПЗ FIB, LSPD и LSCSD", advocate_law)
        self.assertIn("если адвокат не является субъектом задержания", advocate_law)
        medical_access = self.proposed["Статья 4, пункт «е», доступ адвокатов в медицинские учреждения"]
        self.assertIn("статьями 4 и 7.1 Закона «Об адвокатской деятельности", medical_access)
        self.assertIn("режима учреждения и врачебной тайны", medical_access)
        ems = self.proposed["Статья 4, примечание 3"]
        self.assertIn("статьей 3 Закона «Об Экстренной Медицинской Службе", ems)
        self.assertIn("пункта «м» части 1 статьи 18", ems)
        screening = self.proposed["Статья 5, часть 1.2, досмотр"]
        self.assertIn("уполномоченным лицом", screening)
        self.assertIn("с учетом исключений", screening)
        self.assertIn("статьей 29 Процессуального кодекса", screening)
        self.assertIn("оснований и в порядке статьи 29", self.proposed["Статья 42, часть 8"])
        public = self.proposed["Статья 5, часть 1.4"]
        self.assertIn("Отсутствие статуса участника", public)
        self.assertIn("После начала заседания", public)
        self.assertIn("с разрешения судьи", public)
        self.assertIn("части 1.3", self.proposed["Статья 5, часть 1.1"])
        self.assertIn("прямо установленных законодательством", self.proposed["Статья 5, часть 1.2, внешний вид"])

    def test_pass_issuer_and_independent_access(self):
        p = self.proposed["Статья 8, часть 1"]
        for expected in ("для которого статья 4", "указанные для этого объекта лица",
                         "на иные закрытые территории", "за которым закреплена территория",
                         "не более 30 дней", "иного прямо предусмотренного законом основания доступа"):
            self.assertIn(expected, p.lower() if expected == "на иные закрытые территории" else p)
        self.assertIn("в письменной форме", self.proposed["Статья 8, часть 2, порядок оформления"])
        self.assertIn("за которым закреплена территория", self.proposed["Статья 8, часть 3"])
        self.assertIn("ту же территорию", self.proposed["Статья 8, часть 6"])
        self.assertIn("Запрет не ограничивает доступ на ином законном основании", self.proposed["Статья 8, часть 6"])
        self.assertIn("не ограничивает случаи и условия сопровождения", self.proposed["Статья 8, часть 7"])

    def test_fort_measures_and_recording_are_law_bound(self):
        guard = self.proposed["Статья 2, часть 7"]
        for expected in ("незаконно находящегося", "которое не задержано", "достаточное время",
                         "сопровождает такое лицо, исполняющее требование", "до выхода через КПП",
                         "по подозрению в совершении преступления", "уполномоченным военнослужащим по статьям 15 и 16",
                         "с передачей задержанного", "уполномоченному сотруднику FIB, LSPD или LSCSD",
                         "если иное не предусмотрено законом", "по статье 25",
                         "военнослужащих за военные преступления", "военном или чрезвычайном положении",
                         "по основаниям статьи 8", "в порядке статьи 37", "не является основанием",
                         "предупреждает лицо", "дает возможность исполнить требование"):
            self.assertIn(expected.lower(), guard.lower())
        stop = self.final[draft.SANG, 13]
        self.assertNotIn("право останавливать и досматривать лиц", stop)
        self.assertIn("Личный досмотр и обыск, установление личности и задержание", stop)
        self.assertIn("Остановка сама по себе не является их основанием", stop)
        self.assertIn("Исключение: Государственные служащие при исполнении", stop)
        record = self.proposed["Статья 14.4, примечание"]
        for expected in ("прямо предусмотренную или разрешенную законом", "в установленном им порядке",
                         "обязательную видеозапись по статье 32", "врачебной и адвокатской тайны"):
            self.assertIn(expected, record)
        special_recording = self.final[draft.SANG, 4]
        self.assertIn("На территориях военной базы Форт-Занкудо и Авианосца запрещена любая", special_recording)
        self.assertIn("кроме обязательной видеозаписи по статье 32 Процессуального кодекса", special_recording)
        self.assertIn("Исключение: Вести фото/видео/аудио фиксацию", special_recording)
        self.assertIn("Сотрудники государственных силовых структур", special_recording)
        self.assertIn("Сотрудники SANG, Губернатор", special_recording)

    def test_pending_proposals_are_not_treated_as_source(self):
        app = self.final[draft.APP, 7]
        self.assertNotIn("Примечание 1.1:", app)
        self.assertNotIn("Примечание 2.1:", app)
        self.assertNotIn("Статья 4.1", "\n".join(self.final[draft.APP, n] for n in (1, 3, 4, 5, 7, 8, 9, 10, 11)))
        prior314 = next(b for _, b in prior.specs() if b["num"] == 314)
        prior_text = "\n".join(plain(left) for left, _ in prior314["rows"])
        for locator in ("Статья 4, пункт «в», доступ начальства и сопровождаемых служащих",
                        "Статья 4, пункт «д», доступ начальства"):
            item = next(p for p in self.patches if p.locator == locator)
            self.assertIn(item.old.rstrip(";"), prior_text)
        self.assertIn("Статья 2, часть 7", "\n".join(plain(left) for left, _ in sang.specs()[1][1]["rows"]))
        self.assertIn("Примечание 2.1", "\n".join(plain(right) for _, right in earlier.specs()[0][1]["rows"]))


if __name__ == "__main__":
    unittest.main()
