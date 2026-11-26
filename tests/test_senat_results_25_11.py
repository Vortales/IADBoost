# -*- coding: utf-8 -*-
"""Итоги 25.11: голоса, источники, осторожные статусы и формат публикации."""
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import make_senat_results_25_11 as results


class SenateResults25Tests(unittest.TestCase):
    def test_four_polls_match_supplied_counts_and_message_marks(self):
        self.assertTrue(results.validate_source())
        expected = {
            "open": (11, 0, 1, 12, "19:15", "19:26", (92, 0, 8)),
            "316": (11, 0, 1, 12, "19:20", "19:31", (92, 0, 8)),
            "317": (11, 1, 0, 12, "19:18", "19:27", (92, 8, 0)),
            "close": (9, 1, 1, 11, None, "19:27", (82, 9, 9)),
        }
        self.assertEqual([poll.key for poll in results.POLLS], ["open", "317", "316", "close"])
        self.assertEqual(results.BILL_ACTIVE_COUNT, 17)
        self.assertEqual(results.BILL_MAJORITY, 9)
        outcomes = {"open": "Открыто", "316": "Принят Сенатом", "317": "Принят Сенатом", "close": "Закрыто"}
        for poll in results.POLLS:
            with self.subTest(poll=poll.key):
                self.assertEqual((poll.yes, poll.no, poll.abstain, poll.total,
                                  poll.post_time, poll.notice_time, poll.percentages), expected[poll.key])
                self.assertEqual(poll.outcome, outcomes[poll.key])
                if poll.key in ("316", "317"):
                    self.assertGreaterEqual(poll.yes, results.BILL_MAJORITY)
        polls = {poll.key: poll for poll in results.POLLS}
        self.assertEqual(polls["316"].url,
                         "https://docs.google.com/document/d/1kTukWWpBi4HVhwt-0Yaaozt5HMDShKwIbWAJidscTtI/edit?usp=sharing")
        self.assertEqual(polls["317"].url,
                         "https://docs.google.com/document/d/1UV4n3S-7wMGSkGfVsVxinN1G0_NfFuwIvZfybCJUuvo/edit?usp=sharing")
        self.assertIn("заявлено удаление", polls["317"].title)

    def test_source_validation_rejects_changed_facts(self):
        from unittest.mock import patch

        source = results.SOURCE.read_text(encoding="utf-8")
        changes = (
            ("ACT. 316 и ACT. 317 учитывались 17", "ACT. 316 и ACT. 317 учитывались 16"),
            ("закрытие заседания состоялось после рассмотрения ACT. 316",
             "закрытие заседания состоялось до рассмотрения ACT. 316"),
            ("Сообщение с опросом «316»: Спикер Marcus Nomad, 19:20",
             "Сообщение с опросом «316»: Спикер Marcus Nomad, 19:21"),
            ("Отметка уведомления «316»: 19:31", "Отметка уведомления «316»: 19:30"),
            ("За: 11 (92%). Против: 0 (0%). Воздержался: 1 (8%). Всего: 12.",
             "За: 10 (92%). Против: 0 (0%). Воздержался: 1 (8%). Всего: 12."),
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.txt"
            for original, changed in changes:
                with self.subTest(fact=original):
                    self.assertIn(original, source)
                    path.write_text(source.replace(original, changed, 1), encoding="utf-8")
                    with patch.object(results, "SOURCE", path), self.assertRaises(ValueError):
                        results.validate_source()

    def test_texts_match_generator_and_disclose_limits(self):
        md = (results.OUTPUT_DIR / f"{results.BASENAME}.md").read_text(encoding="utf-8")
        bb = (results.OUTPUT_DIR / f"{results.BASENAME} - BB-код.txt").read_text(encoding="utf-8")
        self.assertEqual(md, results.result_markdown())
        self.assertEqual(bb, results.result_bbcode())
        for text in (md, bb):
            with self.subTest(document=text[:12]):
                for fragment in ("13 человек", "17 действующих сенаторов", "для большинства необходимо 9 голосов за",
                                 "19:27", "19:31", "закрыто после рассмотрения ACT. 316",
                                 "точное время закрытия не указано", "судебного одобрения",
                                 "не устанавливает полный состав вопросов"):
                    self.assertIn(fragment, text)
                self.assertEqual(text.count("Принят Сенатом"), 2)
                self.assertNotIn("16 действующих сенаторов", text)
                self.assertNotIn("19:15-19:26", text)
                self.assertNotIn("/edit?usp=sharing\\_", text)
                for poll in results.POLLS:
                    self.assertIn(poll.time_marks, text)
                    if poll.url:
                        self.assertIn(poll.url, text)

    def test_forum_bbcode_is_nested_and_each_table_row_has_correct_votes(self):
        text = results.result_bbcode()
        tag = re.compile(r"\[(/?)(FONT|CENTER|RIGHT|IMG|I|B|COLOR|SIZE|TABLE|TR|TD|LIST|URL)(?:[ =][^\]]*)?\]", re.I)
        stack = []
        for match in tag.finditer(text):
            closing, name = match.group(1), match.group(2).upper()
            if closing:
                self.assertTrue(stack, match.group())
                self.assertEqual(stack.pop(), name, match.group())
            else:
                if name == "SIZE":
                    self.assertNotIn("SIZE", stack)
                stack.append(name)
        self.assertEqual(stack, [])
        rows = re.findall(r"\[TR\](.*?)\[/TR\]", text, flags=re.S)
        self.assertEqual(len(rows), 5)
        for row, poll in zip(rows[1:], results.POLLS):
            with self.subTest(poll=poll.key):
                cells = re.findall(r"\[td\](.*?)\[/td\]", row, flags=re.S | re.I)
                self.assertEqual(len(cells), 6)
                strip = lambda value: re.sub(r"\[/?[^\]]+\]", "", value).strip()
                self.assertEqual(strip(cells[0]), poll.time_marks)
                self.assertEqual([strip(cells[i]) for i in (2, 3, 4)],
                                 [str(poll.yes), str(poll.no), str(poll.abstain)])
                self.assertEqual(strip(cells[5]), poll.outcome)
                self.assertIn(poll.detail_line, cells[1])
                if poll.url:
                    self.assertIn(poll.url, cells[1])
        self.assertNotRegex(text, r"https://discord[.]com/channels/[0-9]+/[0-9]+/[0-9]+")

    def test_results_image_is_rgb_print_resolution_and_no_protocol_created(self):
        path = results.OUTPUT_DIR / f"{results.BASENAME}.png"
        with Image.open(path) as image:
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.width, 3000)
            self.assertGreater(image.height, 2500)
            self.assertAlmostEqual(image.info["dpi"][0], 300, delta=1)
            self.assertEqual(image.getpixel((116, 92)), results.base.GREEN)
            self.assertNotIn("http", str(image.info).lower())
        self.assertFalse(any("протокол" in path.name.casefold() for path in results.SESSION.rglob("*")))

    def test_builder_does_not_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            paths = results.build(out, text_only=True)
            self.assertEqual(len(paths), 2)
            paths[1].write_text("пользовательская редакция", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                results.build(out, text_only=True)
            self.assertEqual(paths[1].read_text(encoding="utf-8"), "пользовательская редакция")
            results.build(out, force=True, text_only=True)
            self.assertEqual(paths[1].read_text(encoding="utf-8"), results.result_bbcode())

    def test_render_uses_provided_font_and_keeps_all_notes(self):
        font_dir = os.environ.get("SENATE_TEST_TINOS_DIR")
        if not font_dir:
            self.skipTest("для проверки рендера укажите SENATE_TEST_TINOS_DIR")
        faces = results.font_faces("tinos", font_dir)
        captured = []
        original = results.Painter.paragraph

        def capture(painter, y, text, **kwargs):
            captured.append(text)
            return original(painter, y, text, **kwargs)

        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "results.png"
            with patch.object(results.Painter, "paragraph", new=capture):
                width, height = results.render_png(path, faces)
            self.assertEqual(width, 3000)
            self.assertGreater(height, 2500)
            self.assertEqual(path.read_bytes(), (results.OUTPUT_DIR / f"{results.BASENAME}.png").read_bytes())
            for paragraph in results.INTRO:
                self.assertIn(paragraph, captured)
            for note in results.NOTES:
                self.assertTrue(any(note in value for value in captured))


if __name__ == "__main__":
    unittest.main()
