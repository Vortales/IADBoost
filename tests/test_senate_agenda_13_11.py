# -*- coding: utf-8 -*-
"""Проверка повестки 13.11 и безопасного обновления листа журнала."""
import ast
import hashlib
import importlib.util
import re
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from openpyxl.formula import Tokenizer
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "Повестка" / "13.11.2026"
AGENDA = SESSION / "02 Повестка"
INPUTS = SESSION / "06 Исходные данные"
XLSX = SESSION / "05 Журнал" / "The Senate of San Andreas 19.xlsx"
SHEET = "Журнал заседаний 13.11"


def load_journal_builder():
    spec = importlib.util.spec_from_file_location(
        "journal_13_11", ROOT / "tools" / "build_senat_journal_13_11.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extra_entries():
    text = (INPUTS / "Повестка_доп.txt").read_text(encoding="utf-8")
    headers = list(re.finditer(r"(?m)^ACT\.?\s*(29[4-7])\s*$", text))
    assert [int(m.group(1)) for m in headers] == [294, 295, 296, 297]
    result = {}
    for i, match in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[match.end():end]
        link = re.search(r"https://docs\.google\.com/document/d/[^\s]+", section)
        time = re.search(r"—\s*(17:\d{2})", section)
        assert link and time and "Gogal Killaz" in section and "63823" in section
        result[int(match.group(1))] = (link.group(), time.group(1))
    return result


class SenateAgendaTests(unittest.TestCase):
    def test_agenda_entries_links_and_order(self):
        entries = extra_entries()
        md = (AGENDA / "Повестка заседания 13.11.2026.md").read_text(encoding="utf-8")
        forum = (AGENDA / "Пост на форум - повестка 13.11.2026.txt").read_text(encoding="utf-8")
        workbook = load_workbook(XLSX)
        ws = workbook[SHEET]
        self.assertEqual([ws[f"C{r}"].value for r in range(7, 19)],
                         [f"ACT. {number}" for number in range(286, 298)])
        self.assertEqual(len(re.findall(r"(?m)^\[TR\]$", forum)), 17)  # шапка и 16 вопросов
        self.assertIn("16 вопросов", md)
        self.assertIn("16 вопросов", forum)
        for number, (link, time) in entries.items():
            start = re.search(rf"(?m)^### \d+\. ACT\. {number}\s*$", md)
            self.assertIsNotNone(start)
            end = re.search(r"(?m)^#{2,3} ", md[start.end():])
            block = md[start.end():start.end() + end.start()] if end else md[start.end():]
            self.assertIn(link, block)
            self.assertIn(time, block)
            self.assertIn("Gogal Killaz", block)
            self.assertIn("63823", block)
            self.assertIn(f"[URL='{link}'][B][I]ACT. {number}[/I][/B][/URL]", forum)
            cell = ws[f"C{number - 279}"]
            self.assertEqual(cell.hyperlink.target, link)
            self.assertIn("Gogal Killaz", cell.hyperlink.tooltip)
            self.assertIn(time, cell.hyperlink.tooltip)
        self.assertEqual(ws["C22"].value, "Инициатива об избрании Afelia Suspect (14077) Вице-Спикером Сената")
        self.assertIsNone(ws["C22"].hyperlink)
        self.assertIn("позиция 14", md)
        self.assertIn("исходной редакции", forum)

    def test_journal_formulas_and_empty_votes(self):
        ws = load_workbook(XLSX)[SHEET]
        cached = load_workbook(XLSX, data_only=True)[SHEET]
        self.assertEqual(ws["G3"].value, "=COUNTA(C7:C22)")
        self.assertEqual(cached["G3"].value, 16)
        self.assertIsNone(ws["B3"].value)
        self.assertIsNone(ws["D3"].value)
        self.assertEqual(ws["J6"].value, "Сенаторов для подсчёта")
        for row in range(7, 23):
            for column in "EFIJ":
                self.assertIsNone(ws[f"{column}{row}"].value)
            for column in "GH":
                formula = ws[f"{column}{row}"].value
                self.assertTrue(formula.startswith("="))
                self.assertTrue(Tokenizer(formula).items)
            self.assertIn(f"E{row}>J{row}/2", ws[f"H{row}"].value)
            self.assertIn(f"ROUNDUP(J{row}*2/3,0)", ws[f"H{row}"].value)
            self.assertIn(f"ROUNDUP(J{row}*3/4,0)", ws[f"H{row}"].value)
            self.assertEqual(ws[f"C{row}"].font.name, "Times New Roman")
        validations = {str(v.sqref) for v in ws.data_validations.dataValidation}
        self.assertTrue({"D7:D22", "D3", "J7:J22", "I7:I22"}.issubset(validations))

    def test_rebuild_only_changes_target_sheet_and_refuses_filled_votes(self):
        module = load_journal_builder()
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "book.xlsx"
            shutil.copyfile(XLSX, copy)
            module.XLSX = str(copy)
            with zipfile.ZipFile(copy) as original:
                parts = {name: original.read(name) for name in original.namelist()}
                target, links = module.sheet_parts(original)
            module.build()
            with zipfile.ZipFile(copy) as rebuilt:
                self.assertEqual(set(parts), set(rebuilt.namelist()))
                for name, contents in parts.items():
                    if name not in {target, links}:
                        self.assertEqual(contents, rebuilt.read(name), name)
            for cell, value in (("E15", 1), ("J15", 16), ("D3", "Собран"), ("G15", "=42")):
                with self.subTest(cell=cell):
                    shutil.copyfile(XLSX, copy)
                    workbook = load_workbook(copy)
                    workbook[SHEET][cell] = value
                    workbook.save(copy)
                    before = hashlib.sha256(copy.read_bytes()).hexdigest()
                    with self.assertRaisesRegex(ValueError, cell):
                        module.build()
                    self.assertEqual(before, hashlib.sha256(copy.read_bytes()).hexdigest())

    def test_corrected_act_and_renumbering(self):
        directory = ROOT / "Законопроекты"
        path = directory / "Законопроекты 294 (вызов прокурора адвокатом)" / "ACT.294.Процессуальный кодекс (вызов прокурора адвокатом).docx"
        doc = Document(path)
        self.assertEqual(doc.paragraphs[0].text, "ACT. 294")
        proposal = doc.tables[0].rows[1].cells[1].text
        self.assertIn("частный адвокат, осуществляющий защиту задержанного, вправе заявить сотруднику", proposal)
        self.assertIn("государственный адвокат, осуществляющий защиту задержанного, вправе самостоятельно", proposal)
        self.assertIn("самостоятельного вызова сотрудника Офиса Генерального прокурора государственным адвокатом", proposal)
        self.assertNotIn("государственным адвокатов", proposal)
        self.assertIn("если иное не предусмотрено статьёй 19", proposal)
        self.assertIn("15 минут с момента вызова", proposal)
        self.assertNotIn("халатност", proposal.lower())
        self.assertNotIn("самоуправств", proposal.lower())
        self.assertIn("с учётом статуса адвоката", proposal)
        self.assertNotIn("влекут дисциплинарную ответственность", proposal)
        for folder, filename, number in [
            ("Законопроекты 298 (неприкосновенность сенатора)", "ACT.298.Закон о неприкосновенности.docx", 298),
            ("Законопроекты 299 (отстранение сенатора)", "ACT.299.Конституционный закон о Сенате.docx", 299),
        ]:
            self.assertEqual(Document(directory / folder / filename).paragraphs[0].text, f"ACT. {number}")
        self.assertFalse((directory / "Законопроекты 298 (лексические и орфографические ошибки)").exists())

    def test_agenda_distinguishes_original_plan_and_meeting_outcomes(self):
        for name in ("Повестка заседания 13.11.2026.md", "Пост на форум - повестка 13.11.2026.txt"):
            text = (AGENDA / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("первоначальн", text.lower())
                self.assertIn("по итогам заседания", text.lower())
                self.assertIn("не рассматривались", text.lower())
                self.assertIn("отстранением", text.lower())
                self.assertIn("Merkylka Fair", text)
                self.assertIn("62277", text)
                self.assertIn("Jonny Zakonov", text)
                self.assertNotIn("инициативу отклонить", text.lower())
                self.assertNotIn("отклонена при её формировании", text.lower())
                self.assertNotIn("внесена председателем политической партии, а не сенатором", text.lower())

    def test_png_data_contains_no_links_or_service_labels(self):
        source = (ROOT / "tools" / "make_senat_agenda_png.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        constants = "\n".join(node.value for node in ast.walk(tree)
                              if isinstance(node, ast.Constant) and isinstance(node.value, str))
        self.assertNotIn("Google Docs", constants)
        self.assertNotIn("https://", constants)
        values = {node.targets[0].id: ast.literal_eval(node.value)
                  for node in tree.body if isinstance(node, ast.Assign)
                  and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                  and node.targets[0].id in {"ACTS", "INITS", "SPECIAL_INITIATIVE", "AFTER_SESSION_NOTE"}}
        self.assertEqual([a[0] for a in values["ACTS"]], [f"ACT. {n}" for n in range(286, 298)])
        self.assertEqual(len(values["INITS"]), 4)
        self.assertIn("Merkylka Fair, номер паспорта 62277", values["SPECIAL_INITIATIVE"][2])
        self.assertIn("Jonny Zakonov, номер паспорта 55454", values["SPECIAL_INITIATIVE"][2])
        self.assertIn("не рассматривались", values["AFTER_SESSION_NOTE"])
        self.assertIn("отстранением Республиканской партии", values["AFTER_SESSION_NOTE"])
        self.assertNotIn("отклонена при её формировании", constants)
        with Image.open(AGENDA / "Повестка заседания 13.11.2026.png") as image:
            self.assertEqual(image.size, (3000, 5200))


if __name__ == "__main__":
    unittest.main()
