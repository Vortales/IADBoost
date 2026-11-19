# -*- coding: utf-8 -*-
"""Материалы 19.11: источник, голосования, BB-код, PNG и журнал."""
import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from openpyxl import load_workbook
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_senat_journal_19_11 as journal
import make_senat_documents_19_11 as senate

SOURCE_SHA = "949cb7d8e2f3c496e425da0d41370abe6efb857c8ec542fddfe3ba8f44fea442"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def untag(text):
    return re.sub(r"\[[^\]]+\]", "", text).strip()


def table_rows(bb):
    rows = re.findall(r"\[TR\](.*?)\[/TR\]", bb, re.S)
    return [re.findall(r"\[td(?: [^\]]+)?\](.*?)\[/td\]", row, re.S | re.I) for row in rows]


def check_balanced_bb(test, text):
    tag = re.compile(r"\[(/?)(FONT|CENTER|RIGHT|IMG|I|B|COLOR|SIZE|TABLE|TR|td|URL|LIST)(?:[ =][^\]]*)?\]", re.I)
    stack = []
    for match in tag.finditer(text):
        close, name = match.group(1), match.group(2).upper()
        if close:
            test.assertTrue(stack, match.group())
            test.assertEqual(stack.pop(), name, match.group())
        else:
            if name == "SIZE":
                test.assertNotIn("SIZE", stack, "nested SIZE tags")
            stack.append(name)
    test.assertEqual(stack, [])


class SenateSession19Tests(unittest.TestCase):
    def test_source_unchanged_and_provenance_is_recorded(self):
        self.assertEqual(sha(senate.SOURCE), SOURCE_SHA)
        notes = (senate.SESSION / "05 Исходные данные/README.md").read_text(encoding="utf-8")
        self.assertIn(SOURCE_SHA, notes)
        self.assertIn("../19.11.26.txt", notes)
        self.assertIn("Arkasha Justice", notes)
        self.assertIn(senate.ITEM["cec"].url, notes)
        self.assertTrue(senate.validate_source())
        text = senate.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(len(senate.ITEMS), 12)
        self.assertEqual(sum(x.kind == "Законопроект" for x in senate.ITEMS), 11)
        self.assertEqual(sum(x.kind == "Инициатива" for x in senate.ITEMS), 1)
        for item in senate.ITEMS:
            self.assertIn(item.url, text, item.key)
        self.assertIn("1u52dXSkXD9J-VCKrx26DKq9uKeSkq9ntvUnqTqbf5kY", senate.ITEM["300"].url)

    def test_all_polls_chronology_counts_and_outcomes(self):
        expected = (
            ("open", "19:08", "19:11", 13, 0, 0, 13, (100, 0, 0), "Открыто"),
            ("299-300", "19:18", "19:19", 4, 8, 1, 13, (31, 62, 8), "Не приняты"),
            ("301", "19:28", "19:33", 4, 7, 1, 12, (33, 58, 8), "Не принят"),
            ("303", "19:34", "19:35", 1, 10, 0, 11, (9, 91, 0), "Не принят"),
            ("308", "19:36", "19:43", 10, 1, 3, 14, (71, 7, 21), "Принят Сенатом"),
            ("cec", "19:38", "19:44", 9, 1, 0, 10, (90, 10, 0), "Поддержана"),
            ("309", "19:39", "19:43", 12, 1, 1, 14, (86, 7, 7), "Принят Сенатом"),
            ("close", "19:44", "19:48", 10, 1, 1, 12, (83, 8, 8), "Закрыто"),
        )
        actual = tuple((p.key, p.start, p.end, p.yes, p.no, p.abstain, p.total,
                        p.percentages, p.outcome) for p in senate.POLLS)
        self.assertEqual(actual, expected)
        self.assertEqual(senate.ACTIVE_COUNT, 16)
        self.assertEqual(senate.MAJORITY, 9)
        self.assertEqual([p.start for p in senate.POLLS], sorted(p.start for p in senate.POLLS))
        self.assertEqual(sum(p.key == "299-300" for p in senate.POLLS), 1)
        self.assertLess(senate.BY_POLL["308"].start, senate.BY_POLL["cec"].start)
        self.assertLess(senate.BY_POLL["cec"].start, senate.BY_POLL["308"].end)
        self.assertLess(senate.BY_POLL["309"].start, senate.BY_POLL["cec"].end)
        # Опрос ЦИК завершился в ту же минуту, когда началось закрытие; секунды не домысливаются.
        self.assertEqual(senate.BY_POLL["cec"].end, senate.BY_POLL["close"].start)
        self.assertEqual([sum(p.percentages) for p in senate.POLLS], [100, 101, 99, 100, 99, 100, 100, 99])
        for key in ("308", "309"):
            self.assertGreaterEqual(senate.BY_POLL[key].yes, senate.MAJORITY)
        for key in ("299-300", "301", "303"):
            self.assertLess(senate.BY_POLL[key].yes, senate.MAJORITY)

    def test_withdrawn_not_converted_to_zero_votes(self):
        self.assertEqual(senate.WITHDRAWN, (("302", "19:39"), ("304", "19:39"),
                                           ("305", "19:39"), ("306", "19:40"), ("307", "19:40")))
        self.assertFalse({key for key, _ in senate.WITHDRAWN} & set(senate.BY_POLL))
        self.assertIn("Отдельные голосования", senate.WITHDRAWN_NOTE)
        self.assertIn("не зафиксированы", senate.WITHDRAWN_NOTE)
        self.assertIn("Неучастие не приравнивается к воздержанию", " ".join(senate.INTRO))

    def test_validator_rejects_changes_to_counts_end_times_and_withdrawal(self):
        original = senate.SOURCE.read_text(encoding="utf-8")
        mutations = (
            ("4 голоса\n31%\nПротив", "5 голосов\n31%\nПротив"),
            ("«299 - 300» завершён. — 19:19", "«299 - 300» завершён. — 19:20"),
            ("10 голосов\n71%\nПротив", "10 голосов\n70%\nПротив"),
            ("«309» завершён. — 19:43", "«309» завершён. — 19:44"),
            ("— 19:40\nОтозван", "— 19:41\nОтозван"),
        )
        for before, after in mutations:
            self.assertIn(before, original)
            with self.subTest(before=before), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "input.txt"
                path.write_text(original.replace(before, after, 1), encoding="utf-8")
                with self.assertRaises(ValueError):
                    senate.validate_source(path)

    def test_initiative_and_308_are_described_without_overstatement(self):
        self.assertIn("Arkasha Justice вместо Angel Insomnia", senate.ITEM["cec"].subject)
        self.assertIn("оформление решения не подтверждено", senate.BY_POLL["cec"].detail)
        self.assertIn("Дорожный кодекс", senate.ACT308_NOTE)
        self.assertIn("уголовную норму", senate.ACT308_NOTE)
        self.assertIn("название изменяемого акта", senate.ACT308_NOTE)
        self.assertIn("Jacob Killa, номер паспорта 57474", senate.BY_POLL["309"].detail)
        self.assertNotIn("назначен", senate.BY_POLL["cec"].detail)
        self.assertIn("Принятие законопроекта Сенатом не подтверждает", senate.ENACTMENT_NOTE)

    def test_bbcode_is_balanced_and_matches_polls(self):
        for bb in (senate.agenda_bb(), senate.result_bb()):
            self.assertTrue(bb.startswith("[FONT=Times New Roman]"))
            self.assertTrue(bb.rstrip().endswith("[/FONT]"))
            check_balanced_bb(self, bb)
            self.assertNotRegex(bb, r"\bID\b")
            self.assertNotIn("Правила проекта", bb)
        agenda, result = senate.agenda_bb(), senate.result_bb()
        agenda_rows = table_rows(agenda)
        self.assertEqual(len(agenda_rows), len(senate.ITEMS) + 1)
        for cells, item in zip(agenda_rows[1:], senate.ITEMS):
            self.assertEqual(len(cells), 5)
            self.assertEqual(untag(cells[0]), item.label)
            self.assertIn(item.url, cells[0])
            self.assertIn(item.subject, cells[1])
            self.assertEqual(untag(cells[2]), item.kind)
            self.assertEqual(untag(cells[3]), item.author)
            self.assertEqual(untag(cells[4]), item.posted)
        rows = table_rows(result)
        self.assertEqual(len(rows), 1 + len(senate.POLLS))
        for cells, poll in zip(rows[1:], senate.POLLS):
            self.assertEqual(len(cells), 6)
            self.assertEqual(untag(cells[0]), poll.interval)
            self.assertEqual([untag(cell) for cell in cells[2:5]],
                             list(map(str, (poll.yes, poll.no, poll.abstain))))
            self.assertEqual(untag(cells[5]), poll.outcome)
            if poll.url:
                self.assertIn(poll.url, cells[1])
            if poll.second_url:
                self.assertIn(poll.second_url, cells[1])
        self.assertEqual(result.count("[COLOR=rgb(210, 55, 55)]Не принят"), 3)
        self.assertIn("Arkasha Justice", result)
        self.assertIn("Jacob Killa, номер паспорта 57474", result)
        self.assertNotIn("Google Docs", result)

    def test_output_text_and_png_agree_with_source(self):
        for directory, name, markdown, bb in (
            (senate.AGENDA_DIR, senate.AGENDA_NAME, senate.agenda_markdown(), senate.agenda_bb()),
            (senate.RESULT_DIR, senate.RESULT_NAME, senate.results_markdown(), senate.result_bb()),
        ):
            self.assertEqual((directory / f"{name}.md").read_text(encoding="utf-8"), markdown)
            self.assertEqual((directory / f"{name} - BB-код.txt").read_text(encoding="utf-8"), bb)
            path = directory / f"{name}.png"
            with Image.open(path) as img:
                self.assertEqual(img.format, "PNG")
                self.assertEqual(img.mode, "RGB")
                self.assertEqual(img.width, 3000)
                self.assertGreater(img.height, 4000)
                self.assertEqual(img.getpixel((116, 92)), senate.previous.GREEN)
                self.assertAlmostEqual(img.info["dpi"][0], 300, delta=1)
            self.assertGreater(path.stat().st_size, 100_000)
        md_rows = [line for line in senate.results_markdown().splitlines() if re.match(r"^\| 19:\d\d-19:\d\d \|", line)]
        self.assertEqual(len(md_rows), len(senate.POLLS))
        self.assertEqual(sum("ACT. 299" in row and "ACT. 300" in row for row in md_rows), 1)
        self.assertNotIn("Протокол", senate.agenda_markdown() + senate.results_markdown())

    def test_png_painters_exclude_links_and_use_times_new_roman(self):
        try:
            faces = senate.previous.font_faces()
        except SystemExit:
            self.skipTest("Установите SENATE_FONT_DIR с Times New Roman")
        for draw in (senate.draw_agenda, senate.draw_results):
            scratch = Image.new("RGB", (1, 1), "white")
            painter = senate.Painter(ImageDraw.Draw(scratch), scratch, faces, True)
            bottom = draw(painter)
            self.assertGreater(bottom, 3500)
            text = " ".join(painter.texts)
            self.assertNotIn("https://", text)
            self.assertNotIn("Google Docs", text)
            self.assertIn("Arkasha", text)
            self.assertIn("19 ноября 2026 года", text)
        scratch = Image.new("RGB", (1, 1), "white")
        painter = senate.Painter(ImageDraw.Draw(scratch), scratch, faces, True)
        senate.draw_results(painter)
        for p in senate.POLLS:
            self.assertEqual(painter.texts.count(p.interval), 1)

    def test_journal_event_values_and_hyperlinks(self):
        workbook = load_workbook(journal.OUTPUT, data_only=False)
        self.assertEqual(workbook.active.title, journal.SHEET)
        sheet = workbook[journal.SHEET]
        self.assertEqual(sheet["A1"].value, "Заседание Сената - 19.11.2026")
        self.assertEqual(sheet["B2"].value, 16)
        self.assertIsNone(sheet["B3"].value)
        self.assertEqual(sheet["D3"].value, "Не подтверждён")
        self.assertEqual(sheet["G3"].value, 12)
        self.assertEqual(str(sheet.print_area), "'Журнал заседаний 19.11'!$A$1:$M$19")
        self.assertEqual(sheet.freeze_panes, "C7")
        links = set()
        for row, (start, _, key, poll) in enumerate(journal.events(), 7):
            with self.subTest(key=key):
                self.assertEqual(sheet.cell(row, 3).value, journal.QUESTION_LABELS[key])
                self.assertEqual(sheet.cell(row, 11).value, start)
                self.assertEqual(sheet.cell(row, 3).font.name, "Times New Roman")
                if poll is None:
                    self.assertEqual([sheet.cell(row, col).value for col in (5, 6, 7, 10)], [None] * 4)
                    self.assertEqual(sheet.cell(row, 8).value, "Отозван")
                    self.assertIsNone(sheet.cell(row, 12).value)
                else:
                    self.assertEqual([sheet.cell(row, col).value for col in (5, 6, 7)],
                                     [poll.yes, poll.no, poll.abstain])
                    self.assertEqual(sheet.cell(row, 8).value, poll.outcome)
                    self.assertEqual(sheet.cell(row, 10).value, 16)
                    self.assertEqual(sheet.cell(row, 12).value, poll.end)
                for col in (3, 13):
                    cell = sheet.cell(row, col)
                    if cell.hyperlink:
                        links.add(cell.hyperlink.target)
        self.assertEqual(links, {item.url for item in senate.ITEMS})
        for text in ("Afelia Suspect", "Merkylka Fair", "Jhonny Scoutezaki"):
            self.assertFalse(any(text in str(c.value or "") for row in sheet.iter_rows() for c in row))

    def test_copy_preserves_historical_workbook_parts(self):
        with ZipFile(journal.TEMPLATE) as old, ZipFile(journal.OUTPUT) as new:
            original = set(old.namelist())
            self.assertTrue(original.issubset(new.namelist()))
            self.assertEqual(set(new.namelist()) - original,
                             {"xl/worksheets/sheet9.xml", "xl/worksheets/_rels/sheet9.xml.rels"})
            allowed = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels", "[Content_Types].xml"}
            self.assertEqual({name for name in original if old.read(name) != new.read(name)}, allowed)
            for name in original - allowed:
                self.assertEqual(old.read(name), new.read(name), name)
        old = load_workbook(journal.TEMPLATE, read_only=True)
        new = load_workbook(journal.OUTPUT, read_only=True)
        self.assertEqual(new.sheetnames[:-1], old.sheetnames)
        self.assertEqual(new.sheetnames[-1], journal.SHEET)

    def test_journal_refuses_to_overwrite_existing_file(self):
        template_before = sha(journal.TEMPLATE)
        source_before = sha(senate.SOURCE)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "журнал.xlsx"
            journal.build(target)
            before = sha(target)
            with self.assertRaises(FileExistsError):
                journal.build(target)
            self.assertEqual(sha(target), before)
            self.assertEqual(load_workbook(target).active.title, journal.SHEET)
        self.assertEqual(sha(journal.TEMPLATE), template_before)
        self.assertEqual(sha(senate.SOURCE), source_before)


if __name__ == "__main__":
    unittest.main()
