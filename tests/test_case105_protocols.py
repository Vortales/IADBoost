# -*- coding: utf-8 -*-
"""Проверки происхождения, источников и комплекта восстановленных протоколов № 105."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from openpyxl import load_workbook

from tools import build_case105_protocols as builder
from tests.test_jonny_current_work import topic_records


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "Компромат на Jonny Zakonov/Текущая работа/Иск № 105 и связанные дела"
PACKAGE = CASE / "Ответ суду и протоколы"
ARCHIVE = ROOT / "Компромат на Jonny Zakonov/Текущая работа/Общие исходные материалы из архива/Discord голосования.md"
CABINET = CASE / "07 Источники из архива/Кабинет Спикер Сената.json"


def protocol(date):
    return PACKAGE / f"Протокол {date}.11.2026 - восстановленные сведения.docx"


def document_text(document):
    parts = [p.text for p in document.paragraphs]
    parts += [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    return "\n".join(parts)


def senate_record(value):
    """Имя и номер из разных форм записи реестра, без отождествления лиц."""
    match = re.fullmatch(r"(.+?)\s*(?:\|\s*|\s+)(\d+)\s*", str(value))
    if not match:
        raise AssertionError(value)
    return match.group(1).strip(), match.group(2)


def github_references():
    references = []
    for path in PACKAGE.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        references += re.findall(r"https://github[.]com/Vortales/IADBoost/blob/[^'\]\s)]+", text)
    for path in PACKAGE.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        references += re.findall(r"https://github[.]com/Vortales/IADBoost/blob/[^'\]\s)]+", text)
    for date in ("09", "13", "19"):
        doc = Document(protocol(date))
        references += [rel.target_ref for rel in doc.part.rels.values()
                       if rel.reltype == RT.HYPERLINK and rel.is_external
                       and rel.target_ref.startswith("https://github.com/Vortales/IADBoost/blob/")]
    return set(references)


class Case105ProtocolsTests(unittest.TestCase):
    def test_package_has_all_deliverables_and_matching_working_copies(self):
        for name in ("README.md", "00 Перед подачей.md", "01 Ответ на запрос - BB-код.txt",
                     "02 Возражения - BB-код.txt", "03 Состав Сената - предварительная сверка.md",
                     "04 Разбор и перечень документов.md"):
            self.assertTrue((PACKAGE / name).is_file(), name)
        for date in ("09", "13", "19"):
            self.assertTrue(protocol(date).is_file(), date)
        self.assertEqual((CASE / "04 Ответ на запрос суда - BB-код.txt").read_bytes(),
                         (PACKAGE / "01 Ответ на запрос - BB-код.txt").read_bytes())
        self.assertEqual((CASE / "05 Возражения по существу и срокам - BB-код.txt").read_bytes(),
                         (PACKAGE / "02 Возражения - BB-код.txt").read_bytes())

    def test_provenance_signature_date_and_document_structure(self):
        for date, row_count in (("09", 17), ("13", 19), ("19", 9)):
            with self.subTest(date=date):
                path = protocol(date)
                with ZipFile(path) as package:
                    self.assertIsNone(package.testzip())
                doc = Document(path)
                text = document_text(doc)
                self.assertIn("Восстановлен по сохранившимся материалам", text)
                self.assertIn("составлен после заседания", text.lower())
                self.assertIn("не подтверждает, что именно эта редакция велась", text)
                self.assertIn("Дата подготовки восстановленной версии: ____________________", text)
                self.assertIn("Подпись: ____________________", text)
                self.assertIn("Дата подписания: ____________________", text)
                self.assertIsNone(doc.core_properties.created)  # нет фиктивной даты шаблона 2013 г.
                self.assertIsNone(doc.core_properties.modified)
                self.assertEqual(len(doc.tables), 2)
                self.assertEqual(len(doc.tables[0].rows), 17)
                self.assertEqual(len(doc.tables[1].rows), row_count)
                available = doc.sections[0].page_width - doc.sections[0].left_margin - doc.sections[0].right_margin
                for table in doc.tables:
                    self.assertLessEqual(sum(col.width for col in table.columns), available)
                    for column, cell in zip(table.columns, table.rows[0].cells):
                        self.assertAlmostEqual(column.width.cm, cell.width.cm, places=1)
                    self.assertIsNotNone(table.rows[0]._tr.trPr.find(qn("w:tblHeader")))
                    for row in table.rows[1:]:
                        self.assertIsNotNone(row._tr.trPr.find(qn("w:cantSplit")))

    def test_builder_does_not_overwrite_user_edits_without_explicit_force(self):
        with tempfile.TemporaryDirectory() as temp:
            command = [sys.executable, str(ROOT / "tools/build_case105_protocols.py"), "--output-dir", temp]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
            files = sorted(Path(temp).glob("*.docx"))
            self.assertEqual(len(files), 3)
            files[0].write_bytes(b"manual edits")
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(files[0].read_bytes(), b"manual edits")
            subprocess.run(command + ["--force"], cwd=ROOT, check=True, capture_output=True, text=True)
            with ZipFile(files[0]) as package:
                self.assertIsNone(package.testzip())

    def test_saved_protocols_match_current_builders(self):
        for date, make in (("09", builder.build_09), ("13", builder.build_13), ("19", builder.build_19)):
            with self.subTest(date=date):
                saved = Document(protocol(date))
                built = make()
                self.assertEqual(saved._element.xml, built._element.xml)
                def links(doc):
                    return {rel.target_ref for rel in doc.part.rels.values()
                            if rel.reltype == RT.HYPERLINK and rel.is_external}
                self.assertEqual(links(saved), links(built))

    def test_roster_09_is_the_later_draft_not_claimed_attendance(self):
        old = Document(ROOT / "Сенат/Протокол заседания (09.11.2026)/Вариант Б - Протокол заседания Сената 09.11.2026 (составлен 12.11.2026).docx")
        expected = [(row.cells[2].text, row.cells[3].text) for row in old.tables[0].rows[1:]]
        self.assertEqual(expected, [(name, number.replace("*", "")) for _, name, number in builder.ROSTER_09])
        doc = Document(protocol("09"))
        self.assertTrue(all(row.cells[2].text == "Не установлена" for row in doc.tables[0].rows[1:]))
        text = document_text(doc)
        self.assertIn("не проверенный поимённый список явки", text)
        self.assertIn("в 20:53 и 20:58", text)
        self.assertIn("19:53:48 и 19:58:50", text)
        self.assertIn("7 / 6 / 0", text)
        self.assertIn("7 / 6 / 1", text)
        self.assertIn("8 / 6 / 0", text)

    def test_roster_13_discloses_journal_heading_and_users_account(self):
        path = ROOT / "Повестка/13.11.2026/05 Журнал/The Senate of San Andreas 19.xlsx"
        sheet = load_workbook(path, data_only=False)["Журнал заседаний 13.11"]
        self.assertEqual(sheet["A4"].value, "Сенаторы на заседании:")
        self.assertIsNone(sheet["B3"].value)
        expected = [senate_record(sheet[f"A{row}"].value) for row in range(5, 21)]
        self.assertEqual(expected, [(name, number.replace("*", "")) for _, name, number in builder.ROSTER_13])
        doc = Document(protocol("13"))
        text = document_text(doc)
        self.assertIn("включая Merkylka", text)
        self.assertIn("Если считать список отметкой явки", text)
        self.assertIn("при условии подтверждения", text)
        self.assertIn("20:52 заявлена замена от Government", text)
        for row in doc.tables[0].rows[1:]:
            self.assertEqual(row.cells[2].text,
                             "Не явился*" if "Merkylka Fair" in row.cells[1].text else "Присутствовал*")

    def test_roster_19_is_only_the_later_registry(self):
        path = ROOT / "Компромат на Jonny Zakonov/Единый реестр Штата Сан-Андреас.xlsx"
        sheet = load_workbook(path, data_only=False)["💼 Сенат Штата Сан-Андреас"]
        raw = [sheet.cell(row, col).value for row in range(4, 13) for col in (2, 4)] + [sheet["B15"].value]
        expected = [senate_record(value) for value in raw if value and value != "Не заявлен"]
        self.assertEqual(expected, [(name, number.replace("*", "")) for _, name, number in builder.ROSTER_19])
        doc = Document(protocol("19"))
        self.assertTrue(all(row.cells[2].text == "Не установлена" for row in doc.tables[0].rows[1:]))
        text = document_text(doc)
        self.assertIn("не подтверждает автоматически состав или явку на 19.11", text)
        self.assertIn("в 20:39 Jhonny Scoutezaki", text)
        self.assertIn("историческая версия реестра", text)

    def test_protocols_use_source_grounded_details_not_invented_attendance(self):
        posts = {post["n"]: post for post in json.loads(CABINET.read_text(encoding="utf-8"))["posts"]}
        text_09 = document_text(Document(protocol("09")))
        text_13 = document_text(Document(protocol("13")))
        text_19 = document_text(Document(protocol("19")))
        self.assertIn("Указ № 0012 назначал", text_09)
        self.assertIn("Точное время окончания заседания по доступным материалам не установлено", text_09)
        for date, text in (("13", text_13), ("19", text_19)):
            with self.subTest(date=date):
                self.assertIn("Капитолий штата Сан-Андреас", text)
                self.assertIn("Это интервалы опросов", text)
        for fragment in ("ACT. 286", "Kiray Fair", "ACT. 298", "Qwikus Killa",
                         "Jhonny Scoutezaki", "Dmitriy Grayrat"):
            with self.subTest(source="13", fragment=fragment):
                self.assertIn(fragment, posts[10]["text"])
                self.assertIn(fragment, text_13)
        self.assertIn("не самостоятельная регистрация явки", text_13)
        for fragment in ("ACT. 299", "Asher K.", "ACT. 308", "Pravik Killaz", "Jacob Killa"):
            with self.subTest(source="19", fragment=fragment):
                self.assertIn(fragment, posts[12]["text"])
                self.assertIn(fragment, text_19)
        self.assertEqual(posts[11]["date"], "13.11.2026 в 22:02")
        self.assertTrue(any("19 ноября 2026" in block.get("ocr_text", "") for block in posts[11]["blocks"]))
        self.assertIn("дата 19.11", text_19)
        self.assertIn("сообщение с ним датировано 13.11 в 22:02", text_19)
        self.assertIn("не подтверждает автоматически состав или явку на 19.11", text_19)

    def test_no_discord_account_names_in_protocols_or_court_texts(self):
        records = topic_records(ARCHIVE.read_text(encoding="utf-8"))
        names = set()
        for number in (1, 6, 17, 35):
            for raw in re.findall(r"\(\d+/\d+ видимых имён\):\s*([^\n]+)", records[number]["body"]):
                names.update(part.strip() for part in raw.split(";"))
        self.assertGreater(len(names), 20)
        # Имя человека в реестре не является запрещённым ником, даже если совпадает с ним.
        real_name_words = {word.casefold() for _, name, _ in builder.ROSTER_09 + builder.ROSTER_13 + builder.ROSTER_19
                           for word in re.findall(r"[A-Za-z0-9_]+", name)}
        nicknames = {name for name in names if name.casefold() not in real_name_words}
        texts = {f"protocol {date}": document_text(Document(protocol(date))) for date in ("09", "13", "19")}
        for filename in ("01 Ответ на запрос - BB-код.txt", "02 Возражения - BB-код.txt"):
            # Электронная почта ответчика - контакт, а не имя Discord-аккаунта.
            text = (PACKAGE / filename).read_text(encoding="utf-8")
            texts[filename] = re.sub(r"[\w.+-]+@[\w.-]+", "", text)
        for label, text in texts.items():
            for nickname in nicknames:
                with self.subTest(document=label, nickname=nickname):
                    pattern = r"(?<![\w])" + re.escape(nickname) + r"(?![\w])"
                    self.assertNotRegex(text.lower(), re.compile(pattern.lower()))

    def test_published_vote_counts_and_intervals(self):
        posts = {post["n"]: (post.get("text") or "").replace("\u200b", "")
                 for post in json.loads(CABINET.read_text(encoding="utf-8"))["posts"]}
        for post_num, rows in ((10, builder.VOTES_13), (12, builder.VOTES_19)):
            for time, question, _, counts, _ in rows:
                with self.subTest(post=post_num, time=time, question=question):
                    matching = [line for line in posts[post_num].splitlines() if line.startswith(time + " ")]
                    self.assertEqual(len(matching), 1)
                    parts = [part.strip() for part in matching[0].split("|")]
                    self.assertEqual(" / ".join(parts[2:5]), counts)
        for _, question, _, counts, _ in builder.VOTES_09[6:15]:
            with self.subTest(date="09", question=question):
                key = "Инициатива о ЦИК" if question == "Инициатива о ЦИК" else re.search(r"ACT[.] \d+", question).group()
                source = next(line for line in posts[8].splitlines() if key in line)
                parts = [part.strip() for part in source.split("|")]
                self.assertEqual(" / ".join(parts[2:5]), counts.replace("***", ""))
        records = topic_records(ARCHIVE.read_text(encoding="utf-8"))
        for number, row in enumerate(builder.VOTES_09[:6], 1):
            counts = " / ".join(str(records[number]["votes"][key]) for key in ("for", "against", "abstain"))
            self.assertEqual(row[0], records[number]["time"])
            self.assertEqual(row[3], counts)

    def test_deadline_condition_and_missing_document_placeholders(self):
        response = (PACKAGE / "01 Ответ на запрос - BB-код.txt").read_text(encoding="utf-8")
        guidance = (PACKAGE / "00 Перед подачей.md").read_text(encoding="utf-8")
        self.assertIn("23.11.2026, в 15:58", response)
        self.assertIn("25.11.2026, 15:58", response)
        self.assertIn("Если этот момент совпадает с получением определения мной, указан единый часовой пояс и отсчёт непрерывен", response)
        self.assertIn("Момент официального получения адресованного Сенату запроса отдельно не подтверждён", response)
        self.assertIn("только если получение определения вами совпало", guidance)
        self.assertIn("post-11841279", response)
        self.assertEqual(len(re.findall(r"\{\{[^{}]+\}\}", response)), 4)
        self.assertIn("ПО КАЖДОМУ ДОКУМЕНТУ ФАКТИЧЕСКУЮ ПРИЧИНУ И МЕСТО", response)
        self.assertIn("#L233-L234", response)  # подтверждение Merkylka 23:55, а не только 09:23

    def test_github_sources_exist_and_line_ranges_are_valid_in_pinned_commits(self):
        refs = github_references()
        self.assertGreaterEqual(len(refs), 10)
        for reference in refs:
            with self.subTest(reference=reference):
                parts = urlsplit(reference)
                segments = unquote(parts.path).split("/", 5)
                self.assertEqual(segments[:4], ["", "Vortales", "IADBoost", "blob"])
                rev, path = segments[4], segments[5]
                subprocess.run(["git", "cat-file", "-e", f"{rev}:{path}"], cwd=ROOT, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if parts.fragment:
                    match = re.fullmatch(r"L(\d+)(?:-L(\d+))?", parts.fragment)
                    self.assertIsNotNone(match)
                    content = subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=ROOT)
                    total = len(content.splitlines())
                    start = int(match.group(1))
                    end = int(match.group(2) or start)
                    self.assertTrue(1 <= start <= end <= total)


if __name__ == "__main__":
    unittest.main()
