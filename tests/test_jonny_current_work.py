# -*- coding: utf-8 -*-
"""Навигация, сохранность источников и доказательства в комплекте по делу № 105."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
CASE_ROOT = ROOT / "Компромат на Jonny Zakonov"
WORK = CASE_ROOT / "Текущая работа"
ARCHIVE = WORK / "Общие исходные материалы из архива/Discord голосования.md"
CHANNEL = "https://discord.com/channels/1514607659758653560/1515423283606982776"
RESPONSE = WORK / "Иск № 105 и связанные дела/04 Ответ на запрос суда - BB-код.txt"
OBJECTIONS = WORK / "Иск № 105 и связанные дела/05 Возражения по существу и срокам - BB-код.txt"
INSTRUCTIONS = WORK / "Иск № 105 и связанные дела/06 Перед подачей.md"
SUBMISSION = WORK / "Иск № 99/01 Представление материалов Сената - BB-код.txt"
REPORT = WORK / "00 Хронология и прогноз.docx"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def topic_records(source):
    """Тема, исходная ссылка, время и видимые голоса из записей неизменённой выгрузки."""
    parts = re.split(r"(?m)^## ([0-9]+)[.] ", source)
    records = {}
    for i in range(1, len(parts), 2):
        number, body = int(parts[i]), parts[i + 1]
        publication = re.search(r"\*\*Ссылка на публикацию:\*\* (https://\S+)", body)
        ids = re.search(r"\*\*ID публикации / сообщения:\*\* `([0-9]+)` / `([0-9]+)`", body)
        time = re.search(r"\*\*Сообщение с итогами:\*\* [0-9-]+ ([0-9:]+) MSK", body)
        if not (publication and ids and time):
            raise AssertionError(f"Неполная запись выгрузки: {number}")
        url = publication.group(1)
        parsed = urlsplit(url)
        segments = parsed.path.strip("/").split("/")
        if (parsed.netloc != "discord.com" or len(segments) != 4
                or segments[0] != "channels" or segments[3] != ids.group(1)):
            raise AssertionError(f"Неверная ссылка публикации: {number}")
        direct_topic = f"https://discord.com/channels/{segments[1]}/{segments[3]}"
        votes = {}
        for vote in re.finditer(r"(?m)^- \*\*([^—\n]+) — ([0-9]+) голос", body):
            name = vote.group(1).strip().lower()
            if name in {"за", "да"}:
                votes["for"] = int(vote.group(2))
            elif name in {"против", "протиив", "нет"}:
                votes["against"] = int(vote.group(2))
            elif name.startswith("воз"):
                votes["abstain"] = int(vote.group(2))
        records[number] = {
            "publication": url,
            "topic": direct_topic,
            "time": time.group(1),
            "votes": votes,
            "body": body,
        }
    return records


def assert_balanced_bbcode(testcase, text):
    """Проверить вложенность используемых в новых проектах BB-тегов."""
    stack = []
    for match in re.finditer(r"\[(/?)(CENTER|B|URL)(?:=[^\]]+)?\]", text, re.IGNORECASE):
        closing, tag = match.group(1), match.group(2).upper()
        if closing:
            testcase.assertTrue(stack, f"Лишний закрывающий тег {tag}")
            testcase.assertEqual(stack.pop(), tag, f"Неверная вложенность тега {tag}")
        else:
            stack.append(tag)
    testcase.assertEqual(stack, [], f"Незакрытые теги: {stack}")
    testcase.assertEqual(text.count("{{"), text.count("}}"))


class JonnyCurrentWorkTests(unittest.TestCase):
    def test_package_and_original_sources_have_separate_locations(self):
        for path in (WORK / "README.md", WORK / "02 Навигатор и уточнения.md",
                     RESPONSE, OBJECTIONS, INSTRUCTIONS, SUBMISSION, REPORT):
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
        original = CASE_ROOT / "Информация.7z"
        self.assertEqual(sha256(original),
                         "2093e8f21546f67cde071c8f2801828386f4de901691c8c9c94ce73cc0893567")
        self.assertTrue((CASE_ROOT / "Иск № 105 и связанные дела/README.md").is_file())
        self.assertEqual(sha256(ARCHIVE),
                         "cb8b741faf5e40e41eee9ce14bf1caad7a493dc10be3e01136bca94b652e5a94")

    def test_archive_index_points_to_byte_identical_copies(self):
        index = (WORK / "Указатель архивных источников.md").read_text(encoding="utf-8")
        pattern = r"^\| `([^`]+)` \| \[[^\]]+\]\(([^)]+)\).*? \| `([a-f0-9]{64})` \| ([0-9]+) \|$"
        rows = re.findall(pattern, index, flags=re.MULTILINE)
        self.assertEqual(len(rows), 42)
        self.assertEqual(len({row[2] for row in rows}), 37)
        for origin, href, expected, size in rows:
            with self.subTest(origin=origin):
                target = WORK / unquote(href)
                self.assertTrue(target.is_file(), href)
                self.assertEqual(target.stat().st_size, int(size))
                self.assertEqual(sha256(target), expected)

    def test_local_markdown_links_resolve(self):
        pages = [CASE_ROOT / "README.md",
                 CASE_ROOT / "Иск № 105 и связанные дела/README.md"] + [
            path for path in WORK.rglob("*.md")
            if "из архива" not in str(path.relative_to(WORK))
        ]
        for page in pages:
            text = page.read_text(encoding="utf-8")
            for href in re.findall(r"\]\(([^)]+)\)", text):
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                with self.subTest(page=page, href=href):
                    self.assertTrue((page.parent / unquote(parsed.path)).exists())
            visible_text = re.sub(r"\]\([^)]+\)", "]", text)
            with self.subTest(page=page):
                self.assertNotRegex(visible_text, r"(?<![A-Za-z0-9])[0-9]{17,20}(?![A-Za-z0-9])")

    def test_drafts_use_known_channel_publications_or_derived_topic_links(self):
        records = topic_records(ARCHIVE.read_text(encoding="utf-8"))
        self.assertEqual(len(records), 42)
        valid_urls = {CHANNEL} | {item["publication"] for item in records.values()} | {
            item["topic"] for item in records.values()
        }
        for draft in (RESPONSE, OBJECTIONS, SUBMISSION):
            text = draft.read_text(encoding="utf-8")
            with self.subTest(draft=draft):
                self.assertIn(CHANNEL, text)
                self.assertIn("сотрудники Government имеют доступ", text)
                urls = re.findall(r"https://discord[.]com/channels/[^'\]\s]+", text)
                self.assertTrue(any(url != CHANNEL for url in urls))
                for url in urls:
                    self.assertIn(url, valid_urls, url)
                visible_text = re.sub(r"\[URL='[^']+'\]", "[URL]", text)
                self.assertNotRegex(visible_text, r"(?<![0-9])[0-9]{17,20}(?![0-9])")
                self.assertEqual(text.count("[URL="), text.count("[/URL]"))
                self.assertEqual(text.count("{{"), text.count("}}"))

    def test_each_disputed_poll_has_the_right_direct_topic_time_and_votes(self):
        records = topic_records(ARCHIVE.read_text(encoding="utf-8"))
        text = RESPONSE.read_text(encoding="utf-8")
        groups = {
            "09.11": [
                ("ACT. 277", 7), ("ACT. 278", 8), ("ACT. 279", 9),
                ("ACT. 280", 10), ("ACT. 282", 11), ("Инициатива о ЦИК", 12),
                ("ACT. 283", 13), ("ACT. 284", 14), ("ACT. 285", 15),
            ],
            "13.11": [
                ("Открытие заседания", 17), ("Инициатива о Jonny и партии", 18),
                ("Инициатива Губернатора об избрании ЦИК", 19),
                ("ACT. 286", 20), ("ACT. 287", 21), ("ACT. 288", 22),
                ("ACT. 298", 23), ("ACT. 289", 24), ("ACT. 290", 25),
                ("ACT. 291", 26), ("ACT. 292", 27), ("ACT. 293", 28),
                ("ACT. 294", 29), ("ACT. 295", 30), ("ACT. 296", 31),
                ("ACT. 297", 32), ("Избрание Afelia Suspect Вице-Спикером", 33),
                ("Закрытие заседания", 34),
            ],
            "19.11": [
                ("Открытие заседания", 35), ("ACT. 299 и ACT. 300", 36),
                ("ACT. 301", 37), ("ACT. 303", 38), ("ACT. 308", 39),
                ("Замена члена ЦИК", 40), ("ACT. 309", 41), ("Закрытие заседания", 42),
            ],
        }
        for date, expected in groups.items():
            marker = f"[B]{date} — результаты по "
            self.assertEqual(text.count(marker), 1)
            group_text = text.split(marker, 1)[1].split("\n\n", 1)[0]
            lines = [line for line in group_text.splitlines() if line.startswith("- ")]
            self.assertEqual(len(lines), len(expected), date)
            for (label, number), line in zip(expected, lines):
                with self.subTest(date=date, label=label):
                    record = records[number]
                    self.assertTrue(line.startswith(f"- {label} — "), line)
                    self.assertIn(record["topic"], line)
                    self.assertIn(f"отметка сообщения {record['time']} UTC+3", line)
                    self.assertEqual(set(record["votes"]), {"for", "against", "abstain"})
                    counts = " / ".join(str(record["votes"][key])
                                        for key in ("for", "against", "abstain"))
                    self.assertIn(counts, line)
                    if number == 12:
                        self.assertIn("7 / 6 / 0", line)
                        self.assertIn("причину расхождения", line)
        self.assertIn(records[6]["topic"], text)
        self.assertIn(records[6]["time"], text)
        self.assertIn("адреса тем составлены", text)
        self.assertIn("они не проверены по оригиналу", text)

    def test_poll_list_counts_and_outcomes_match_archived_published_results(self):
        cabinet = WORK / "Иск № 105 и связанные дела/07 Источники из архива/Кабинет Спикер Сената.json"
        posts = {post["n"]: post.get("text", "").replace("\u200b", "")
                 for post in json.loads(cabinet.read_text(encoding="utf-8"))["posts"]}
        response = RESPONSE.read_text(encoding="utf-8")
        numbers = {
            "09.11": (8, [277, 278, 279, 280, 282, 283, 284, 285]),
            "13.11": (10, list(range(286, 299))),
            "19.11": (12, [299, 300, 301, 303, 308, 309]),
        }
        for date, (post_number, act_numbers) in numbers.items():
            group = response.split(f"[B]{date} — результаты по ", 1)[1].split("\n\n", 1)[0]
            for number in act_numbers:
                with self.subTest(date=date, act=number):
                    act = re.compile(rf"ACT[.] {number}(?![0-9])")
                    source = next(line for line in posts[post_number].splitlines() if act.search(line))
                    target = next(line for line in group.splitlines() if act.search(line))
                    match = re.search(r"\|\s*([0-9]+)\s*\|\s*([0-9]+)\s*\|\s*([0-9]+)\s*\|", source)
                    self.assertIsNotNone(match, source)
                    self.assertIn(" / ".join(match.groups()), target)
                    outcome = "не принят" if "Не принят" in source else "принят"
                    self.assertIn(outcome, target.lower())
        # По ЦИК 09.11 публикация и выгрузка не совпадают; обе версии явно сохранены.
        self.assertIn("7 | 6 | 0 | Не принят", posts[8])
        self.assertIn("7 / 6 / 0", response)
        self.assertIn("8 / 6 / 0", response)

    def test_response_is_clear_partial_and_preserves_unavailable_evidence(self):
        text = RESPONSE.read_text(encoding="utf-8")
        for required in (
            "Что я представляю и чего прошу", "частичный ответ", "не подтверждает полномочий представлять Сенат",
            "1. Что запросил суд", "2. На каком основании", "3. Как избирался Спикер",
            "4. Что показывают материалы", "5. Ссылки на конкретные голосования",
            "6. Какие запрошенные первичные документы пока не приложены", "отдельное решение об избрании",
            "протокол соответствующего голосования", "поимённая регистрация явки",
            "причину", "место нахождения", "каждого", "48 часов с получения запроса",
            "Протоколы имеются и представляются", "подготовлены после заседаний",
            "не выдаются за файлы, составленные непосредственно в ходе заседаний",
            "23.11.2026, в 15:58", "25.11.2026, 15:58",
            "не обязательно является временем завершения голосования",
            "вопрос в выгрузке не распознан", "не доказывает законность нового назначения",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertEqual(len(re.findall(r"\{\{[^{}]+\}\}", text)), 4)
        assert_balanced_bbcode(self, text)
        instructions = INSTRUCTIONS.read_text(encoding="utf-8")
        self.assertIn("одно общее поле", instructions)
        self.assertIn("по каждому", instructions)
        self.assertIn("не придумывайте", instructions.lower())

    def test_objections_dont_overstate_identity_or_deadline(self):
        text = OBJECTIONS.read_text(encoding="utf-8")
        self.assertIn("По моим сведениям, Jonny Zakonov участвовал", text)
        self.assertIn("сопоставлении записи сохранённого опроса с его личностью", text)
        self.assertIn("независимое подтверждение принадлежности аккаунта", text)
        self.assertNotIn("uhge", text)
        self.assertNotIn("jhonnyycc", text)
        self.assertIn("Если указанные времена, часовой пояс UTC+3", text)
        self.assertIn("Не прошу автоматически считать все требования за эту дату просроченными", text)
        self.assertIn("каждому подтверждённому пропуску", text)
        self.assertIn("не проверенный оригинал", text)
        self.assertEqual(len(re.findall(r"\{\{[^{}]+\}\}", text)), 0)
        self.assertIn("25.11.2026", text)
        self.assertIn("Подпись: Nomad", text)
        assert_balanced_bbcode(self, text)

    def test_report_contains_channel_link_and_access_note(self):
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with ZipFile(REPORT) as doc:
            self.assertIsNone(doc.testzip())
            content = ElementTree.fromstring(doc.read("word/document.xml"))
            text = "".join(element.text or "" for element in content.findall(".//w:t", ns))
            rels = ElementTree.fromstring(doc.read("word/_rels/document.xml.rels"))
            self.assertIn("сотрудники Government имеют доступ", text)
            self.assertNotRegex(text, r"(?<![0-9])[0-9]{17,20}(?![0-9])")
            self.assertIn(CHANNEL, {relation.get("Target") for relation in rels})


if __name__ == "__main__":
    unittest.main()
