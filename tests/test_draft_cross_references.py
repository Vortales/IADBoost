# -*- coding: utf-8 -*-
"""В новых нормах номера сохраняются только для отсылок внутри того же акта."""
import re
import sys
import unittest
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_act303 as territory
import build_acts301_302 as releases
import build_acts304_307 as defence
import build_sang_299_300 as sang

# Находит как прямые ссылки («статьи 16 Процессуального кодекса»), так и
# ссылки через уже названный акт («статьи 37 указанного Кодекса» / «его статьи 2»).
ARTICLE = r"(?:стать(?:я|и|е|ю|ей|ёй|ями|ям|ях)|ст\.)\s*"
NUMBER = r"\d+(?:\.\d+)*(?:(?:\s*,\s*|\s+(?:и|или)\s+|\s*-\s*)\d+(?:\.\d+)*)*"
ACT = (r"(?:Процессуальн\w*\s+кодекс\w*|Уголовн\w*\s+кодекс\w*|"
       r"(?:Конституционн\w*\s+)?закон\w*|Приложени\w*|кодекс\w*|"
       r"Конституци\w*|ПК|УК|КоАП)")
DIRECT = re.compile(
    rf"\b{ARTICLE}{NUMBER}(?:\s+ч\.\s*\d+(?:\.\d+)*)?\s+"
    rf"(?:(?:указанн\w*|данн\w*|этого|его)\s+)?{ACT}\b", re.I)
INDIRECT = re.compile(rf"\b(?:его|этого|указанн\w*)\s+{ARTICLE}{NUMBER}", re.I)
PARENTHETICAL = re.compile(
    rf"\b{ACT}(?:\s+штата\s+[\w-]+)?\s*[,(]\s*"
    rf"(?:(?:част[ьиью]+|ч\.)\s*\d+(?:\.\d+)*\s+)?{ARTICLE}{NUMBER}", re.I)


def forbidden_references(text):
    return [m.group() for pattern in (DIRECT, INDIRECT, PARENTHETICAL)
            for m in pattern.finditer(text)]


def bills():
    return ([(releases.OUT / folder, bill) for folder, bill in releases.specs()]
            + [(territory.OUT, territory.specs()[0])]
            + [(defence.OUT / folder, bill) for folder, bill in defence.specs()[0]]
            + [(sang.OUT / folder, bill) for folder, bill in sang.specs()])


class CrossReferenceTests(unittest.TestCase):
    def test_detector_distinguishes_external_and_internal_references(self):
        external = (
            "по пункту «е» части 1 статьи 18 Процессуального кодекса",
            "статьями 17, 18 и 22 Процессуального кодекса",
            "в порядке статьи 37 указанного Кодекса",
            "применяется указанный Кодекс в порядке его статьи 2",
            "по ст. 16 ПК",
            "Процессуальный кодекс (статья 29)",
        )
        for phrase in external:
            with self.subTest(phrase=phrase):
                self.assertTrue(forbidden_references(phrase))
        internal = (
            "по части 2 статьи 23 настоящего Кодекса",
            "по статье 8 настоящего Закона в порядке Процессуального кодекса",
            "части 1.3 статьи 5 настоящего Приложения",
        )
        for phrase in internal:
            with self.subTest(phrase=phrase):
                self.assertFalse(forbidden_references(phrase))

    def test_all_proposed_docx_provisions_have_no_numbered_external_citations(self):
        self.assertEqual(len(bills()), 9)
        for directory, bill in bills():
            doc = Document(directory / bill["file"])
            self.assertEqual(len(doc.tables[0].rows), len(bill["rows"]) + 1)
            for row, (_, proposed) in zip(doc.tables[0].rows[1:], bill["rows"]):
                title, locator, body = row.cells[1].text.split("\n", 2)
                self.assertEqual(row.cells[1].text, territory.plain(proposed))
                with self.subTest(bill=bill["num"], act=title, locator=locator):
                    self.assertEqual(forbidden_references(body), [])
            # Заголовки и SECTION также являются частью документа.
            narrative = "\n".join(p.text for p in doc.paragraphs)
            self.assertEqual(forbidden_references(narrative), [])

    def test_explanations_only_number_the_act_being_discussed(self):
        # Эти четыре совпадения описывают собственные положения изменяемого акта,
        # а не отсылают к нормам другого акта.
        allowed = {
            303: ["Статья 2 Приложения"],
            299: ["статьи 4 Приложения"],
            300: ["статьи 2 Закона", "статье 8 Закона"],
        }
        for directory, bill in bills():
            text = (directory / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8").replace("**", "")
            with self.subTest(bill=bill["num"]):
                self.assertEqual(forbidden_references(text), allowed.get(bill["num"], []))

    def test_referenced_act_names_in_proposals_are_bold(self):
        names = re.compile(
            r"Процессуальн\w+ кодекс\w+ штата Сан-Андреас|"
            r"Приложени\w+ № 1 к Уголовному кодексу штата Сан-Андреас|"
            r"Закон\w* «[^»]+»", re.I)
        found = 0
        for directory, bill in bills():
            doc = Document(directory / bill["file"])
            for row in doc.tables[0].rows[1:]:
                for paragraph in row.cells[1].paragraphs:
                    for run in paragraph.runs:
                        if names.search(run.text):
                            found += 1
                            with self.subTest(bill=bill["num"], name=run.text):
                                self.assertTrue(run.bold)
        self.assertGreater(found, 35)

    def test_precise_internal_references_remain(self):
        index = {}
        for directory, bill in bills():
            doc = Document(directory / bill["file"])
            for row in doc.tables[0].rows[1:]:
                title, locator, body = row.cells[1].text.split("\n", 2)
                index[bill["num"], title, locator] = body
        pc = releases.PC_TITLE
        app = releases.APP_TITLE
        guard = sang.SANG_TITLE
        self.assertIn("части 1 статьи 19 настоящего Кодекса",
                      index[302, pc, "Статья 18, часть 1, пункт «е»"])
        self.assertIn("пункту «е» части 1 статьи 18 настоящего Кодекса",
                      index[302, pc, "Статья 19, часть 1"])
        self.assertIn("части 2 настоящей статьи", index[302, pc, "Статья 18, часть 1, пункт «е»"])
        self.assertIn("статьей 2 настоящего Приложения", index[303, app, "Статья 1, основные понятия"])
        self.assertIn("примечанию 2 настоящей статьи", index[303, app, "Статья 4, примечание 4"])
        self.assertIn("примечанию 1 пункта «а» статьи 4 настоящего Приложения",
                      index[303, app, "Статья 2, цели посещения SANG"])
        self.assertIn("части 2 статьи 23 настоящего Кодекса", index[304, pc, "Статья 20, часть 2, пункт «ж»"])
        self.assertIn("статьям 11-14 настоящего Кодекса", index[305, pc, "Статья 23, часть 1, пункт «г» и исключение"])
        self.assertIn("статье 32 настоящего Кодекса", index[306, pc, "Статья 43, часть 3"])
        self.assertIn("статьи 10 настоящего Закона", index[300, guard, "Статья 2, часть 7"])
        self.assertIn("статье 8 настоящего Закона", index[300, guard, "Статья 2, часть 7"])


if __name__ == "__main__":
    unittest.main()
