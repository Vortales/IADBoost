# -*- coding: utf-8 -*-
"""Краткий ACT. 303, источники, режим территорий и совместимость с 301-302."""
import hashlib
import json
import re
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
import build_act303 as draft
import build_acts301_302 as prior
import check_docx


def text(document):
    return "\n".join([p.text for p in document.paragraphs] +
                     [c.text for row in document.tables[0].rows for c in row.cells])


def replace_once(content, before, after):
    if content.count(before) != 1:
        raise AssertionError(f"Фрагмент не найден или не уникален: {before[:110]!r}")
    return content.replace(before, after, 1)


class Act303Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bill, cls.patches, cls.documents = draft.specs()
        cls.final = draft.apply_patches(cls.patches, cls.documents)
        cls.by_locator = {p.locator: p for p in cls.patches}
        cls.path = draft.OUT / cls.bill["file"]
        cls.doc = Document(cls.path)
        cls.notes = (draft.OUT / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")

    def test_source_comparisons_marking_and_compactness(self):
        self.assertEqual(len(self.patches), 33)  # согласован доступ к КПП-2
        self.assertEqual(len(self.bill["rows"]), len(self.patches))
        self.assertEqual(len(self.doc.tables[0].rows), len(self.patches) + 1)
        for row, (left, right), item in zip(self.doc.tables[0].rows[1:], self.bill["rows"], self.patches):
            with self.subTest(locator=item.locator):
                self.assertEqual(row.cells[0].text, draft.plain(left))
                self.assertEqual(row.cells[1].text, draft.plain(right))
                _, locator, body = row.cells[0].text.split("\n", 2)
                self.assertEqual(locator, item.locator)
                self.assertTrue(all(cell.paragraphs[0].runs[0].bold for cell in row.cells))
                fills = lambda cell: [el.get(qn("w:fill")) for el in cell._tc.iter(qn("w:shd"))]
                self.assertIn("D9EAD3", fills(row.cells[1]))
                if item.old:
                    self.assertEqual(body, item.old)
                    self.assertEqual(draft.clean(self.documents[item.source][item.section]).count(body), 1)
                    self.assertIn("F4CCCC", fills(row.cells[0]))
                    if item.new:
                        self.assertEqual(row.cells[1].text.split("\n", 2)[2], item.new)
                    else:
                        self.assertIn("Исключить", row.cells[1].text)
                else:
                    self.assertEqual(body, "В действующей редакции отсутствует.")
                    self.assertEqual(row.cells[1].text.split("\n", 2)[2], item.new)
                if item.locator in self.bill["keep_rows_together"]:
                    self.assertIsNotNone(row._tr.trPr.find(qn("w:cantSplit")))

    def test_layout_fonts_metadata_and_no_private_references(self):
        self.assertEqual(check_docx.check(str(self.path)), [])
        self.assertEqual(self.doc.paragraphs[0].text, "ACT. 303")
        self.assertEqual(self.doc.paragraphs[3].text, "")
        self.assertEqual(self.doc.core_properties.author, "")
        self.assertIsNone(self.doc.core_properties.created)
        self.assertIsNone(self.doc.core_properties.modified)
        table, section = self.doc.tables[0], self.doc.sections[0]
        half = (section.page_width.twips - 864) // 2
        self.assertEqual([col.width.twips for col in table.columns], [half, half])
        self.assertEqual(table._tbl.getnext().tag, qn("w:sectPr"))
        self.assertIn("Attest: __________________", section.footer.paragraphs[1].text)
        roots = [self.doc.element.body, self.doc.styles.element, section.header._element, section.footer._element]
        for root in roots:
            for font in root.iter(qn("w:rFonts")):
                for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                    self.assertEqual(font.get(qn(attr)), "Times New Roman")
        for forbidden in ("Правила проекта", "правила проекта", "правила сервера", "ПГО", "ChatGPT", "—", "–", "[["):
            self.assertNotIn(forbidden, text(self.doc))
            self.assertNotIn(forbidden, self.notes)
        self.assertNotRegex(text(self.doc), r"\bID\b")
        for row in self.doc.tables[0].rows[1:]:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if any(name in run.text for name in ("Процессуального кодекса штата", "Закона «Об Экстренной",
                                "Законом «Об адвокатской", "Приложением № 1 к Уголовному кодексу штата San-Andreas")):
                            self.assertTrue(run.bold, run.text)
        with zipfile.ZipFile(self.path) as z:
            self.assertFalse(any(name.startswith("word/fonts/") for name in z.namelist()))

    def test_date_correction_and_no_constitutional_amendment_inside_303(self):
        self.assertIn("ошибоч", self.notes)
        self.assertIn("подтверждённой даты проверки нет", self.notes)
        self.assertIn("11.11.2026", self.notes)
        self.assertIn("15.11.2026", self.notes)
        self.assertNotIn("позднее даты проверки", self.notes)
        self.assertNotIn(draft.COURT if hasattr(draft, "COURT") else "Конституционный закон «О судебной системе", text(self.doc))
        self.assertIn("Раздельный проект об обыске в суде удалён", self.notes)
        self.assertFalse((ROOT / "Законопроекты/Законопроекты 316 - обыск в суде").exists())
        self.assertTrue(all("Конституцион" not in p.source for p in self.patches))

    def test_closed_territory_definition_is_a_proposal_not_a_source_quote(self):
        definition = ("Закрытая территория - часть объекта, доступ на которую ограничен законом. "
                      "Прилегающая территория и общедоступный холл не являются закрытыми только в силу их расположения.")
        self.assertIn(definition, self.by_locator["Статья 1, основные понятия"].new)
        self.assertNotIn("Закрытая территория", draft.clean(self.documents[draft.APP][3]))
        self.assertIn("Прилегающий объект", draft.clean(self.documents[draft.APP][3]))
        self.assertIn("Белым цветом выделяются прилегающие территории", draft.clean(self.documents[draft.APP][9]))
        sources = list((ROOT / "Законодательная база").glob("*.json"))
        self.assertEqual(len(sources), 52)
        for path in sources:
            data = json.loads(path.read_text(encoding="utf-8"))
            for section in data["sections"]:
                self.assertNotIn(definition, draft.clean(section.get("text") or ""), path.name)
        self.assertIn("авторское предложение проекта, а не цитата действующего закона", self.notes)
        self.assertIn("могут не охватывать объект целиком", self.notes)

    def test_user_archive_preserved_and_source_spelling_not_falsified(self):
        archive = ROOT / "Законопроекты после правок.7z"
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),
                         "6dbb2c159ae8a624840befc65360afd51e7c5b7a6c8abcf9fedcf5901e580f58")
        visual = self.by_locator["Статья 6, визуализация и прилегающие территории"]
        self.assertIn("Желтымцветом", visual.old)
        self.assertIn("Краснымцветом", visual.old)
        self.assertIn("Желтым цветом", visual.new)
        self.assertIn("Красным цветом", visual.new)
        self.assertIn("колонке исходной редакции", self.notes)

    def test_entire_appendix_review_and_fort_exception(self):
        self.assertEqual({p.section for p in self.patches if p.source == draft.APP}, {1, 3, 4, 5, 7, 8, 9, 10, 11})
        preamble = self.by_locator["Преамбула"].new
        self.assertIn("при производстве по делу", preamble.lower())
        self.assertIn("указанный Кодекс в установленном им порядке", preamble)
        self.assertNotIn("его статьи 2", preamble)
        app2 = self.final[draft.APP, 4]
        self.assertIn("Перечень законных целей визита (список открытый)", app2)
        self.assertIn("с законной целью посещения", app2)
        self.assertIn("находящиеся в оперативном ведении или на балансе", app2)
        note = self.by_locator["Статья 4, пункт «а», примечание 1"].new
        for phrase in ("до линий КПП", "свободна для посещения", "независимо от ее обозначения",
                       "Цель визита, пропуск и сопровождение не требуются", "в обход КПП",
                       "угрозу обществу", "размахивания кулаками, ногами", "основание и путь выхода",
                       "достаточное время", "При невыполнении требования", "горячей линии «911»",
                       "Вызов не исключает иных мер при наличии самостоятельных законных оснований"):
            self.assertIn(phrase, note)
        self.assertNotIn("2 км", note)
        goal = self.by_locator["Статья 2, цели посещения SANG"].new
        for phrase in ("трудоустройство, запись на курс молодого бойца",
                       "только на территории Форта за КПП-2 до линии развилки",
                       "только в сопровождении уполномоченного лица Национальной гвардии",
                       "Свободное нахождение на прилегающей территории Форта до КПП сохраняется"):
            self.assertIn(phrase, goal)
        self.assertEqual(self.by_locator["Статья 2, цели посещения SANG"].old,
                         "- SANG- трудоустройство, запись на курс молодого бойца.")
        access = self.by_locator["Статья 4, пункт «а», доступ для трудоустройства"].new
        self.assertIn("сопровождении генералитета", access)
        self.assertIn("при наличии пропуска", access)
        self.assertIn("лица, прибывшие для трудоустройства или записи на курс молодого бойца", access)
        self.assertIn("в порядке статьи 2 настоящего Приложения", access)
        visual = self.by_locator["Статья 6, визуализация и прилегающие территории"].new
        for phrase in ("общедоступные холлы", "Схемы обозначают границы", "применяется текст",
                       "Форта до КПП цель не требуется", "Перечень целей в статье 2 открыт"):
            self.assertIn(phrase, visual)
        self.assertIn("само по себе не является основанием", self.by_locator["Статья 7, права сотрудников"].new)
        self.assertIn("открытой для посещения", self.final[draft.APP, 5])
        self.assertNotIn("Аэропорт на территории острова является открытой", self.final[draft.APP, 7])

    def test_access_subjects_duplicate_notes_and_court_guarantees(self):
        app = self.final[draft.APP, 7]
        for label in ("Примечание 2:", "Примечание 3:", "Примечание 4:", "Примечание 5:",
                      "Примечание 6.1:", "Примечание 6.2:", "Примечание 7:", "Примечание 8:", "Примечание 9:"):
            self.assertEqual(app.count(label), 1, label)
        self.assertNotIn("Примечание 6:", app)
        self.assertIn("по примечанию 2 настоящей статьи", self.by_locator["Статья 4, примечание 4"].new)
        self.assertIn("по примечанию 3 настоящей статьи", self.by_locator["Статья 4, примечание 5"].new)
        note = self.by_locator["Статья 4, примечание 2"].new
        for phrase in ("Государственные и частные адвокаты", "5 минут", "фактической возможности выхода",
                       "необходимого сопровождения", "не зависящих от лица"):
            self.assertIn(phrase, note)
        note9 = self.by_locator["Статья 4, примечание 9"].new
        self.assertIn("в порядке Процессуального кодекса штата Сан-Андреас", note9)
        self.assertNotIn("статьи 18", note9)
        self.assertIn("Иные законные основания доступа сохраняются", note9)
        self.assertIn("врачебной тайны", self.by_locator["Статья 4, пункт «е», доступ адвокатов"].new)
        self.assertIn("не входят в состав КПЗ", self.by_locator["Статья 4, примечание 8 и исключение"].new)
        article5 = self.final[draft.APP, 8]
        self.assertIn("для которого суд не является местом работы", article5)
        self.assertIn("с учетом части 1.3", article5)
        self.assertIn("учетом исключений, предусмотренных Процессуальным кодексом", article5)
        self.assertNotIn("статьей 29 Процессуального кодекса", article5)
        self.assertIn("посетителей, желающих посетить открытые судебные заседания", article5)

    def test_sang_force_search_transfers_and_pass_priority(self):
        # Единственная редакция этой части теперь находится в ACT. 300 SANG.
        self.assertNotIn("Статья 2, часть 7", self.by_locator)
        self.assertIn("изменяется только в ACT. 300", self.notes)
        guard7 = self.final[draft.SANG, 13]
        self.assertNotIn("право останавливать и досматривать лиц", guard7)
        self.assertIn("Остановка сама по себе не является основанием", guard7)
        self.assertIn("Исключение: Государственные служащие при исполнении", guard7)
        self.assertIn("фиксацию, прямо предусмотренную или разрешенную законом", self.by_locator["Статья 14.4, примечание"].new)
        p = self.by_locator["Статья 8, часть 1"].new
        self.assertIn("указанные для этого объекта лица", p)
        self.assertIn("На иные закрытые территории", p)
        self.assertIn("Иные законные основания доступа сохраняются", p)

    def test_303_and_302_apply_in_either_order_without_overwriting(self):
        prior_bill = next(b for _, b in prior.specs() if b["num"] == 302)
        rows = [(draft.plain(l).split("\n", 2)[2], draft.plain(r).split("\n", 2)[2])
                for l, r in prior_bill["rows"] if draft.plain(l).startswith(draft.APP_TITLE + "\n")]
        self.assertEqual(len(rows), 2)
        source = draft.clean(self.documents[draft.APP][7])
        app_patches = [p for p in self.patches if (p.source, p.section) == (draft.APP, 7)]
        def apply303(value):
            for p in app_patches:
                value = replace_once(value, p.old, p.new) if p.old else value.rstrip() + "\n" + p.new
            return value
        def apply302(value):
            for left, right in rows:
                value = replace_once(value, left, right)
            return value
        combined = apply303(apply302(source))
        self.assertEqual(combined, apply302(apply303(source)))
        self.assertEqual(combined.count("одно лицо, вызванное как начальство задержанного"), 2)
        self.assertIn("а также служащие органов правопорядка и военных органов в сопровождении руководства ФРБ;", combined)
        self.assertIn("Примечание 9:", combined)
        app_text = "\n".join(v for (source_name, _), v in self.final.items() if source_name == draft.APP)
        self.assertNotIn("Статья 4.1", app_text)  # ACT. 301 добавляет ее самостоятельно

    def test_rebuild_is_isolated_and_reproducible(self):
        with TemporaryDirectory() as temp, patch.object(draft, "OUT", Path(temp)):
            with redirect_stdout(StringIO()):
                draft.main()
            with zipfile.ZipFile(self.path) as original, zipfile.ZipFile(Path(temp) / self.bill["file"]) as rebuilt:
                self.assertEqual(set(original.namelist()), set(rebuilt.namelist()))
                for name in original.namelist():
                    self.assertEqual(original.read(name), rebuilt.read(name), name)


if __name__ == "__main__":
    unittest.main()
