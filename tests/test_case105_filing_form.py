# -*- coding: utf-8 -*-
"""Форма и сохранность отправленных текстов по делу № 105."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from tests.test_jonny_current_work import assert_balanced_bbcode, topic_records

try:
    import py7zr
except ImportError:
    py7zr = None


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "Компромат на Jonny Zakonov/Текущая работа"
PACKAGE = WORK / "Иск № 105 - исправленная редакция"
RESPONSE = PACKAGE / "01 Ответ на запрос - BB-код.txt"
OBJECTIONS = PACKAGE / "02 Возражения - BB-код.txt"
ARCHIVE = ROOT / "Ответ на ИСК.7z"
FORM = "Формы подачи исковых заявлений, жалоб, ходатайств и иных дел.json"
VOTES = WORK / "Общие исходные материалы из архива/Discord голосования.md"
PASSPORT = "https://skrinshoter.ru/seek0aCF5gc?a"
PROTOCOLS = (
    ("09.11.2026", "https://docs.google.com/document/d/1oCRxaGGvfieXgcAk8G0do5i5fXQbzpiCR45fxPy_b3c/edit?usp=sharing", False),
    ("13.11.2026", "https://docs.google.com/document/d/1HxDwWJ2N4d_4UTzk5-BMuYSGvXuP0aULRCnNDxmQGXE/edit?usp=sharing", True),
    ("19.11.2026", "https://docs.google.com/document/d/1kj12ZOxSxHKs-1Yd6QIWwDCYgH2jo-9V07aD5XH0Rfs/edit?usp=sharing", True),
)


def plain(text):
    return re.sub(r"\[(?:/?(?:CENTER|B|URL))(?:=[^\]]*)?\]", "", text, flags=re.I)


def squash(text):
    return " ".join(text.split())


def unpack_archive(destination):
    with py7zr.SevenZipFile(ARCHIVE) as archive:
        members = archive.list()
        if {member.filename for member in members} != {"1.txt", "2.txt", FORM}:
            raise AssertionError("Изменился состав архива с поданными текстами")
        if not all(member.is_file and not member.is_symlink for member in members):
            raise AssertionError("Архив должен содержать только файлы")
        archive.extractall(path=destination)


class Case105FilingFormTests(unittest.TestCase):
    def test_fields_follow_the_application_form_in_order(self):
        for path, title, date_label in (
            (RESPONSE, "ПРЕДСТАВЛЕНИЕ МАТЕРИАЛОВ И ПИСЬМЕННЫХ ПОЯСНЕНИЙ", "Дата подачи представления:"),
            (OBJECTIONS, "ОБРАЩЕНИЕ\nПИСЬМЕННЫЕ ВОЗРАЖЕНИЯ", "Дата подачи обращения:"),
        ):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                fields = (
                    "В Верховный Суд штата Сан-Андреас", "От: Marcus Nomad.",
                    "[B]Данные заявителя:[/B]", "Имя Фамилия: Marcus Nomad.",
                    "Номер паспорта: 85028.",
                    f"Копия паспорта заявителя: [URL='{PASSPORT}']копия паспорта[/URL]",
                    "Номер телефона: 28197253.", "Электронная почта: insideofdead@sa.com.",
                    title, "[B]ПРОШУ СУД:[/B]", "[B]МАТЕРИАЛЫ[/B]",
                    "С уважением, Marcus Nomad.", date_label, "Подпись заявителя: Nomad.",
                )
                positions = [text.index(field) for field in fields]
                self.assertEqual(positions, sorted(positions))
                self.assertEqual(text.count("[B]Данные заявителя:[/B]"), 1)
                self.assertEqual(text.count("[B]МАТЕРИАЛЫ[/B]"), 1)
                self.assertIn("административный ответчик по делу № 105", text)
                self.assertIn("25.11.2026", text)
                self.assertNotRegex(text, r"27[.]11[.]2026|27 ноября 2026")
                assert_balanced_bbcode(self, text)

    def test_materials_contain_correct_protocol_links_and_provenance(self):
        for path in (RESPONSE, OBJECTIONS):
            text = path.read_text(encoding="utf-8")
            materials = text.split("[B]МАТЕРИАЛЫ[/B]", 1)[1].split("С уважением", 1)[0]
            for number, (date, url, restored) in enumerate(PROTOCOLS, 1):
                label = f"Протокол заседания {date}"
                if restored:
                    label += " - восстановленные сведения"
                with self.subTest(path=path.name, date=date):
                    self.assertIn(f"{number}. [URL='{url}']{label}[/URL]", materials)
            self.assertIn("раздел", materials)
            urls = re.findall(r"\[URL='([^']+)'\]", text)
            self.assertTrue(urls)
            self.assertTrue(all(url.startswith("https://") and "\\" not in url for url in urls))
            for url in (url for url in urls if url.startswith("https://discord.com/")):
                parts = urlsplit(url).path.strip("/").split("/")
                self.assertEqual(len(parts), 3, f"Нужна ссылка на канал или тему, не на сообщение: {url}")
                self.assertEqual(parts[0], "channels")

    def test_vote_topics_and_timestamps_are_preserved(self):
        records = topic_records(VOTES.read_text(encoding="utf-8"))
        lines = RESPONSE.read_text(encoding="utf-8").splitlines()
        for number in (6, *range(7, 16), *range(17, 43)):
            record = records[number]
            with self.subTest(record=number):
                matches = [line for line in lines if record["topic"] in line]
                self.assertEqual(len(matches), 1)
                self.assertIn(record["time"], matches[0])
        response = RESPONSE.read_text(encoding="utf-8")
        self.assertIn("7 / 6 / 0", response)
        self.assertIn("8 / 6 / 0", response)
        self.assertIn("26 ноября 2026 года в 10:00", response)
        self.assertIn("Если этот момент совпадает с получением определения мной", response)

    @unittest.skipUnless(py7zr, "py7zr необходим для чтения исходного архива")
    def test_source_is_the_user_supplied_form_for_topic_3740273(self):
        with tempfile.TemporaryDirectory() as temp:
            unpack_archive(temp)
            document = json.loads((Path(temp) / FORM).read_text(encoding="utf-8-sig"))
        self.assertTrue(document["url"].endswith(".3740273"))
        self.assertEqual(document["parsed_at"], "2026-11-22 20:04:06")
        text = document["posts"][0]["text"]
        start = text.index("ФОРМА ПОДАЧИ ХОДАТАЙСТВ, ЗАЯВЛЕНИЙ ИЛИ ИНЫХ ОБРАЩЕНИЙ")
        end = text.index("ФОРМА ПЕРЕДАЧИ", start)
        form = text[start:end]
        fields = (
            "ПО КОНКРЕТНОМУ ДЕЛУ - В РАЗДЕЛ ИСКА/ЖАЛОБЫ/ДЕЛА",
            "В Верховный/Апелляционный/Окружной Суд", "От : [Nick Name]",
            "Данные заявителя:", "Имя Фамилия:", "Номер паспорта (ID-card):",
            "Копия паспорта заявителя: [*Гиперссылка*]", "Номер телефона:", "Электронная почта:",
            "ХОДАТАЙСТВО/ЗАЯВЛЕНИЕ/ОБРАЩЕНИЕ/ПРЕДСТАВЛЕНИЕ", "МАТЕРИАЛЫ",
            "С уважением", "Дата подачи", "Подпись заявителя",
        )
        positions = [form.index(field) for field in fields]
        self.assertEqual(positions, sorted(positions))

    @unittest.skipUnless(py7zr, "py7zr необходим для сравнения с поданными текстами")
    def test_submitted_arguments_are_preserved_in_the_reformatted_documents(self):
        with tempfile.TemporaryDirectory() as temp:
            unpack_archive(temp)
            for number, path, start in (
                (1, RESPONSE, "Во исполнение определения № 105-1"),
                (2, OBJECTIONS, "В связи с определениями № 105-2"),
            ):
                original = (Path(temp) / f"{number}.txt").read_text(encoding="utf-8-sig")
                section = original[original.index(start):original.index("С уважением", original.index(start))]
                revised = squash(plain(path.read_text(encoding="utf-8")))
                for line in section.splitlines():
                    line = squash(line)
                    if not line:
                        continue
                    if number == 1 and line == "Протоколы имеются и представляются:":
                        self.assertIn("Протоколы имеются и представляются.", revised)
                        continue
                    if number == 1 and line.startswith("- Протокол заседания "):
                        self.assertIn(line.removeprefix("- ").rstrip(";."), revised)
                        continue
                    if number == 1 and line.startswith("Истец просит представить полный перечень"):
                        self.assertIn("Истец просит представить полный перечень индивидуальных постановлений Marcus Nomad.", revised)
                        self.assertIn("Проекты законов сами по себе не являются индивидуальными постановлениями.", revised)
                        continue
                    with self.subTest(document=number, line=line[:100]):
                        self.assertIn(line, revised)


if __name__ == "__main__":
    unittest.main()
