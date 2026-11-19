# -*- coding: utf-8 -*-
"""Сравнительные таблицы и совместимость исправленных инициатив SANG."""
import hashlib
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
import legal_sources as legal
import build_acts313_314 as release_drafts
import build_sang_299_300 as drafts
import check_docx

TOKEN = re.compile(r"\[\[/?(?:R|G|B)\]\]")


def plain(value):
    return TOKEN.sub("", value)


def document(folder, bill):
    return Document(drafts.OUT / folder / bill["file"])


def right_for(number):
    folder, bill = next((f, b) for f, b in drafts.specs() if b["num"] == number)
    return document(folder, bill).tables[0].rows[1].cells[1].text


def locators(bill):
    return {tuple(plain(left).split("\n", 2)[:2]) for left, _ in bill["rows"]}


class SangStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bills = drafts.specs()

    def test_files_form_dates_and_provenance(self):
        self.assertEqual([b["num"] for _, b in self.bills], [299, 300])
        self.assertEqual(drafts.DATE, "")
        original_hashes = {
            299: "38738885cf0910d3be858e4d68aaeeddf0baabfc91d0161d876316c1f34c06e7",
            300: "b277ea220e327cbfe7707fc39d3a4bf5a9620d52d396d4fe47ecab324e995de8",
        }
        for folder, bill in self.bills:
            path = drafts.OUT / folder / bill["file"]
            with self.subTest(number=bill["num"]):
                self.assertTrue(path.is_file())
                self.assertEqual(list(path.parent.glob("*.docx")), [path])
                self.assertTrue(path.name.startswith(f"ACT.{bill['num']}."))
                self.assertEqual(check_docx.check(str(path)), [])
                explanation = (path.parent / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")
                self.assertIn(original_hashes[bill["num"]], explanation)
                self.assertIn("16.11.2026", explanation)
                self.assertIn("Attest: Asher Keates", explanation)
                self.assertIn("не подтверждены", explanation)
                doc = Document(path)
                self.assertEqual(doc.paragraphs[0].text, f"ACT. {bill['num']}")
                self.assertEqual(doc.paragraphs[3].text, "")
                self.assertEqual(doc.core_properties.last_modified_by, "")
                self.assertIsNone(doc.core_properties.created)
                self.assertIsNone(doc.core_properties.modified)
                self.assertIn("SECTION 1. СУТЬ ПРАВКИ.", [p.text for p in doc.paragraphs])
                self.assertEqual([cell.text for cell in doc.tables[0].rows[0].cells],
                                 ["настоящая редакция", "предложенный вариант"])
                footer = doc.sections[0].footer.paragraphs[1].text
                self.assertIn("Attest: __________________", footer)
                self.assertNotIn("Asher Keates", footer)
                self.assertNotIn("Marcus Nomad", footer)
                self.assertEqual([e.text for e in doc.sections[0].footer._element.iter(qn("w:instrText"))],
                                 ["PAGE"])
                with zipfile.ZipFile(path) as package:
                    self.assertFalse(any(n.startswith("word/fonts/") for n in package.namelist()))

    def test_source_excerpts_marking_and_fonts(self):
        sources = {drafts.APP_TITLE: billkit.load(drafts.APP),
                   drafts.SANG_TITLE: billkit.load(drafts.SANG)}
        for folder, bill in self.bills:
            doc = document(folder, bill)
            self.assertEqual(len(doc.tables[0].rows), len(bill["rows"]) + 1)
            for row, (left, right) in zip(doc.tables[0].rows[1:], bill["rows"]):
                self.assertEqual(row.cells[0].text, plain(left))
                self.assertEqual(row.cells[1].text, plain(right))
                title, _, body = row.cells[0].text.split("\n", 2)
                if body != "В действующей редакции отсутствует.":
                    self.assertTrue(any(body in legal.clean(s) for s in sources[title].values()))
                self.assertTrue(all(cell.paragraphs[0].runs[0].bold for cell in row.cells))
                fills = lambda cell: [e.get(qn("w:fill")) for e in cell._tc.iter(qn("w:shd"))]
                self.assertIn("D9EAD3", fills(row.cells[1]))
                if "[[R]]" in left:
                    self.assertIn("F4CCCC", fills(row.cells[0]))
                for cell in row.cells:
                    self.assertTrue(all(p.paragraph_format.widow_control for p in cell.paragraphs))
            roots = [doc.element.body, doc.styles.element]
            for section in doc.sections:
                roots.extend((section.header._element, section.footer._element))
            for root in roots:
                for fonts in root.iter(qn("w:rFonts")):
                    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                        self.assertEqual(fonts.get(qn(attr)), "Times New Roman")
                    self.assertFalse(any(k.endswith("Theme") for k in fonts.attrib))
            for row in doc.tables[0].rows[1:]:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            if "Процессуального кодекса штата Сан-Андреас" in run.text:
                                self.assertTrue(run.bold, run.text)

    def test_no_forbidden_references_or_artifacts_in_user_documents(self):
        for folder, bill in self.bills:
            doc = document(folder, bill)
            text = "\n".join([p.text for p in doc.paragraphs] +
                             [c.text for row in doc.tables[0].rows for c in row.cells])
            note = (drafts.OUT / folder / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")
            for forbidden in ("—", "–", "[[", "]]", "ПГО", "Discord", "ChatGPT",
                              "Правила проекта", "правила проекта", "правила сервера", "коллиз"):
                self.assertNotIn(forbidden, text)
            for forbidden in ("Правила проекта", "правила проекта", "правила сервера", "коллиз"):
                self.assertNotIn(forbidden, note)
            self.assertNotRegex(text, r"\bID\b")

    def test_rebuild_from_base_without_originals(self):
        with TemporaryDirectory() as temp, patch.object(drafts, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                drafts.main()
            for folder, bill in self.bills:
                original = ROOT / "Законопроекты" / "Инициативы SANG" / folder / bill["file"]
                rebuilt = Path(temp) / folder / bill["file"]
                with self.subTest(number=bill["num"]), zipfile.ZipFile(original) as a, zipfile.ZipFile(rebuilt) as b:
                    self.assertEqual(set(a.namelist()), set(b.namelist()))
                    for name in a.namelist():
                        self.assertEqual(a.read(name), b.read(name), name)
        with TemporaryDirectory() as temp, patch.object(drafts, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                drafts.main(only=299)
            self.assertEqual(len(list(Path(temp).rglob("*.docx"))), 1)
            with self.assertRaises(ValueError):
                drafts.main(only=999)

    def test_original_root_inputs_removed_but_other_same_number_projects_preserved(self):
        self.assertFalse((ROOT / "ACT.299.docx").exists())
        self.assertFalse((ROOT / "ACT. 300.docx").exists())
        archived = ROOT / "Архив" / "Законопроекты 259-301 до обновления базы"
        expected = {
            "Законопроекты 299 (отстранение сенатора)/ACT.299.Конституционный закон о Сенате.docx":
                "cbf88f89e1a15f47b1d58b90246b1e6061711f70e706425dd6d2e8af9cca3c2a",
            "Законопроекты 300 (вызов прокурора руководством Коллегии)/ACT.300.Процессуальный кодекс.docx":
                "8bfe0d33b9a9af1d673c8c3ff8b2bcc7e3f7e48406529c6a92db0780dc09eb61",
        }
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((archived / name).read_bytes()).hexdigest(), digest)


class SangSubstanceTests(unittest.TestCase):
    def test_note_is_new_behind_fort_checkpoint_and_does_not_replace_existing_notes(self):
        app = billkit.load(drafts.APP)[7]
        fort = legal.excerpt(app, "а)\nФорт Занкудо", "\nб)\nАвианосец")
        self.assertIn("Примечание 1:", fort)
        self.assertNotIn("Примечание 1.1:", app)
        self.assertIn("Примечание 2: Государственные и частные адвокаты", app)
        text = right_for(299)
        for expected in ("Примечание 1.1:", "за контрольно-пропускным пунктом",
                         "обозначает принадлежность к Национальной гвардии", "указывает путь к выходу",
                         "достаточное время для выхода", "исполняющее требование и не задержанное",
                         "сопровождается военнослужащим до выхода", "непосредственной угрозы жизни или здоровью"):
            self.assertIn(expected, text)
        self.assertNotIn("Примечание 2", text)

    def test_detention_and_weapon_require_actual_conditions_not_blanket_permission(self):
        text = right_for(300)
        for expected in ("Форте-Занкудо или Авианосце", "покинуть объект",
                         "статьи 16 Процессуального кодекса штата Сан-Андреас",
                         "на Форте или около него", "против сотрудника Национальной гвардии",
                         "передать сотрудникам FIB, LSPD или LSCSD", "по статье 10 настоящего Закона",
                         "пресечении нарушения", "продолжающемся преследовании лица в действующем розыске",
                         "ордеру или решению суда",
                         "военнослужащих за военные преступления", "военном или чрезвычайном положении",
                         "по основаниям статьи 8 настоящего Закона", "статьи 37 указанного Кодекса",
                         "Невыполнение требования само по себе не дает права на стрельбу",
                         "предупреждает лицо о намерении применить оружие",
                         "дает возможность ответить", "непосредственной угрозы жизни или здоровью"):
            self.assertIn(expected, text)
        self.assertNotIn("открыть огонь на поражение без предупреждения", text)
        self.assertNotIn("Примечание 1.1", text)

    def test_projects_target_distinct_provisions_and_no_future_law_dependency(self):
        first, second = [b for _, b in drafts.specs()]
        self.assertFalse(locators(first) & locators(second))
        for _, other in release_drafts.specs():
            self.assertFalse(locators(first) & locators(other))
            self.assertFalse(locators(second) & locators(other))
        self.assertNotIn("ACT. 300", right_for(299))
        self.assertNotIn("ACT. 299", right_for(300))
        self.assertNotIn("статьей 4.1", right_for(299) + right_for(300))


if __name__ == "__main__":
    unittest.main()
