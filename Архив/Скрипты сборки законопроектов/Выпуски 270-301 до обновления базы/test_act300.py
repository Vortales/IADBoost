# -*- coding: utf-8 -*-
"""Проверки нового проекта ACT. 300 и его стыковки с ACT. 294."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from docx import Document
from docx.oxml.ns import qn
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_act300 as bill  # noqa: E402
from billkit import load  # noqa: E402
from check_docx import check  # noqa: E402

ACT300 = bill.OUT / bill.FILE
ACT294 = (
    ROOT / "Законопроекты" / "Законопроекты 294 (вызов прокурора адвокатом)"
    / "ACT.294.Процессуальный кодекс (вызов прокурора адвокатом).docx"
)
BASE_PC = ROOT / "Законодательная база" / (bill.PC + ".json")
REFERENCE_PC = ROOT / "Новая законка" / (bill.PC + ".json")


class Act300Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = Document(ACT300)
        cls.table = cls.doc.tables[0]
        cls.source = load(bill.PC)

    def test_source_and_new_locators(self):
        self.assertEqual(BASE_PC.read_bytes(), REFERENCE_PC.read_bytes())
        bill.validate_source()
        self.assertFalse(any(
            re.match(r"^\s*Статья\s+8\.1(?:\D|$)", text)
            for text in self.source.values()
        ))
        part2 = self.source[33].split("ч. 2.\n", 1)[1]
        self.assertIsNone(re.search(r"^\s*ж\)", part2, re.MULTILINE))
        self.assertIn("статьёй 8.1 настоящего Кодекса", bill.NEW_POINT)

    def test_builder_rejects_occupied_article_or_point(self):
        occupied = dict(self.source)
        occupied[9999] = "Статья 8.1\nУже принятая норма"
        with patch.object(bill, "load", return_value=occupied):
            with self.assertRaisesRegex(AssertionError, "Статья 8.1"):
                bill.validate_source()
        occupied = dict(self.source)
        occupied[33] += "\nж) Уже действующий пункт."
        with patch.object(bill, "load", return_value=occupied):
            with self.assertRaisesRegex(AssertionError, "Пункт «ж»"):
                bill.validate_source()

    def test_docx_structure_and_exact_proposed_text(self):
        self.assertEqual([], check(str(ACT300)))
        pars = [p.text for p in self.doc.paragraphs]
        self.assertEqual("ACT. 300", pars[0])
        self.assertEqual("IN THE SENATE OF THE STATE OF SAN ANDREAS", pars[2])
        self.assertEqual("NOVEMBER 13, 2026", pars[3])
        self.assertEqual("SECTION 1. СУТЬ ПРАВКИ.", pars[8])
        self.assertEqual(["настоящая редакция", "предложенный вариант"],
                         [cell.text for cell in self.table.rows[0].cells])
        self.assertEqual(3, len(self.table.rows))
        for row, locator, text in (
            (self.table.rows[1], "Статья 8.1", bill.NEW_ARTICLE),
            (self.table.rows[2], "Статья 20, часть 2, пункт «ж»", bill.NEW_POINT),
        ):
            heading = f"{bill.PC}\n{locator}\n"
            self.assertEqual(heading + "В действующей редакции отсутствует.",
                             row.cells[0].text)
            self.assertEqual(heading + text, row.cells[1].text)

    def test_formatting_fonts_dashes_and_bold_act_names(self):
        all_paragraphs = list(self.doc.paragraphs)
        for row in self.table.rows:
            for cell in row.cells:
                all_paragraphs.extend(cell.paragraphs)
        full_text = "\n".join(p.text for p in all_paragraphs)
        self.assertNotRegex(full_text, r"[—–−→]")
        self.assertNotIn("[[", full_text)
        self.assertNotIn("]]", full_text)
        title_runs = [r for p in all_paragraphs for r in p.runs if bill.PC in r.text]
        self.assertGreaterEqual(len(title_runs), 6)
        self.assertTrue(all(r.bold for r in title_runs))
        for row in self.table.rows[1:]:
            for p in row.cells[1].paragraphs[2:]:
                for run in p.runs:
                    if run.text:
                        shading = run._r.rPr.find(qn("w:shd"))
                        self.assertIsNotNone(shading)
                        self.assertEqual("D9EAD3", shading.get(qn("w:fill")))
            for p in row.cells[0].paragraphs:
                for run in p.runs:
                    self.assertIsNone(run._r.rPr.find(qn("w:shd")))
        with zipfile.ZipFile(ACT300) as archive:
            font_parts = [n for n in archive.namelist()
                          if n in {"word/document.xml", "word/styles.xml"}
                          or re.match(r"word/(?:header|footer)\d+\.xml$", n)]
            for name in font_parts:
                root = etree.fromstring(archive.read(name))
                for fonts in root.iter(qn("w:rFonts")):
                    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
                        self.assertEqual("Times New Roman", fonts.get(qn("w:" + attr)),
                                         f"{name}: {attr}")

    def test_process_and_detention_guarantees_are_explicit(self):
        art = bill.NEW_ARTICLE
        first_part = art.split("ч. 2.\n", 1)[0]
        self.assertIn("прибывший по вызову", first_part)
        self.assertIn("участвующий в процессуальных действиях", first_part)
        self.assertIn("без согласия сотрудника", first_part)
        self.assertNotIn("при задержании", first_part)
        for phrase in (
            "обязан приостановить их дальнейшее проведение и ожидать ответа прокурора",
            "его прибытия и рассмотрения изложенных ему вопросов",
            "в течение 15 минут с момента его направления",
            "в любое время сообщил о невозможности прибытия",
            "включая обязательное освобождение задержанного",
            "дополнительные вызовы в течение этого срока его не продлевают",
            "реализации прав участников процессуальных действий",
            "не являются основанием для ограничения свободы лица",
        ):
            self.assertIn(phrase, art)

    def test_act294_changes_a_different_point_and_edits_commute(self):
        existing = self.source[33].rstrip()
        old_v = next(line for line in existing.splitlines()
                     if line.startswith("в) вызова и разбирательства с Офисом"))
        old_project = Document(ACT294)
        proposed_20 = old_project.tables[0].rows[2].cells[1].text
        new_v = next(line for line in proposed_20.splitlines()
                     if line.startswith("в) вызова и разбирательства с Офисом"))
        self.assertIn("частью 4.2 статьи 17", new_v)
        self.assertNotEqual(old_v, new_v)
        self.assertNotIn(bill.NEW_POINT, proposed_20)
        # Сравниваются точечные поправки, а не замена статьи целиком:
        # при полном копировании таблицы ACT. 294 пункт «ж» надо сохранить вручную.
        first_294 = existing.replace(old_v, new_v, 1) + "\n" + bill.NEW_POINT
        first_300 = (existing + "\n" + bill.NEW_POINT).replace(old_v, new_v, 1)
        self.assertEqual(first_294, first_300)
        self.assertEqual(1, first_300.count(bill.NEW_POINT))
        self.assertEqual(1, first_300.count(new_v))
        self.assertIn("после ответа прокурора либо истечения срока ожидания ответа", bill.NEW_ARTICLE)
        self.assertIn("наличие оснований, установленных иными положениями", bill.NEW_ARTICLE)

    def test_rebuild_reproduces_package_contents(self):
        original_out = bill.OUT
        with tempfile.TemporaryDirectory() as temp:
            try:
                bill.OUT = Path(temp)
                with redirect_stdout(StringIO()):
                    bill.main()
                with zipfile.ZipFile(ACT300) as original, \
                     zipfile.ZipFile(Path(temp) / bill.FILE) as rebuilt:
                    self.assertEqual(set(original.namelist()), set(rebuilt.namelist()))
                    for name in original.namelist():
                        self.assertEqual(original.read(name), rebuilt.read(name), name)
            finally:
                bill.OUT = original_out


if __name__ == "__main__":
    unittest.main()
