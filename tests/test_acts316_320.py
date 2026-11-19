# -*- coding: utf-8 -*-
"""Новые инициативы: точность источников, процедуры и совместное применение."""
import hashlib
import itertools
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
import billkit
import build_act315 as territory
import build_acts313_314 as releases
import build_acts316_320 as drafts
import check_docx
import legal_sources as sources


def full_text(doc):
    return "\n".join([p.text for p in doc.paragraphs] +
                     [c.text for row in doc.tables[0].rows for c in row.cells])


def replace_once(content, before, after):
    if content.count(before) != 1:
        raise AssertionError(f"Несовместимый фрагмент: {before[:100]!r}")
    return content.replace(before, after, 1)


def insert_before_or_append(content, new, next_part):
    if next_part in content:
        index = content.index(next_part)
        return content[:index].rstrip() + "\n" + new + content[index:]
    return content.rstrip() + "\n" + new


class NewDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bills, cls.patches, cls.documents = drafts.specs()
        cls.by_num = {b["num"]: (folder, b) for folder, b in cls.bills}
        cls.by_locator = {(p.number, p.locator): p for p in cls.patches}

    def test_archived_release_folders_are_not_active_or_rebuilt(self):
        base = ROOT / "Законопроекты"
        archive = ROOT / "Архив/Законопроекты 302-312 (сняты с рассмотрения)"
        expected = list(range(302, 313))
        active = sorted(int(m.group(1)) for x in base.iterdir()
                        if x.is_dir() and (m := re.match(r"Законопроекты (30[2-9]|31[0-2]) - ", x.name)))
        archived = sorted(int(m.group(1)) for x in archive.iterdir()
                          if x.is_dir() and (m := re.match(r"Законопроекты (30[2-9]|31[0-2]) - ", x.name)))
        self.assertEqual(active, [])
        self.assertEqual(archived, expected)
        self.assertFalse((ROOT / "tools/build_acts302_312.py").exists())
        self.assertFalse((ROOT / "tests/test_acts302_312.py").exists())

    def test_separate_docs_sources_colors_fonts_and_hygiene(self):
        self.assertEqual(set(self.by_num), set(range(316, 321)))
        self.assertEqual(len(self.patches), 8)
        for num, (folder, bill) in self.by_num.items():
            with self.subTest(number=num):
                directory = drafts.OUT / folder
                path = directory / bill["file"]
                self.assertEqual(list(directory.glob("*.docx")), [path])
                self.assertTrue(path.name.startswith(f"ACT.{num}."))
                self.assertTrue((directory / "ПОЯСНЕНИЕ К ПАПКЕ.md").is_file())
                doc = Document(path)
                self.assertEqual(doc.paragraphs[0].text, f"ACT. {num}")
                self.assertEqual(doc.paragraphs[3].text, "")
                self.assertEqual(doc.core_properties.author, "")
                self.assertIsNone(doc.core_properties.created)
                self.assertIsNone(doc.core_properties.modified)
                self.assertEqual(check_docx.check(str(path)), [])
                self.assertIn("Attest: __________________", doc.sections[0].footer.paragraphs[1].text)
                self.assertEqual([c.text for c in doc.tables[0].rows[0].cells],
                                 ["настоящая редакция", "предложенный вариант"])
                selected = [p for p in self.patches if p.number == num]
                self.assertEqual(len(selected), len(bill["rows"]))
                for row, (left, right), item in zip(doc.tables[0].rows[1:], bill["rows"], selected):
                    self.assertEqual(row.cells[0].text, drafts.plain(left))
                    self.assertEqual(row.cells[1].text, drafts.plain(right))
                    self.assertTrue(all(c.paragraphs[0].runs[0].bold for c in row.cells))
                    fills = lambda c: [x.get(qn("w:fill")) for x in c._tc.iter(qn("w:shd"))]
                    self.assertIn("D9EAD3", fills(row.cells[1]))
                    if item.old:
                        self.assertEqual(row.cells[0].text.split("\n", 2)[2], item.old)
                        self.assertEqual(sources.clean(self.documents[item.source][item.section]).count(item.old), 1)
                        self.assertIn("F4CCCC", fills(row.cells[0]))
                    else:
                        self.assertEqual(row.cells[0].text.split("\n", 2)[2], "В действующей редакции отсутствует.")
                        self.assertNotIn(item.marker, sources.clean(self.documents[item.source][item.section]))
                    self.assertEqual(row.cells[1].text.split("\n", 2)[2], item.new)
                    if item.locator in bill["keep_rows_together"]:
                        self.assertIsNotNone(row._tr.trPr.find(qn("w:cantSplit")))
                section = doc.sections[0]
                roots = [doc.element.body, doc.styles.element, section.header._element, section.footer._element]
                for root in roots:
                    for fonts in root.iter(qn("w:rFonts")):
                        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                            self.assertEqual(fonts.get(qn(attr)), "Times New Roman")
                notes = (directory / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")
                for bad in ("Правила проекта", "правила проекта", "правила сервера", "ПГО", "ChatGPT", "—", "–", "[["):
                    self.assertNotIn(bad, full_text(doc))
                    self.assertNotIn(bad, notes)
                self.assertNotRegex(full_text(doc), r"\bID\b")
                with zipfile.ZipFile(path) as z:
                    self.assertFalse(any(x.startswith("word/fonts/") for x in z.namelist()))

    def test_only_316_changes_constitutional_law(self):
        constitutional = [p for p in self.patches if p.source == sources.COURT]
        self.assertEqual([(p.number, p.locator) for p in constitutional], [(316, "Статья 42, часть 8")])
        court = constitutional[0].new
        self.assertIn("Судебный пристав вправе проводить личный обыск", court)
        self.assertIn("оснований и в порядке Процессуального кодекса штата Сан-Андреас", court)
        self.assertNotIn("статьи 29", court)
        self.assertIn("оружия, пронос которого запрещен частью 7", court)
        self.assertNotIn("независимо от должности", court)
        t_bill, t_patches, _ = territory.specs()
        self.assertTrue(all(p.source != sources.COURT for p in t_patches))
        self.assertTrue(all(p.source == sources.COURT for p in self.patches if p.number == 316))
        self.assertNotIn("ACT. 315", drafts.plain("\n".join(r for _, r in self.by_num[316][1]["rows"])))

    def test_motivated_call_respects_release_and_article19(self):
        clause = self.by_locator[317, "Статья 23, часть 2"].new
        for phrase in ("участвующий в задержании адвокат", "конкретное основание освобождения", "части 1 статьи 20",
                       "не согласен", "устному ходатайству", "в КПЗ или допросной вызывает туда прокурора",
                       "уже участвует", "вызван по статье 19", "новых существенных обстоятельствах",
                       "не ответил или не прибыл в течение 10 минут", "только при наличии законных оснований",
                       "Порядок и сроки статьи 19 сохраняются", "освобождается незамедлительно",
                       "не дожидаясь прокурора", "Прокурор незамедлительно оценивает доводы", "в пределах полномочий"):
            self.assertIn(phrase, clause)
        self.assertIn("Повторный вызов по тем же обстоятельствам не производится", clause)
        clock = self.by_locator[317, "Статья 20, часть 2, пункт «ж»"].new
        self.assertIn("фактическое время ожидания", clock)
        self.assertIn("не более 10 минут с момента вызова", clock)
        self.assertIn("не суммируются", clock)
        self.assertIn("по статье 19", clock)
        conclusion = self.by_locator[317, "Статья 5.1, часть 2"].new
        self.assertIn("не обязательно для сотрудника", conclusion)
        self.assertIn("не является решением об освобождении", conclusion)
        self.assertIn("адвокат вправе заявить ходатайство", conclusion)
        old = sources.clean(self.documents[sources.AD][13])
        self.assertIn("рекомендательного характера", old)
        self.assertIn("не является отказом от защиты", old)

    def test_defence_materials_cover_all_detentions_with_bounded_freeze(self):
        recording = self.by_locator[318, "Статья 23, часть 1, пункт «г» и исключение"].new
        for phrase in ("задержанного или участвующего в задержании адвоката", "приобщить к материалам дела",
                       "доказательства и иные материалы", "аудио- и видеозаписи изучаются", "независимо от основания задержания",
                       "представившие записи", "до 10 минут за задержание", "оцениваются по статьям 11-14", "само по себе не отменяет ордер",
                       "до 1 часа", "ожидание само по себе не приостанавливает", "представить ее позднее"):
            self.assertIn(phrase, recording)
        old = self.by_locator[318, "Статья 23, часть 1, пункт «г» и исключение"].old
        self.assertIn("автоматически созданной записи в боло-розыске", old)
        clock = self.by_locator[318, "Статья 20, часть 2, пункт «е»"].new
        for phrase in ("на фактическое время изучения", "не более 10 минут в совокупности за задержание",
                       "не суммируются", "иные самостоятельные основания приостановления сохраняются"):
            self.assertIn(phrase, clock)

    def test_oral_motions_and_factual_questions_do_not_transfer_authority(self):
        petition = self.by_locator[319, "Статья 43, часть 3"].new
        for phrase in ("непосредственно после заявления", "устное ходатайство задержанного или участвующего адвоката",
                       "до решения о наказании", "полном или частичном отказе с указанием причин",
                       "не входит в полномочия сотрудника", "передает ходатайство ему", "в видеозаписи по статье 32",
                       "нарушением процессуального порядка", "не устранено до решения о наказании",
                       "уполномоченный прокурор или суд при рассмотрении жалобы",
                       "признает последующий арест незаконным в пределах своих полномочий"):
            self.assertIn(phrase, petition)
        self.assertNotIn("автоматически признается незаконным", petition)
        facts = self.by_locator[320, "Статья 23, часть 1, пункт «д»"].new
        for phrase in ("известные сотруднику фактические обстоятельства", "время, место и способ фиксации",
                       "последовательность применения силы", "отдававшиеся команды", "При отсутствии сведений сообщается",
                       "ограниченным доступом", "не обязывает разъяснять адвокату", "не отменяет обязанностей по пунктам «б» и «в»",
                       "квалификацию задержанному сохраняется"):
            self.assertIn(phrase, facts)
        self.assertNotIn("обязан установить состав", facts)
        precedent = billkit.load("Судебные Прецеденты и Толкования")[1]
        self.assertIn("не возлагается обязанность разъяснять адвокату юридическую квалификацию", precedent)

    def test_article20_release_and_both_freezes_commute_in_all_orders(self):
        base = sources.clean(self.documents[sources.PC][33]).rstrip()
        first = next(b for _, b in releases.specs() if b["num"] == 313)
        left, right = next((l, r) for l, r in first["rows"] if "Статья 20, часть 3" in l)
        self.assertIn("В действующей редакции отсутствует", left)
        release = drafts.plain(right).split("\n", 2)[2]
        call = self.by_locator[317, "Статья 20, часть 2, пункт «ж»"].new
        video = self.by_locator[318, "Статья 20, часть 2, пункт «е»"]
        def apply(content, op):
            if op == "release":
                return insert_before_or_append(content, release, "\nч. 4.")
            if op == "call":
                return insert_before_or_append(content, call, "\nч. 3.")
            return replace_once(content, video.old, video.new)
        all_versions = []
        for order in itertools.permutations(("release", "call", "video")):
            value = base
            for op in order:
                value = apply(value, op)
            self.assertLess(value.index("е) при изучении"), value.index("ж) при ожидании"))
            self.assertLess(value.index("ж) при ожидании"), value.index("ч. 3. При наличии основания"))
            self.assertEqual(value.count("ч. 3. При наличии основания"), 1)
            all_versions.append(value)
        self.assertEqual(len(set(all_versions)), 1)

    def test_article23_prosecutor_materials_and_questions_commute_in_all_orders(self):
        base = sources.clean(self.documents[sources.PC][36]).rstrip()
        call = self.by_locator[317, "Статья 23, часть 2"].new
        video = self.by_locator[318, "Статья 23, часть 1, пункт «г» и исключение"]
        questions = self.by_locator[320, "Статья 23, часть 1, пункт «д»"].new
        def apply(content, op):
            if op == "call":
                return insert_before_or_append(content, call, "\nч. 3.")
            if op == "questions":
                return insert_before_or_append(content, questions, "\nч. 2.")
            return replace_once(content, video.old, video.new)
        results = []
        for order in itertools.permutations(("call", "video", "questions")):
            value = base
            for op in order:
                value = apply(value, op)
            self.assertLess(value.index("г) По заявлению"), value.index("д) По вопросам"))
            self.assertLess(value.index("д) По вопросам"), value.index("ч. 2. Если участвующий"))
            results.append(value)
        self.assertEqual(len(set(results)), 1)

    def test_only_selected_project_rebuilds_and_output_is_reproducible(self):
        for num, (folder, bill) in self.by_num.items():
            with self.subTest(number=num), TemporaryDirectory() as temp, patch.object(drafts, "OUT", Path(temp)):
                with redirect_stdout(StringIO()):
                    drafts.main(only=num)
                generated = list(Path(temp).rglob("*.docx"))
                self.assertEqual(len(generated), 1)
                original = ROOT / "Законопроекты" / folder / bill["file"]
                with zipfile.ZipFile(original) as before, zipfile.ZipFile(generated[0]) as after:
                    self.assertEqual(set(before.namelist()), set(after.namelist()))
                    for name in before.namelist():
                        self.assertEqual(before.read(name), after.read(name), name)


if __name__ == "__main__":
    unittest.main()
