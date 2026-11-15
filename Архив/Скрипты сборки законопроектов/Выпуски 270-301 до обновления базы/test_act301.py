# -*- coding: utf-8 -*-
"""Проверки проекта ACT. 301, исходных норм и процессуальных сценариев."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_act301 as bill  # noqa: E402
from billkit import load  # noqa: E402
from check_docx import check  # noqa: E402
from make_acts import _lines  # noqa: E402

ACT = bill.OUT / bill.FILE
ACT289 = (
    ROOT / "Законопроекты" / "Законопроекты 289 (адвокат и закрытые территории)"
    / "ACT.289.Закон об адвокатской деятельности (адвокат и закрытые территории).docx"
)
ACT294 = (
    ROOT / "Законопроекты" / "Законопроекты 294 (вызов прокурора адвокатом)"
    / "ACT.294.Процессуальный кодекс (вызов прокурора адвокатом).docx"
)
ACT300 = (
    ROOT / "Законопроекты" / "Законопроекты 300 (вызов прокурора руководством Коллегии)"
    / "ACT.300.Процессуальный кодекс.docx"
)


def section(text, number):
    marker = f"ч. {number}.\n"
    result = text.split(marker, 1)[1]
    next_part = re.search(r"\nч\. \d+\.\n", result)
    return result[:next_part.start()] if next_part else result


def actual_segments(paragraph):
    result = []
    for run in paragraph.runs:
        shd = run._r.rPr.find(qn("w:shd"))
        fill = None if shd is None else shd.get(qn("w:fill"))
        result.append((run.text, fill, bool(run.bold)))
    return result


class Act301Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = Document(ACT)
        cls.table = cls.doc.tables[0]
        cls.source = load(bill.PC)
        cls.law = load(bill.AD_SOURCE)
        cls.appendix = load(bill.APP_SOURCE)
        cls.marked_rows = bill.prepare_rows()

    def test_original_sources_match_reference_and_new_article_is_free(self):
        for source_name in (bill.PC, bill.AD_SOURCE, bill.APP_SOURCE):
            filename = source_name if source_name.endswith(".json") else source_name + ".json"
            base = ROOT / "Законодательная база" / filename
            reference = ROOT / "Новая законка" / filename
            self.assertEqual(base.read_bytes(), reference.read_bytes(), source_name)
        self.assertFalse(any(
            re.match(r"^\s*Статья\s+17\.3(?:\D|$)", text)
            for text in self.source.values()
        ))
        for number, heading in ((25, "Статья 17\n"), (35, "Статья 22\n"), (36, "Статья 23\n")):
            self.assertTrue(self.source[number].startswith(heading))
        self.assertTrue(self.law[17].startswith("Статья 8. Клиент\n"))
        self.assertTrue(self.appendix[7].startswith("Статья 4\n"))
        self.assertIsNone(re.search(r"^\s*Примечание\s+2\.1(?:\s|:|$)",
                                    self.appendix[7], re.MULTILINE))
        original_note = bill.one_line(self.appendix[7], "Примечание 2: Государственные и частные адвокаты")
        self.assertEqual(
            'Примечание 2: Государственные и частные адвокаты могут проходить на территорию КПЗ, '
            'а также направляться в/из КПЗ только в рамках вызова через телефон, если ранее с адвокатом '
            'был заключен договор, или через приложение "Адвокаты". После окончания вызова адвокат '
            'обязан в течение 5 минут покинуть данную территорию.', original_note)

    def test_builder_rejects_occupied_article_and_changed_law_source(self):
        occupied = dict(self.source)
        occupied[9999] = "Статья 17.3\nУже существующая норма"
        with patch.object(bill, "load", return_value=occupied):
            with self.assertRaisesRegex(ValueError, "Статья 17.3"):
                bill.prepare_rows()
        changed_law = dict(self.law)
        changed_law[17] = "Статья 9. Другая норма"
        def load_changed(name):
            return self.source if name == bill.PC else changed_law
        with patch.object(bill, "load", side_effect=load_changed):
            with self.assertRaisesRegex(ValueError, "статьи 8"):
                bill.prepare_rows()
        occupied_app = dict(self.appendix)
        occupied_app[7] += "\nПримечание 2.1: Уже существующая норма."
        def load_occupied(name):
            return {bill.PC: self.source, bill.AD_SOURCE: self.law,
                    bill.APP_SOURCE: occupied_app}[name]
        with patch.object(bill, "load", side_effect=load_occupied):
            with self.assertRaisesRegex(ValueError, "Примечание 2.1"):
                bill.prepare_rows()

    def test_template_header_structure_and_exact_left_columns(self):
        self.assertEqual([], check(str(ACT)))
        pars = [p.text for p in self.doc.paragraphs]
        self.assertEqual("ACT. 301", pars[0])
        self.assertEqual("IN THE SENATE OF THE STATE OF SAN ANDREAS", pars[2])
        self.assertEqual("NOVEMBER 14, 2026", pars[3])
        self.assertEqual("SECTION 1. СУТЬ ПРАВКИ.", pars[8])
        self.assertEqual(["настоящая редакция", "предложенный вариант"],
                         [cell.text for cell in self.table.rows[0].cells])
        self.assertEqual(len(self.marked_rows) + 1, len(self.table.rows))
        p17, p22, p23, law8 = self.source[25], self.source[35], self.source[36], self.law[17]
        expected = [
            (bill.PC, "Статья 17, часть 4", bill.one_line(p17, "В случае если задержанный требует государственного адвоката,")),
            (bill.PC, "Статья 17, часть 4.1, абзац 1", bill.one_line(p17, "В случае, если задержанный требует самостоятельно вызвать частного адвоката,")),
            (bill.PC, "Статья 17, часть 4.1, примечание 1", bill.one_line(p17, "В случае с частным адвокатом,")),
            (bill.PC, "Статья 17, часть 4.1, примечание 2", bill.one_line(p17, "Если в течение 3 минут с момента обращения,")),
            (bill.PC, "Статья 17, часть 5, примечание о телефонном звонке", bill.one_line(p17, "Телефонный звонок, предоставляемый задержанному")),
            (bill.PC, "Статья 17.3", "В действующей редакции отсутствует."),
            (bill.PC, "Статья 22, часть 1, пункт «а»", bill.one_line(p22, "а) Подозреваемый имеет право на один телефонный звонок")),
            (bill.PC, "Статья 23, часть 1, пункт «б»", bill.one_line(p23, "б) Разъяснить адвокату, прокурору причины задержания;")),
            (bill.AD_TITLE, "Статья 8, часть 1, пояснение 4", bill.one_line(law8, "Пояснение 4: В случае если с доверителем/подзащитным")),
            (bill.APP_TITLE, "Статья 4, примечание 2.1", "В действующей редакции отсутствует."),
        ]
        for row, (act, locator, source) in zip(self.table.rows[1:], expected):
            self.assertEqual(f"{act}\n{locator}\n{source}", row.cells[0].text, locator)
        self.assertEqual(f"{bill.PC}\nСтатья 17.3\n{bill.NEW_ARTICLE}",
                         self.table.rows[6].cells[1].text)
        note = re.sub(r"\[\[/?[RGB]\]\]", "", bill.APP_NEW_NOTE)
        self.assertEqual(f"{bill.APP_TITLE}\nСтатья 4, примечание 2.1\n{note}",
                         self.table.rows[10].cells[1].text)
        self.assertIsNone(self.table.rows[6]._tr.find(qn("w:trPr"))
                          if self.table.rows[6]._tr.trPr is None
                          else self.table.rows[6]._tr.trPr.find(qn("w:cantSplit")))

    def test_docx_colours_bold_fonts_and_hyphens(self):
        for row, expected in zip(self.table.rows[1:], self.marked_rows):
            for cell, markup in zip(row.cells, expected):
                lines = _lines(markup)
                self.assertEqual(len(lines), len(cell.paragraphs))
                for p, expected_segments in zip(cell.paragraphs, lines):
                    self.assertEqual(expected_segments, actual_segments(p), p.text[:80])
        paragraphs = list(self.doc.paragraphs)
        for row in self.table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
        text = "\n".join(p.text for p in paragraphs)
        self.assertNotRegex(text, r"[—–−→]")
        self.assertNotIn("[[", text)
        self.assertNotIn("]]", text)
        for title in (bill.PC, bill.AD_TITLE, bill.APP_TITLE,
                      "Процессуального кодекса штата Сан-Андреас",
                      "Закона «Об адвокатской деятельности и адвокатуре в штате Сан-Андреас»"):
            runs = [r for p in paragraphs for r in p.runs if title in r.text]
            self.assertTrue(runs, title)
            self.assertTrue(all(r.bold for r in runs), title)
        with zipfile.ZipFile(ACT) as archive:
            font_parts = [n for n in archive.namelist()
                          if n in {"word/document.xml", "word/styles.xml"}
                          or re.match(r"word/(?:header|footer)\d+\.xml$", n)]
            for name in font_parts:
                root = etree.fromstring(archive.read(name))
                for fonts in root.iter(qn("w:rFonts")):
                    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
                        self.assertEqual("Times New Roman", fonts.get(qn("w:" + attr)),
                                         f"{name}: {attr}")

    def test_refusal_three_minutes_and_both_alternatives(self):
        second = section(bill.NEW_ARTICLE, 2)
        self.assertIn("сотрудник обязан предложить задержанному обращение к адвокату другого вида", second)
        self.assertIn("по желанию задержанного обеспечить такое обращение", second)
        first_direction = second.split("а) ", 1)[1].split("\nб) ", 1)[0]
        second_direction = second.split("\nб) ", 1)[1].split("\n", 1)[0]
        self.assertIn("при непринятии вызова государственного адвоката", first_direction)
        self.assertIn("предоставить телефон", first_direction)
        self.assertIn("частному адвокату через приложение «Адвокаты»", first_direction)
        self.assertIn("при непринятии вызова частного адвоката", second_direction)
        self.assertIn("вызвать государственного адвоката по горячей линии Правительства", second_direction)
        self.assertIn("в течение 3 минут с момента обращения", bill.ANSWER_NEW)
        self.assertIn("подтверждения о его принятии адвокатом", bill.ANSWER_NEW)
        self.assertIn("окончательный отказ", bill.ANSWER_NEW)
        self.assertIn("отказ отдельного адвоката не является окончательным", bill.ANSWER_NEW.lower())
        self.assertIn("принятия того же обращения другим адвокатом", bill.ANSWER_NEW)
        self.assertIn("Срок ожидания ответа исчисляется отдельно по каждому вызову", second)
        self.assertIn("по тому же обращению не начинают заново срок ожидания ответа", second)
        self.assertIn("или прибытия по этому вызову", second)
        self.assertIn("Принятие первоначального вызова после истечения срока ожидания ответа", second)
        self.assertIn("само по себе не отменяет обязанности предложить альтернативный вызов", second)

    def test_accepted_first_unanswered_both_and_phone_not_conflated(self):
        first = section(bill.NEW_ARTICLE, 1)
        accepted = section(bill.NEW_ARTICLE, 3)
        failed = section(bill.NEW_ARTICLE, 4)
        self.assertIn("без направления вызова не является вызовом адвоката или телефонным звонком", first)
        self.assertIn("не лишает задержанного права требовать государственного адвоката", first)
        self.assertIn("Молчание само по себе не является отказом от адвоката", first)
        self.assertIn("адвокат принял первоначальный или альтернативный вызов", accepted)
        self.assertIn("сотрудник ожидает его прибытия", accepted)
        self.assertIn("не обязан дополнительно вызывать другого адвоката", accepted)
        self.assertIn("в том числе адвоката другого вида", accepted)
        self.assertIn("предоставлять телефон для такого вызова", accepted)
        self.assertIn("Право на один телефонный звонок", accepted)
        self.assertIn("в том числе для связи с адвокатом, принявшим вызов", accepted)
        self.assertIn("не прибыл в установленный срок", accepted)
        self.assertIn("вызовы государственного и частного адвокатов", failed)
        self.assertIn("право на адвоката считается реализованным для данного задержания", failed)
        self.assertIn("не обязан обеспечивать дополнительный вызов адвоката", failed)
        self.assertIn("Неиспользованное право на один телефонный звонок сохраняется", failed)
        self.assertIn("его использование не возобновляет сроки ожидания", failed)
        self.assertIn("прямом добровольном отказе", failed)
        self.assertIn("такой отказ не приравнивается к непринятию обоих вызовов", failed)
        self.assertIn("Признание права реализованным не означает фактического оказания юридической помощи",
                      bill.NEW_ARTICLE)

    def test_separate_phone_miranda_and_existing_evidence_are_preserved(self):
        p17 = self.source[25]
        miranda = bill.one_line(p17, "Правило Миранды:")
        self.assertIn("Вы имеете право на один телефонный звонок. Также Вы имеете право на адвоката.", miranda)
        self.assertFalse(any("часть 3" in row.cells[0].text for row in self.table.rows[1:]))
        original = bill.one_line(self.source[35], "а) Подозреваемый имеет право на один телефонный звонок")
        proposed = self.table.rows[7].cells[1].text.split("\n", 2)[2]
        self.assertEqual(original.replace(bill.PHONE_DURATION,
                                          bill.PHONE_DURATION + bill.PHONE_RIGHT_INSERT), proposed)
        self.assertIn("сотрудник обязан предоставить телефонный звонок задержанному по его запросу", proposed)
        self.assertIn("исключительно для связи с адвокатом", bill.PHONE_SCOPE_NEW)
        phone_proposed = self.table.rows[5].cells[1].text
        self.assertIn("звонок лицам, не обладающим статусом адвоката, не допускается", phone_proposed)
        self.assertIn("для заключения договора", phone_proposed)
        self.assertIn("без дополнительного телефонного звонка", section(bill.NEW_ARTICLE, 2))
        self.assertIn("направление заявки без телефонного звонка не считаются таким звонком", bill.NEW_ARTICLE)
        original_law = bill.one_line(self.law[17], "Пояснение 4: В случае если с доверителем/подзащитным")
        proposed_law = self.table.rows[9].cells[1].text.split("\n", 2)[2]
        self.assertTrue(proposed_law.startswith(original_law))
        self.assertIn("статьёй 17.3 Процессуального кодекса", proposed_law)
        self.assertIn("по требованию - предоставить доказательства", self.source[36])
        self.assertFalse(any("Статья 23, часть 1, пункт «в»" in row.cells[0].text
                             for row in self.table.rows))

    def test_arrival_clocks_freeze_recording_and_legal_guarantees(self):
        self.assertIn("принявший вызов, не приехал в течение 10 минут с момента принятия вызова", bill.STATE_TIME_NEW)
        self.assertIn("принявший вызов, не приехал в течение 10 минут", bill.PRIVATE_TIME_NEW)
        self.assertIn("окончания телефонного звонка, которым первоначально направлен вызов", bill.PRIVATE_TIME_NEW)
        self.assertIn("с момента направления заявки", bill.PRIVATE_TIME_NEW)
        timing = section(bill.NEW_ARTICLE, 5)
        for phrase in ("На время ожидания ответа по первоначальному и альтернативному вызовам", "по истечении 3 минут",
                       "с момента окончательного отказа", "Ожидание выбора задержанного само по себе",
                       "не является основанием приостановления", "учитываются один раз"):
            self.assertIn(phrase, timing)
        fixed = section(bill.NEW_ARTICLE, 6)
        for phrase in ("время направления каждого вызова", "прямой добровольный отказ",
                       "фиксируются на видеозаписи задержания", "не включает содержание конфиденциальной встречи",
                       "Не направленный вызов не считается непринятым", "при передаче процессуальных действий"):
            self.assertIn(phrase.lower(), fixed.lower())
        for phrase in ("не отменяют требований статьи 19", "участие адвоката в допросе",
                       "право на адвоката в суде", "прибывшего до окончания задержания",
                       "с соблюдением статьи 18", "требований доступа на территорию"):
            self.assertIn(phrase, fixed)
        for phrase in ("известные сотруднику фактические обстоятельства каждого вменяемого правонарушения",
                       "время, место и действия лица", "номер каждой вменяемой статьи",
                       "при задержании по ордеру", "Об изменении оснований задержания"):
            self.assertIn(phrase.lower(), bill.INFORM_NEW.lower())

    def test_access_clarification_preserves_exact_original_note(self):
        note2 = bill.one_line(self.appendix[7], "Примечание 2: Государственные и частные адвокаты")
        self.assertIn('или через приложение "Адвокаты"', note2)
        self.assertIn("После окончания вызова адвокат обязан в течение 5 минут", note2)
        self.assertFalse(any(row.cells[0].text.split("\n")[1] == "Статья 4, примечание 2"
                             for row in self.table.rows[1:]))
        new = self.table.rows[10].cells[1].text
        for phrase in ("принятый государственным адвокатом вызов по горячей линии Правительства",
                       "является вызовом через телефон", "заключённый при таком вызове",
                       "до прохода адвоката в КПЗ", "считается ранее заключённым договором",
                       "Иные установленные законодательством требования доступа"):
            self.assertIn(phrase, new)
        proposed_289 = Document(ACT289).tables[0].rows[1].cells[1].text
        self.assertIn("Статья 4, ч. 2, пункт «ж»", proposed_289)
        self.assertIn("через телефон, если ранее с адвокатом был заключен договор", proposed_289)
        self.assertIn("пункта «ж» части 2 статьи 4", new)

    def test_other_projects_have_separate_locators(self):
        table294 = Document(ACT294).tables[0]
        table300 = Document(ACT300).tables[0]
        self.assertIn("Статья 17, части 4.2-4.5", table294.rows[1].cells[0].text)
        self.assertIn("ч. 4.2.", table294.rows[1].cells[1].text)
        self.assertIn("ч. 4.5.", table294.rows[1].cells[1].text)
        self.assertIn("Статья 8.1", table300.rows[1].cells[0].text)
        self.assertIn("Статья 20, часть 2, пункт «ж»", table300.rows[2].cells[0].text)
        self.assertFalse(any("Статья 17.3" in cell.text for table in (table294, table300)
                             for row in table.rows for cell in row.cells))
        locators = [row.cells[0].text.split("\n")[1] for row in self.table.rows[1:]]
        self.assertIn("Статья 17.3", locators)
        self.assertFalse(any(x.startswith("Статья 20") for x in locators))

    def test_rebuild_reproduces_package_contents(self):
        original_out = bill.OUT
        with tempfile.TemporaryDirectory() as temp:
            try:
                bill.OUT = Path(temp)
                with redirect_stdout(StringIO()):
                    bill.main()
                with zipfile.ZipFile(ACT) as original, \
                     zipfile.ZipFile(Path(temp) / bill.FILE) as rebuilt:
                    self.assertEqual(set(original.namelist()), set(rebuilt.namelist()))
                    for name in original.namelist():
                        self.assertEqual(original.read(name), rebuilt.read(name), name)
            finally:
                bill.OUT = original_out


if __name__ == "__main__":
    unittest.main()
