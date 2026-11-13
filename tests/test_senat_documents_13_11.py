# -*- coding: utf-8 -*-
"""Проверка хронологии, голосов и согласованности двух сенатских документов."""
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_senat_documents_13_11 as senate


def untag(text):
    return re.sub(r"\[[^\]]+\]", "", text).strip()


def table_rows(bb):
    rows = re.findall(r"\[TR\](.*?)\[/TR\]", bb, re.S)
    return [re.findall(r"\[td(?: [^\]]+)?\](.*?)\[/td\]", row, re.S | re.I)
            for row in rows]


def check_balanced_bb(test, text):
    expression = re.compile(r"\[(/?)(CENTER|RIGHT|IMG|I|B|COLOR|SIZE|TABLE|TR|td|URL|LIST)(?:[ =][^\]]*)?\]", re.I)
    stack = []
    for token in expression.finditer(text):
        close, name = token.group(1), token.group(2).upper()
        if close:
            test.assertTrue(stack, f"unexpected closing tag {token.group(0)}")
            test.assertEqual(stack.pop(), name, f"unbalanced tag {token.group(0)}")
        else:
            if name == "SIZE":
                test.assertNotIn("SIZE", stack, "nested SIZE tags are not supported consistently")
            stack.append(name)
    test.assertEqual(stack, [])


class SenateDocumentsTests(unittest.TestCase):
    def test_all_completed_polls_match_discord(self):
        self.assertTrue(senate.validate_polls_against_log())
        self.assertEqual(len(senate.POLLS), 18)
        self.assertEqual(len(senate.SUBSTANTIVE), 16)
        self.assertEqual(len(senate.RESULT_POLLS), 18)
        self.assertEqual(senate.RESULT_POLLS, (senate.BY_KEY["open"],) + senate.SUBSTANTIVE + (senate.BY_KEY["close"],))
        self.assertEqual(senate.RESULT_POLLS, senate.POLLS)
        self.assertEqual(sum(p.key.isdigit() for p in senate.POLLS), 13)
        self.assertEqual(len({p.key for p in senate.POLLS}), 18)

    def test_opening_votes_time_and_percentages_in_both_documents(self):
        opening = senate.BY_KEY["open"]
        self.assertEqual((opening.start, opening.end), ("19:00", "19:05"))
        self.assertEqual((opening.yes, opening.no, opening.abstain, opening.total), (13, 0, 1, 14))
        self.assertEqual(opening.detail, "Всего 14 голосов: да - 93%, нет - 0%, воздержался - 7%.")
        source = senate.SOURCE.read_text(encoding="utf-8")
        source = source.split("\nОткрытие Сената 13.11.26\n", 1)[1].split("\nОпрос завершён\n", 1)[0]
        self.assertRegex(source, r"(?s)Да\s+13 голосов\s+93%\s+Нет\s+0 голосов\s+0%"
                                 r"\s+Воздержался.*?1 голос\s+7%\s+14 голосов")
        for protocol in (False, True):
            rows = table_rows(senate.build_bb(protocol))
            self.assertEqual(untag(rows[1][0]), "19:00-19:05")
            self.assertIn(opening.title, rows[1][1])
            self.assertIn(senate.bb_text(opening.detail), rows[1][1])
            count_index = 3 if protocol else 2
            self.assertEqual([untag(c) for c in rows[1][count_index:count_index + 3]], ["13", "0", "1"])
            self.assertEqual(sum(opening.title in row[1] for row in rows[1:]), 1)
            self.assertNotIn("Вы проголосовали за этот ответ", senate.build_bb(protocol))

    def test_closing_votes_time_and_percentages_in_both_documents(self):
        closing = senate.BY_KEY["close"]
        self.assertEqual((closing.start, closing.end), ("20:53", "20:54"))
        self.assertEqual((closing.yes, closing.no, closing.abstain, closing.total), (9, 0, 0, 9))
        self.assertEqual(closing.active, 14)
        self.assertEqual(closing.detail, "Всего 9 голосов: за - 100%, против - 0%, воздержался - 0%.")
        source = senate.SOURCE.read_text(encoding="utf-8")
        source = source.split("\nЗакрытие заседания 13.11.26\n", 1)[1].split("\nОпрос завершён\n", 1)[0]
        self.assertRegex(source, r"(?s)Закрытие\s+За\s+9 голосов\s+100%\s+Против\s+0 голосов\s+0%"
                                 r"\s+Воздержался\s+0 голосов\s+0%\s+9 голосов")
        for protocol in (False, True):
            rows = table_rows(senate.build_bb(protocol))
            self.assertEqual(untag(rows[-1][0]), "20:53-20:54")
            self.assertIn(closing.title, rows[-1][1])
            self.assertIn(senate.SPEAKER, rows[-1][1])
            self.assertIn(senate.bb_text(closing.detail), rows[-1][1])
            count_index = 3 if protocol else 2
            self.assertEqual([untag(c) for c in rows[-1][count_index:count_index + 3]], ["9", "0", "0"])
            self.assertEqual(untag(rows[-1][-1]), "Закрыто")
            self.assertEqual(sum(closing.title in row[1] for row in rows[1:]), 1)
            self.assertNotIn("Aliya Nomad", rows[-1][1])  # упоминание не устанавливает личный голос

    def test_validator_rejects_modified_poll_or_finish_time(self):
        original = senate.SOURCE.read_text(encoding="utf-8")
        changes = [
            ("8 голосов\n89%\nПротив", "7 голосов\n89%\nПротив"),
            ("«296» завершён. — 20:54", "«296» завершён. — 20:55"),
            ("Закрытие\nЗа\n\n9 голосов\n100%", "Закрытие\nЗа\n\n8 голосов\n100%"),
            ("«Закрытие» завершён. — 20:54", "«Закрытие» завершён. — 20:55"),
        ]
        for before, after in changes:
            self.assertIn(before, original)
            with self.subTest(before=before), tempfile.TemporaryDirectory() as td:
                path = Path(td) / "source.txt"
                path.write_text(original.replace(before, after, 1), encoding="utf-8")
                with self.assertRaises(ValueError):
                    senate.validate_polls_against_log(path)

    def test_sequence_active_senators_and_overlaps(self):
        polls = senate.POLLS
        self.assertEqual([p.start for p in polls], sorted(p.start for p in polls))
        self.assertTrue(all(p.start <= p.end for p in polls))
        self.assertEqual((senate.BY_KEY["open"].active, senate.BY_KEY["jonny"].active), (16, 16))
        self.assertEqual(senate.BY_KEY["jonny"].end, "19:10")
        for poll in polls[2:-1]:
            self.assertEqual(poll.active, 15, poll.key)
        vice, closing = senate.BY_KEY["vice"], senate.BY_KEY["close"]
        self.assertEqual((vice.start, vice.end, vice.yes, vice.active), ("20:45", "20:52", 8, 15))
        self.assertEqual((closing.start, closing.end, closing.active), ("20:53", "20:54", 14))
        for key in ("295", "296"):
            p = senate.BY_KEY[key]
            self.assertLess(p.start, vice.start)
            self.assertGreater(p.end, vice.end)
            self.assertEqual(p.end, closing.end)
            self.assertEqual(p.active, 15)  # по началу опроса, не задним числом 14

    def test_thresholds_and_results(self):
        expected_accepted = {"287", "288", "298", "289", "290", "292", "293", "296", "297"}
        expected_failed = {"286", "291", "294", "295"}
        self.assertEqual(expected_accepted | expected_failed, {p.key for p in senate.POLLS if p.key.isdigit()})
        for key in expected_failed:
            self.assertEqual(senate.BY_KEY[key].outcome, "Не принят")
            self.assertLess(senate.BY_KEY[key].yes, 8)
        for key in expected_accepted:
            poll = senate.BY_KEY[key]
            needed = 10 if poll.kind == "конституционный" else 8
            self.assertGreaterEqual(poll.yes, needed)
            self.assertNotEqual(poll.outcome, "Не принят")
        self.assertEqual(senate.BY_KEY["298"].kind, "закон")
        self.assertEqual(senate.BY_KEY["298"].threshold, "8")
        self.assertEqual(senate.BY_KEY["298"].outcome, "Принят")
        self.assertEqual(senate.BY_KEY["296"].outcome, "Принят")
        self.assertIn("оперативно-розыскной деятельности", senate.BY_KEY["298"].title)
        self.assertIn("пункте «в» части 1 статьи 20", senate.BY_KEY["296"].title)
        self.assertIn("на часть 1 статьи 16", senate.BY_KEY["296"].title)
        self.assertEqual(senate.BY_KEY["vice"].threshold, "8")

    def test_unvoted_questions_and_personal_votes_not_guessed(self):
        source = senate.SOURCE.read_text(encoding="utf-8")
        special = source.split(senate.UNVOTED_ANCHORS[0], 1)[1].split(senate.UNVOTED_ANCHORS[1], 1)[0]
        merkylka = source.split(senate.UNVOTED_ANCHORS[1], 1)[1].split("\nACT. 287\n", 1)[0]
        self.assertNotIn("Опрос завершён", special)
        self.assertNotIn("Опрос завершён", merkylka)
        for text in (senate.build_bb(False), senate.build_bb(True)):
            self.assertIn("Merkylka Fair, номер паспорта 62277", text)
            self.assertIn("Jhonny Scoutezaki, номер паспорта 164317", text)
            self.assertIn("Dmitriy Grayrat, номер паспорта 40117", text)
            self.assertIn("вопроса о назначении специального прокурора", text.lower())
            self.assertIn("Qwikus Killa, номер паспорта 11736", text)
            self.assertIn("Pravik Killaz, номер паспорта 91999", text)
            self.assertIn("фамилия также указана как Killa", text)
            self.assertIn("номер паспорта Angel Insomnia не установлен", text)
            self.assertIn(senate.UNCONSIDERED_REASON, text)
            self.assertEqual(text.count("[B]не рассматривалась[/B]"), 2)
            for question, url in senate.UNCONSIDERED:
                self.assertIn(f"[URL='{url}']{question}[/URL]", text)
            self.assertNotIn("Что смешного", text)
            self.assertNotIn("обойдутся", text)
            self.assertNotIn("youtu.be", text)
            self.assertNotIn("\u2014", text)
            self.assertNotIn("\u2013", text)

    def test_bb_tables_match_canonical_data_and_links(self):
        for protocol in (False, True):
            with self.subTest(protocol=protocol):
                bb = senate.build_bb(protocol)
                check_balanced_bb(self, bb)
                rows = table_rows(bb)
                polls = senate.POLLS if protocol else senate.RESULT_POLLS
                self.assertEqual(len(rows), len(polls) + 1)
                for cells, poll in zip(rows[1:], polls):
                    self.assertEqual(len(cells), 8 if protocol else 6, poll.key)
                    expected = ([poll.interval, poll.active, poll.yes, poll.no, poll.abstain,
                                 poll.threshold, poll.outcome] if protocol else
                                [poll.interval, poll.yes, poll.no, poll.abstain, poll.outcome])
                    actual = [untag(cells[0])] + [untag(cell) for cell in cells[2:]]
                    self.assertEqual(actual, [str(x) for x in expected], poll.key)
                    self.assertIn(poll.title, cells[1])
                    self.assertIn(poll.meta, cells[1])
                    if poll.detail:
                        self.assertIn(senate.bb_text(poll.detail), cells[1])
                    if poll.url:
                        self.assertIn(poll.url, cells[1])
                    if poll.key == "294":
                        self.assertIn(f"[URL='{poll.url}']Исходная редакция[/URL]", cells[1])
                        self.assertIn(f"[URL='{senate.REVISED_294_URL}']исправленная редакция[/URL]", cells[1])
                self.assertIn(senate.UNVOTED_CEC_URL, bb)
                self.assertIn(senate.SPECIAL_PROSECUTOR_URL, bb)

    def test_notes_are_concise_and_keep_publication_caveat(self):
        bills = [p for p in senate.POLLS if p.key.isdigit()]
        self.assertEqual(sum(p.outcome == "Принят" for p in bills), 9)
        self.assertEqual(sum(p.outcome == "Не принят" for p in bills), 4)
        self.assertEqual(len(senate.RESULT_NOTES), 2)
        self.assertEqual(len(senate.PROTOCOL_NOTES), 1)
        for protocol in (False, True):
            with self.subTest(protocol=protocol):
                bb = senate.build_bb(protocol)
                notes = bb.split(senate.bb_heading("Примечания"), 1)[1].split("[RIGHT]", 1)[0]
                self.assertEqual(notes.count("[*]"), 1 if protocol else 2)
                self.assertIn(senate.ENACTMENT_NOTE, notes)
                self.assertNotIn("ACT. 294", notes)
                self.assertNotIn("Qwikus", notes)
                self.assertNotIn("Scoutezaki", notes)
                self.assertNotIn("http", notes)
                if not protocol:
                    self.assertIn("приняты 9 законопроектов, не приняты - 4", notes)
                self.assertLess(len(untag(notes)), 250)

    def test_bb_font_sizes_and_more_saturated_red(self):
        self.assertEqual((senate.BB_BODY_SIZE, senate.BB_META_SIZE, senate.BB_HEADING_SIZE), (5, 3, 6))
        self.assertEqual(senate.BB_REJECTED_COLOR, "rgb(210, 55, 55)")
        for protocol in (False, True):
            with self.subTest(protocol=protocol):
                bb = senate.build_bb(protocol)
                polls = senate.POLLS if protocol else senate.RESULT_POLLS
                rows = table_rows(bb)
                self.assertEqual(bb.count("[SIZE=3]"), len(polls))
                self.assertEqual(bb.count("[SIZE=6]"), 7)
                self.assertNotIn("[SIZE=2]", bb)
                self.assertNotIn("rgb(235, 107, 86)", bb)
                self.assertEqual(bb.count(f"[COLOR={senate.BB_REJECTED_COLOR}]Не принят[/COLOR]"), 4)
                self.assertIn("[COLOR=rgb(97, 189, 109)]Принят[/COLOR]", bb)
                for cells in rows:
                    for cell in cells:
                        self.assertIn("[SIZE=5]", cell)
                for poll in polls:
                    self.assertIn(f"[SIZE=3]{poll.meta}[/SIZE]", bb)
                self.assertIn(senate.bb_text(senate.UNCONSIDERED_REASON), bb)
                check_balanced_bb(self, bb)

    def test_meeting_files_are_sorted_in_date_directory(self):
        session = ROOT / "Повестка" / "13.11.2026"
        self.assertEqual(senate.SESSION, session)
        for name in ("01 Созыв", "02 Повестка", "03 Итоги", "04 Протокол", "05 Журнал", "06 Исходные данные"):
            self.assertTrue((session / name).is_dir(), name)
        self.assertTrue((session / "01 Созыв" / "Созыв заседания Сената - 13.11.2026.png").is_file())
        self.assertTrue((session / "02 Повестка" / "Повестка заседания 13.11.2026.png").is_file())
        self.assertTrue((session / "05 Журнал" / "The Senate of San Andreas 19.xlsx").is_file())
        self.assertTrue((session / "06 Исходные данные" / "Результаты.txt").is_file())
        self.assertTrue((ROOT / "Повестка" / "Образцы" / "message.txt").is_file())
        for path in (senate.RESULT_BB, senate.RESULT_PNG, senate.PROTOCOL_BB, senate.PROTOCOL_PNG):
            self.assertTrue(path.is_file())
            self.assertTrue(path.is_relative_to(session))
        index = (session / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", index)
        local_links = [link for link in links if not link.startswith("https://")]
        self.assertEqual(len(local_links), 5)
        for link in local_links:
            self.assertTrue((session / unquote(link)).is_file(), link)
        self.assertIn(senate.BY_KEY["296"].url, links)
        self.assertIn(senate.BY_KEY["298"].url, links)

    def test_publication_output_matches_generator(self):
        for path, protocol in ((senate.RESULT_BB, False), (senate.PROTOCOL_BB, True)):
            self.assertEqual(path.read_text(encoding="utf-8"), senate.build_bb(protocol))
        for path in (senate.RESULT_PNG, senate.PROTOCOL_PNG):
            with Image.open(path) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.width, 3000)
                self.assertGreater(image.height, 4000)
                self.assertGreater(path.stat().st_size, 100_000)

    def test_png_render_uses_no_links_or_service_labels(self):
        try:
            fonts = senate.font_faces()
        except SystemExit:
            self.skipTest("Times New Roman не установлен; SENATE_FONT_DIR для полной проверки")
        for protocol in (False, True):
            scratch = Image.new("RGB", (1, 1), "white")
            painter = senate.DocumentPainter(ImageDraw.Draw(scratch), scratch, fonts, True)
            senate.draw_document(painter, protocol)
            visible = " ".join(painter.texts)
            self.assertNotIn("https://", visible)
            self.assertNotIn("Google Docs", visible)
            self.assertIn("Jonny", visible)
            self.assertIn("Afelia", visible)
            self.assertIn("296", visible)
            for key in ("open", "cec_governor", "293", "294", "close"):
                self.assertIn(senate.BY_KEY[key].detail, visible)
            self.assertEqual(painter.texts.count("19:00-19:05"), 1)
            self.assertEqual(painter.texts.count("20:53-20:54"), 1)
            self.assertNotIn("Вы проголосовали за этот ответ", visible)
            for p in senate.POLLS if protocol else senate.RESULT_POLLS:
                self.assertIn(p.interval, visible)


if __name__ == "__main__":
    unittest.main()
