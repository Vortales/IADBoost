# -*- coding: utf-8 -*-
"""Структура, источники и ключевые правовые ограничения ACT. 302-312."""
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import unittest
import zipfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import billkit
import build_acts302_312 as drafts
import check_docx

BASE = ROOT / "Законодательная база"
TOKEN = re.compile(r"\[\[/?(?:R|G|B)\]\]")


def plain(text):
    return TOKEN.sub("", text)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def right_rows(number):
    matches = [(folder, bill) for folder, bill in drafts.specs() if bill["num"] == number]
    if len(matches) != 1:
        raise AssertionError(number)
    folder, bill = matches[0]
    doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
    return [row.cells[1].text for row in doc.tables[0].rows[1:]]


def find_row(rows, locator):
    matches = [row for row in rows if locator in row.split("\n")[:2]]
    if len(matches) != 1:
        raise AssertionError((locator, len(matches)))
    return matches[0]


class BaseInventoryTests(unittest.TestCase):
    def test_manifest_json_and_unique_sources(self):
        records = (BASE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(records), 52)
        manifest = {}
        for record in records:
            digest, name = record.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertNotIn(name, manifest)
            manifest[name] = digest
        json_files = list(BASE.glob("*.json"))
        self.assertEqual(set(manifest), {p.name for p in json_files})
        sources = set()
        parsed_dates = []
        for path in json_files:
            with self.subTest(file=path.name):
                self.assertEqual(file_hash(path), manifest[path.name])
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(data["sections"])
                parsed_dates.append(data["parsed_at"][:10])
                url = data.get("norm_url") or data["url"]
                self.assertNotIn(url, sources)
                sources.add(url)
        self.assertEqual(parsed_dates.count("2026-11-15"), 44)
        self.assertEqual(parsed_dates.count("2026-11-18"), 8)
        self.assertFalse((BASE / "Конституционный закон «О нормативных правовых актах штата Сан-Андреас».json").exists())

    def test_billkit_loads_base_relative_to_the_checkout(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "Законодательная база").mkdir()
            kit = root / "tools/billkit.py"
            shutil.copy2(ROOT / "tools/billkit.py", kit)
            shutil.copy2(BASE / f"{drafts.PC}.json", root / "Законодательная база")
            spec = importlib.util.spec_from_file_location("portable_billkit", kit)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(Path(module.ROOT), root)
            self.assertEqual(module.load(drafts.PC), billkit.load(drafts.PC))

    def test_billkit_rejects_sources_outside_the_current_base(self):
        for name in ("../другая база/закон.json", str(ROOT / "Правила проекта/Основные правила проекта.json")):
            with self.subTest(name=name), self.assertRaises(ValueError):
                billkit.load(name)
        # Отсутствующий в срезе акт не ищется в архиве или другом месте.
        with self.assertRaises(FileNotFoundError):
            billkit.load("Закон “О политических партиях на территории штата San-Andreas”")

        with TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / "Законодательная база"
            base.mkdir()
            outside = root / "прежний.json"
            outside.write_text('{"sections": []}', encoding="utf-8")
            (base / "ссылка.json").symlink_to(outside)
            with patch.object(billkit, "BASE", str(base)), self.assertRaises(ValueError):
                billkit.load("ссылка")

    def test_old_locations_removed_and_unique_inputs_preserved(self):
        for name in ("Новая законка", "286", "Темы.7z", "Результаты сената.txt"):
            self.assertFalse((ROOT / name).exists(), name)
        for name in ("Справочные материалы прежней базы", "Законодательная база (устаревшие редакции)"):
            self.assertFalse((ROOT / "Архив" / name).exists(), name)
        self.assertEqual(list((ROOT / "Архив").rglob("*.json")), [])
        self.assertEqual(list(ROOT.glob("*.json")), [])
        preserved = {
            "Компромисс/Исходные данные/ACT286.txt": "1578110e7a2d48fba31fa7c8b61a3ff6d10debfabb2cceb0016e7d4b44d3b2b9",
            "Компромисс/Исходные данные/АСТ 286.docx": "ee9a2559024982a869d933ec85eb0d0cae901bf60f0830c0bb8bfe121cdbc4e7",
            "Сенат/Протокол заседания (09.11.2026)/Исходные результаты голосований 09.11.2026.txt": "70e7522f0732d539cf3e9d201bca3635c77c8caa7e08ea5890ed6526d81ca08f",
            "Законопроекты/_ШАБЛОН/ACT.260.Закон об охоте и рыбалке (лицензия FISHING).docx": "11bf05feeef06c4e939d53a43ef69ace6ec669479023d197e5cb4f2559ae20f8",
        }
        for path, digest in preserved.items():
            with self.subTest(path=path):
                self.assertEqual(file_hash(ROOT / path), digest)
        meeting_09 = ROOT / next(k for k in preserved if k.startswith("Сенат/"))
        meeting_13 = ROOT / "Повестка/13.11.2026/06 Исходные данные/Результаты.txt"
        self.assertNotEqual(file_hash(meeting_09), file_hash(meeting_13))
        self.assertTrue((ROOT / "Архив/Законопроекты 259-301 до обновления базы/Законопроекты 301 (право на адвоката при задержании)").is_dir())
        self.assertTrue((ROOT / "Архив/Законопроекты 259-301 до обновления базы/Законопроекты 293 (контроль за партиями)/ACT.293.Закон о политических партиях (контроль и приостановление деятельности).docx").is_file())


class HistoricalSourceTests(unittest.TestCase):
    def test_senate_builders_find_archived_user_template_without_writing_documents(self):
        import build_senat_initiative
        import build_senat_protocol
        import build_senat_results
        builders = (build_senat_initiative, build_senat_protocol, build_senat_results)
        sources = {Path(builder.SRC) for builder in builders}
        self.assertEqual(1, len(sources))
        source = sources.pop()
        self.assertTrue(source.is_file())
        self.assertTrue(source.is_relative_to(ROOT / "Архив"))
        doc = Document(source)
        self.assertIn("Tommy Harlow", doc.paragraphs[5].text)
        self.assertGreaterEqual(len(doc.paragraphs), 27)


class PairTests(unittest.TestCase):
    def test_delete_is_absent_from_new_version(self):
        left, right = billkit.pair("до удалить после", [("D", "удалить", "")])
        self.assertEqual(left, "до [[R]]удалить[[/R]] после")
        self.assertEqual(right, "до  после")
        with self.assertRaises(ValueError):
            billkit.pair("до удалить после", [("D", "удалить", "другое")])

    def test_insert_and_replace_are_isolated(self):
        left, right = billkit.pair("альфа бета", [("R", "альфа", "гамма"),
                                                   ("I", "бета", " плюс")])
        self.assertEqual(left, "[[R]]альфа[[/R]] бета")
        self.assertEqual(right, "[[G]]гамма[[/G]] бета[[G]] плюс[[/G]]")
        with self.assertRaises(ValueError):
            billkit.pair("альфа", [("R", "не существует", "замена")])
        with self.assertRaises(ValueError):
            billkit.pair("альфа", [("R", "альфа", "")])
        with self.assertRaises(ValueError):
            billkit.pair("альфа", [("I", "", "текст")])


class DraftStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bills = drafts.specs()

    def test_eleven_separate_docs_and_explanations(self):
        self.assertEqual([b["num"] for _, b in self.bills], list(range(302, 313)))
        directories = {p.name for p in (ROOT / "Законопроекты").glob("Законопроекты 3* - *")
                       if re.match(r"Законопроекты (?:30[2-9]|31[0-2]) - ", p.name)}
        self.assertEqual(directories, {folder for folder, _ in self.bills})
        for folder, bill in self.bills:
            path = ROOT / "Законопроекты" / folder / bill["file"]
            with self.subTest(number=bill["num"]):
                self.assertTrue(path.is_file())
                self.assertTrue((path.parent / "ПОЯСНЕНИЕ К ПАПКЕ.md").is_file())
                self.assertEqual(len(list(path.parent.glob("*.docx"))), 1)
                self.assertTrue(path.name.startswith(f"ACT.{bill['num']}."))
                self.assertNotRegex(path.name, r"[()]")
                self.assertTrue(zipfile.is_zipfile(path))
                with zipfile.ZipFile(path) as package:
                    # В исходном образце TNR не встроен; чужие встроенные шрифты
                    # не должны копироваться в каждый новый документ.
                    self.assertFalse(any(n.startswith("word/fonts/") for n in package.namelist()))
                    self.assertNotIn("word/_rels/fontTable.xml.rels", package.namelist())
                self.assertEqual(check_docx.check(str(path)), [])
                doc = Document(path)
                self.assertEqual(doc.paragraphs[0].text, f"ACT. {bill['num']}")
                self.assertEqual(doc.paragraphs[3].text, drafts.DATE)
                self.assertEqual([c.text for c in doc.tables[0].rows[0].cells],
                                 ["настоящая редакция", "предложенный вариант"])
                self.assertIn("Attest: Marcus Nomad", doc.sections[0].footer.paragraphs[1].text)
                self.assertEqual([n.text for n in doc.sections[0].footer._element.iter(qn("w:instrText"))], ["PAGE"])

    def test_left_and_right_cells_exactly_match_spec_and_local_sources(self):
        aliases = {
            drafts.PC_TITLE: drafts.PC,
            drafts.AD_TITLE: drafts.AD,
            drafts.APP_TITLE: drafts.APP,
            drafts.EMS_TITLE: drafts.EMS,
            drafts.AK_TITLE: drafts.AK,
            drafts.DK_TITLE: drafts.DK,
        }
        sources = {title: [drafts.clean(t) for t in billkit.load(filename).values()]
                   for title, filename in aliases.items()}
        for folder, bill in self.bills:
            doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
            self.assertEqual(len(doc.tables[0].rows), len(bill["rows"]) + 1)
            for row, (left, right) in zip(doc.tables[0].rows[1:], bill["rows"]):
                with self.subTest(number=bill["num"], locator=plain(left).split("\n")[1]):
                    self.assertEqual(row.cells[0].text, plain(left))
                    self.assertEqual(row.cells[1].text, plain(right))
                    title, locator, body = row.cells[0].text.split("\n", 2)
                    self.assertIn(title, sources)
                    self.assertTrue(locator.startswith("Статья "))
                    if body != "В действующей редакции отсутствует.":
                        self.assertTrue(any(body in full for full in sources[title]),
                                        f"Source excerpt not found: {bill['num']} {locator}")
                    self.assertTrue(row.cells[0].paragraphs[0].runs[0].bold)
                    self.assertTrue(row.cells[1].paragraphs[0].runs[0].bold)
                    def fills(cell):
                        return [shd.get(qn("w:fill")) for shd in cell._tc.iter(qn("w:shd"))]
                    self.assertIn("D9EAD3", fills(row.cells[1]))
                    if "[[R]]" in left:
                        self.assertIn("F4CCCC", fills(row.cells[0]))

    def test_font_and_document_hygiene(self):
        for folder, bill in self.bills:
            doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
            roots = [doc.element.body, doc.styles.element]
            for section in doc.sections:
                roots.extend([section.header._element, section.footer._element,
                              section.first_page_header._element, section.first_page_footer._element,
                              section.even_page_header._element, section.even_page_footer._element])
            for root in roots:
                for fonts in root.iter(qn("w:rFonts")):
                    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                        self.assertEqual(fonts.get(qn(attr)), "Times New Roman", (bill["num"], attr))
                    self.assertFalse(any(key.endswith("Theme") for key in fonts.attrib))
            texts = [p.text for p in doc.paragraphs]
            texts += [cell.text for table in doc.tables for row in table.rows for cell in row.cells]
            text = "\n".join(texts)
            for forbidden in ("—", "–", "[[", "]]", "ПГО", "Discord", "ChatGPT"):
                self.assertNotIn(forbidden, text, bill["num"])
            self.assertNotRegex(text, r"\bID\b")
            self.assertEqual(doc.paragraphs[10].text.count("SECTION. 2."), 1)

    def test_rebuild_reproduces_document_parts_without_touching_deliverables(self):
        with TemporaryDirectory() as temp, patch.object(drafts, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                drafts.main()
            for folder, bill in self.bills:
                original = ROOT / "Законопроекты" / folder / bill["file"]
                rebuilt = Path(temp) / folder / bill["file"]
                with self.subTest(number=bill["num"]), zipfile.ZipFile(original) as a, zipfile.ZipFile(rebuilt) as b:
                    self.assertEqual(set(a.namelist()), set(b.namelist()))
                    for name in a.namelist():
                        self.assertEqual(a.read(name), b.read(name), name)

    def test_targeted_rebuild_writes_only_selected_bill(self):
        with TemporaryDirectory() as temp, patch.object(drafts, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                drafts.main(only=302)
            folder, bill = self.bills[0]
            rebuilt = Path(temp) / folder / bill["file"]
            self.assertEqual(list(Path(temp).rglob("*.docx")), [rebuilt])
            original = ROOT / "Законопроекты" / folder / bill["file"]
            with zipfile.ZipFile(original) as a, zipfile.ZipFile(rebuilt) as b:
                self.assertEqual(set(a.namelist()), set(b.namelist()))
                for name in a.namelist():
                    self.assertEqual(a.read(name), b.read(name), name)
            with self.assertRaises(ValueError):
                drafts.main(only=999)

    def test_short_new_norms_keep_heading_and_text_together(self):
        for folder, bill in self.bills:
            doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
            for row, (left, right) in zip(doc.tables[0].rows[1:], bill["rows"]):
                if left.endswith("В действующей редакции отсутствует.") and len(right) < 1200:
                    with self.subTest(number=bill["num"], locator=row.cells[1].paragraphs[1].text):
                        self.assertIsNotNone(row._tr.trPr.find(qn("w:cantSplit")))
                for cell in row.cells:
                    self.assertTrue(all(p.paragraph_format.widow_control for p in cell.paragraphs))

    def test_selected_short_comparisons_do_not_orphan_headings(self):
        folder, bill = self.bills[0]
        doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
        selected = set(bill["keep_rows_together"])
        self.assertEqual(selected, {"Статья 17, часть 4.1, примечание 1",
                                    "Статья 17, часть 5, примечание о назначении звонка"})
        found = set()
        for row, (left, right) in zip(doc.tables[0].rows[1:], bill["rows"]):
            locator = plain(left).split("\n")[1]
            tr_properties = row._tr.trPr
            keep = tr_properties is not None and tr_properties.find(qn("w:cantSplit")) is not None
            if locator in selected:
                found.add(locator)
                self.assertLess(max(len(left), len(right)), 1200)
                self.assertTrue(keep, locator)
            elif not left.endswith("В действующей редакции отсутствует."):
                self.assertFalse(keep, locator)
        self.assertEqual(found, selected)

    def test_bold_named_act_inside_replacement(self):
        folder, bill = self.bills[0]
        doc = Document(ROOT / "Законопроекты" / folder / bill["file"])
        matches = [run for row in doc.tables[0].rows[1:] for cell in row.cells
                   for para in cell.paragraphs for run in para.runs
                   if "Процессуального кодекса штата Сан-Андреас" in run.text]
        self.assertGreaterEqual(len(matches), 2)
        self.assertTrue(all(run.bold for run in matches))
        other_act = [run for row in doc.tables[0].rows[1:] for cell in row.cells
                     for para in cell.paragraphs for run in para.runs
                     if "Закона «Об адвокатской деятельности и адвокатуре" in run.text]
        # Вызов госадвоката по договору и порядок прохода в КПЗ FIB.
        self.assertEqual(len(other_act), 2)
        self.assertTrue(all(run.bold for run in other_act))


class DraftSubstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pc = right_rows(302)

    def test_miranda_and_right_to_call_are_one_alternative(self):
        miranda = find_row(self.pc, "Статья 17, часть 3, правило Миранды")
        self.assertEqual(miranda.split("\n", 2)[2],
            'ч. 3.\nПравило Миранды: "Вы имеете право хранить молчание. '
            'Всё, что вы скажете, может и будет использовано против Вас в суде. '
            'Вы имеете право на защиту государственным адвокатом либо на один телефонный звонок '
            'для вызова частного адвоката. Если вам необходим адвокат, он будет для Вас запрошен. '
            'Вы понимаете свои права?"')
        elements = find_row(self.pc, "Статья 17, часть 3, примечание об обязательных элементах")
        self.assertEqual(elements.splitlines()[-4:], [
            "- Право на хранение молчания;",
            "- Предупреждение о том, что всё сказанное может и будет использовано против задержанного в суде;",
            "- Право на защиту государственным адвокатом либо на один телефонный звонок для вызова частного адвоката;",
            "- Уведомление о том, что при необходимости адвокат будет запрошен.",
        ])
        right = find_row(self.pc, "Статья 22, часть 1, пункт «а»")
        self.assertIn("право на защиту государственным адвокатом либо на один телефонный звонок для вызова частного адвоката", right)
        self.assertIn("вместо вызова государственного адвоката по горячей линии", right)
        self.assertIn("телефонный звонок для вызова государственного адвоката по договору", right)
        self.assertIn("в том числе дополнительный", right)
        self.assertIn("до начала процесса ареста в присутствии сотрудника", right)
        self.assertIn("в случаях и порядке, предусмотренных статьей 17 настоящего Кодекса", right)
        self.assertIn("Длительность звонка не должна превышать 3-х минут", right)
        self.assertNotIn("сотрудник обязан предоставить телефонный звонок задержанному по его запросу", right)

    def test_state_phone_contract_call_and_no_extra_after_acceptance(self):
        state = find_row(self.pc, "Статья 17, часть 4")
        private = find_row(self.pc, "Статья 17, часть 4.1")
        phone = find_row(self.pc, "Статья 17, часть 5")
        self.assertIn("В указанном случае по выбору задержанного вместо вызова по горячей линии", state)
        self.assertIn("по ранее заключенному договору либо для заключения устного договора", state)
        self.assertIn("части 1 статьи 8 Закона «Об адвокатской деятельности", state)
        self.assertIn("части 5 настоящей статьи", state)
        for text in (state, private):
            self.assertIn("ранее не был своевременно принят вызов адвоката", text)
            self.assertIn("право на адвоката не признано реализованным", text)
        self.assertIn("один телефонный звонок для вызова частного адвоката либо государственного адвоката по договору", phone)
        self.assertIn("Длительность каждого звонка не должна превышать 3 минут", phone)
        self.assertIn("При своевременном принятии вызова, а также после признания права на адвоката реализованным", phone)
        self.assertIn("не обязан предоставлять телефон или телефонный звонок для вызова другого адвоката", phone)
        self.assertIn("в том числе если телефон ранее не предоставлялся", phone)

    def test_state_arrival_and_alternative_path(self):
        state = find_row(self.pc, "Статья 17, часть 4")
        alternative = find_row(self.pc, "Статья 17, часть 4.1, примечание 2")
        private = find_row(self.pc, "Статья 17, часть 4.1")
        private_time = find_row(self.pc, "Статья 17, часть 4.1, примечание 1")
        self.assertIn("по горячей линии Правительства либо по телефону задержанного", state)
        self.assertIn("10 минут с момента принятия вызова", state)
        self.assertIn("не прибыл в течение указанного срока, процедура задержания продолжается и право на адвоката считается реализованным", state)
        self.assertIn("после оказания задержанному юридической помощи", alternative)
        self.assertIn("При прямом добровольном отказе задержанного от юридической помощи прибывшего адвоката", alternative)
        self.assertIn("вызов адвоката другого вида", alternative)
        self.assertIn("по его желанию обеспечить этот вызов", alternative)
        self.assertIn("не является окончательным", alternative)
        self.assertIn("молчание отказом не является", alternative)
        self.assertIn("молчание не является отказом от права на адвоката", alternative)
        self.assertIn("Ожидание выбора само по себе не приостанавливает течение срока задержания", alternative)
        self.assertIn("Принятие первоначального вызова после истечения срока ожидания ответа не отменяет обязанности предложить альтернативу", alternative)
        self.assertIn("Просмотр телефона без направления вызова не является вызовом адвоката или телефонным звонком", alternative)
        self.assertIn("дополнительный вызов адвоката другого вида не обязателен", alternative)
        self.assertIn("само по себе не означает фактического оказания юридической помощи", alternative)
        self.assertIn("прибывшего до окончания задержания", alternative)
        self.assertIn("ранее не был своевременно принят вызов", private)
        self.assertIn("с момента направления заявки через приложение", private_time)
        self.assertIn("С момента направления каждого вызова", alternative)
        self.assertIn("не более чем на 3 минуты по соответствующему вызову", alternative)
        self.assertIn("заморозка по этому основанию прекращается с момента отказа", alternative)
        self.assertIn("Пересекающиеся периоды заморозки процессуального часа учитываются один раз", alternative)
        self.assertIn("конфиденциальную встречу по требованию задержанного", alternative)

    def test_only_unaccepted_first_phone_call_triggers_alternative_phone_call(self):
        alternative = find_row(self.pc, "Статья 17, часть 4.1, примечание 2")
        phone = find_row(self.pc, "Статья 17, часть 5")
        fallback = next(line for line in alternative.splitlines() if line.startswith("Если в течение 3 минут"))
        # Правило одинаково для первого вызова любого вида: частный -> государственный
        # (горячая линия или телефон по договору) и государственный -> частный.
        self.assertIn("вызов не принят адвокатом либо до истечения этого срока получен окончательный отказ", fallback)
        self.assertIn("обязан предложить задержанному вызов адвоката другого вида", fallback)
        self.assertIn("по его желанию обеспечить этот вызов в порядке частей 4 и 4.1", fallback)
        self.assertIn("первоначальный вызов, направленный телефонным звонком задержанного, не был принят в указанном порядке", fallback)
        self.assertIn("по желанию задержанного предоставляется один дополнительный телефонный звонок", fallback)
        self.assertIn("Дополнительный телефонный звонок для вызова адвоката другого вида предоставляется в случае, предусмотренном примечанием 2", phone)
        self.assertIn("Если первоначальный или альтернативный вызов своевременно принят, дополнительный вызов адвоката другого вида не обязателен", alternative)

    def test_attorney_law_and_informing_are_not_contradictory(self):
        note = find_row(self.pc, "Статья 8, часть 1, пояснение 4")
        source = drafts.excerpt(billkit.load(drafts.AD)[17],
                                "Пояснение 4: В случае если с доверителем/подзащитным", "\nч. 2.")
        self.assertIn(source, note)  # сохраняются письменный договор и устный договор по телефону
        self.assertIn("Телефон для вызова государственного адвоката предоставляется в порядке статьи 17 Процессуального кодекса", note)
        self.assertIn("При ранее заключенном письменном договоре государственный адвокат вправе прибыть также по вызову через горячую линию", note)
        self.assertIn("не устанавливает обязанности дополнительно предоставлять телефон после своевременного принятия вызова или реализации права", note)
        purpose = find_row(self.pc, "Статья 17, часть 5, примечание о назначении звонка")
        self.assertIn("для связи с частным или государственным адвокатом в целях его вызова", purpose)
        self.assertIn("по вопросу заключения договора на оказание юридических услуг в установленном законом порядке", purpose)
        self.assertIn("не обладающими статусом частного или государственного адвоката", purpose)
        self.assertIn("Использование указанного телефонного звонка для иных целей", purpose)
        self.assertNotIn("с которым задержанный заключил действительный устный договор", purpose)
        self.assertNotIn("не обладающими статусом частного адвоката", purpose)
        info = find_row(self.pc, "Статья 23, часть 1, пункты «б» и «в»")
        self.assertIn("известные фактические обстоятельства каждого вменяемого правонарушения", info)
        self.assertIn("в) По требованию предоставить доказательства совершенного правонарушения, в том числе адвокату", info)
        self.assertIn("статьей 19 настоящего Кодекса, руководству", info)

    def test_fib_access_clarification_preserves_current_note_and_legal_agreement(self):
        appendix = billkit.load(drafts.APP)[7]
        self.assertIn("Примечание 2: Государственные и частные адвокаты", appendix)
        self.assertNotIn("Примечание 2.1:", appendix)
        # Проект не переписывает примечание 2, а дополняет его разъяснением.
        self.assertFalse(any(row.split("\n")[1] == "Статья 4, примечание 2" for row in self.pc))
        added = find_row(self.pc, "Статья 4, примечание 2.1")
        self.assertIn("принятый государственным адвокатом вызов по горячей линии Правительства", added)
        self.assertIn("является вызовом через телефон", added)
        self.assertIn("Устный договор с государственным адвокатом", added)
        self.assertIn("при этом вызове либо по телефону задержанного", added)
        self.assertIn("в порядке части 1 статьи 8", added)
        self.assertIn("до прохода адвоката в КПЗ, считается ранее заключенным договором", added)
        self.assertIn("Иные требования доступа и нахождения на территории сохраняются", added)
        self.assertNotIn("пункта «ж» части 2 статьи 4", added)  # это прежний проект, не закон

    def test_compromises_keep_safety_and_accountability(self):
        c303 = "\n".join(right_rows(303))
        c304 = "\n".join(right_rows(304))
        c305 = "\n".join(right_rows(305))
        c306 = "\n".join(right_rows(306))
        c307 = "\n".join(right_rows(307))
        self.assertIn("если", c303.lower())
        self.assertIn("последующему привлечению к ответственности", c303)
        self.assertIn("пресечению непосредственной угрозы", c303)
        self.assertIn("пунктах «а», «б», «г» и «д»", c304)
        self.assertIn("не препятствует проезду других экстренных служб", c304)
        self.assertIn("впервые совершенное по неосторожности", c305)
        self.assertIn("состоянии опьянения", c305)
        self.assertIn("условия части 2 статьи 3.4 настоящего Кодекса", c305)
        warning = billkit.load(drafts.AK)[21]
        self.assertIn("отсутствии причинения вреда", warning)
        self.assertIn("угрозы причинения вреда жизни и здоровью людей", warning)
        self.assertNotIn("не подлежит ответственности", c306)
        self.assertIn("непосредственно связанного с необходимостью", c306)
        self.assertIn("не превышает 5 минут", c307)
        self.assertIn("Отсутствие ответа не препятствует рассмотрению дела", c307)
        self.assertIn("Врачебная тайна", c307)
        self.assertIn("Статья 32, часть 7", c303)
        self.assertIn("Статья 33, часть 7", c307)
        self.assertNotIn("Статья 32, часть 7", c307)

    def test_five_other_projects_are_distinct_and_bounded(self):
        texts = {n: "\n".join(right_rows(n)) for n in range(308, 313)}
        self.assertIn("месте безопасного ожидания", texts[308])
        self.assertIn("по доступной связи", texts[309])
        self.assertIn("при наличии возможности передает вызов", texts[309])
        self.assertIn("о сохраняющейся опасности", texts[310])
        self.assertIn("уведомляет EMS об отмене вызова", texts[311])
        self.assertIn("не ограничивает обращение за медицинской помощью", texts[311])
        self.assertIn("приостанавливает освидетельствование", texts[312])
        self.assertIn("части 3 статьи 12", texts[312])
        self.assertIn("врачебную тайну", texts[312])


if __name__ == "__main__":
    unittest.main()
