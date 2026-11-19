# -*- coding: utf-8 -*-
"""Совместимость инициатив SANG и перенумерованного пакета."""
import hashlib
import itertools
import re
import sys
import unittest
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import billkit
import build_act303 as territory
import build_acts301_302 as releases
import build_acts304_307 as defence
import build_sang_299_300 as sang
import legal_sources as law


def all_bills():
    return (sang.specs() + releases.specs() + [(territory.OUT.name, territory.specs()[0])]
            + defence.specs()[0])


def body(value):
    return territory.plain(value).split("\n", 2)[2]


def bill(number):
    found = [b for _, b in all_bills() if b["num"] == number]
    if len(found) != 1:
        raise AssertionError(number)
    return found[0]


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError(f"Фрагмент не найден или не уникален: {old[:100]!r}")
    return text.replace(old, new, 1)


class BundleCompatibilityTests(unittest.TestCase):
    def test_unified_folders_and_number_mapping(self):
        expected = {
            299: "выход с территории Форта",
            300: "охрана военных объектов",
            301: "освобождение и выход",
            302: "вызов и статус начальства",
            303: "режим территорий",
            304: "прокурор по ходатайству адвоката",
            305: "материалы защиты",
            306: "устные ходатайства",
            307: "фактические обстоятельства",
        }
        self.assertEqual([b["num"] for _, b in all_bills()], list(expected))
        base = ROOT / "Законопроекты"
        for num, topic in expected.items():
            folder = base / f"Законопроекты {num} - {topic}"
            files = list(folder.glob("*.docx"))
            self.assertEqual(len(files), 1, folder)
            self.assertTrue(files[0].name.startswith(f"ACT.{num}."))
            self.assertEqual(Document(files[0]).paragraphs[0].text, f"ACT. {num}")
        self.assertFalse((base / "Инициативы SANG").exists())
        self.assertFalse((base / "Законопроекты 316 - обыск в суде").exists())
        self.assertFalse(any(re.match(r"Законопроекты 31[3-9] - |Законопроекты 320 - ", p.name)
                             for p in base.iterdir()))

    def test_no_two_bills_target_the_same_comparison_locator(self):
        locators = {}
        for _, item in all_bills():
            for left, _ in item["rows"]:
                title, locator, _ = territory.plain(left).split("\n", 2)
                key = (title, locator)
                self.assertNotIn(key, locators, (item["num"], locators.get(key), key))
                locators[key] = item["num"]
        self.assertEqual(locators[(law.SANG_TITLE, "Статья 2, часть 7")], 300)

    def test_300_and_303_change_guard_law_in_both_orders(self):
        base = law.clean(billkit.load(law.SANG)[4])
        old300, new300 = map(body, bill(300)["rows"][0])
        _, patches, _ = territory.specs()
        guard = [p for p in patches if (p.source, p.section) == (law.SANG, 4)]
        self.assertEqual([p.locator for p in guard], ["Статья 2, часть 6"])
        p = guard[0]
        a = replace_once(replace_once(base, old300, new300), p.old, p.new)
        b = replace_once(replace_once(base, p.old, p.new), old300, new300)
        self.assertEqual(a, b)
        self.assertEqual(a.count("ч. 7. При незаконном нахождении"), 1)
        self.assertIn("статьи 10 настоящего Закона", a)
        self.assertIn("при отражении нападения на форт", a.lower())
        self.assertIn("Доступ на прилегающую территорию до КПП", a)
        self.assertIn("ч. 8 К территориальной юрисдикции", a)

    def test_299_302_and_303_combine_in_every_order(self):
        source = law.clean(billkit.load(law.APP)[7])
        p303 = [p for p in territory.specs()[1] if (p.source, p.section) == (law.APP, 7)]
        p302 = [(body(left), body(right)) for left, right in bill(302)["rows"]
                if territory.plain(left).startswith(law.APP_TITLE + "\n")]
        self.assertEqual(len(p302), 2)
        p299 = body(bill(299)["rows"][0][1])
        anchor = "\nб)\n"

        def apply(value, num):
            if num == 299:
                self.assertNotIn("Примечание 1.1:", value)
                self.assertEqual(value.count(anchor), 1)
                return value.replace(anchor, "\n" + p299 + anchor, 1)
            if num == 302:
                for old, new in p302:
                    value = replace_once(value, old, new)
                return value
            for p in p303:
                value = replace_once(value, p.old, p.new) if p.old else value.rstrip() + "\n" + p.new
            return value

        combined = []
        for order in itertools.permutations((299, 302, 303)):
            result = source
            for num in order:
                result = apply(result, num)
            self.assertEqual(result.count("Примечание 1.1:"), 1, order)
            self.assertEqual(result.count("одно лицо, вызванное как начальство задержанного"), 2, order)
            self.assertEqual(result.count("Примечание 9:"), 1, order)
            self.assertIn("горячей линии «911»", result)
            combined.append(result)
        self.assertEqual(len(set(combined)), 1)

    def test_301_leave_guarantee_and_sang_measures_are_compatible(self):
        release = body(bill(301)["rows"][0][1])
        exit_rule = body(bill(301)["rows"][1][1])
        fort_exit = body(bill(299)["rows"][0][1])
        guard = body(bill(300)["rows"][0][1])
        self.assertIn("незамедлительно снять примененные наручники", release)
        self.assertIn("по 5 минут для выхода", exit_rule)
        self.assertIn("Нахождение для выхода в пределах срока является законным", exit_rule)
        self.assertIn("Время ожидания сопровождения", exit_rule)
        self.assertIn("не имеющего законных оснований", fort_exit)
        self.assertIn("с учетом установленных законом сроков", fort_exit)
        self.assertIn("При незаконном нахождении", guard)
        self.assertIn("с учетом установленных законом сроков", guard)
        self.assertIn("Невыполнение требования уйти само по себе не является основанием для применения оружия", guard)
        self.assertNotIn("ACT. 301", guard)
        self.assertNotIn("статьей 4.1", guard)

    def test_authored_input_is_preserved_and_material_changes_are_transferred(self):
        path = ROOT / "Законопроекты после правок.7z"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         "6dbb2c159ae8a624840befc65360afd51e7c5b7a6c8abcf9fedcf5901e580f58")
        supervisor = body(bill(302)["rows"][0][1])
        self.assertIn("для государственных и частных адвокатов - Глава Коллегии адвокатов или его заместитель, "
                      "а при их отсутствии - Старший адвокат", supervisor)
        self.assertIn("Если лицо, законно находящееся на объекте, заявило, что является начальством задержанного, "
                      "то сотрудник без промедления проверяет его личность и полномочия.", supervisor)
        self.assertNotIn("государственных юристов", supervisor)
        patches = {p.locator: p for p in territory.specs()[1]}
        goal = patches["Статья 2, цели посещения SANG"].new
        self.assertIn("на территории Форта за КПП-2 до линии развилки", goal)
        self.assertIn("только в сопровождении уполномоченного лица Национальной гвардии", goal)
        note = patches["Статья 4, пункт «а», примечание 1"].new
        self.assertIn("размахивания кулаками, ногами", note)
        self.assertIn("вызвать сотрудников правоохранительных органов по телефону горячей линии «911»", note)
        self.assertIn("Вызов не исключает иных мер при наличии самостоятельных законных оснований", note)


if __name__ == "__main__":
    unittest.main()
