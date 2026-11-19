# -*- coding: utf-8 -*-
"""Рабочий пакет ACT. 301-303 и побайтное сохранение перенесённых документов."""
import hashlib
import re
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import build_act303 as territory
import build_acts301_302 as releases

ARCHIVE = ROOT / "Архив/Законопроекты 299-300 и 304-307 (перенесены в архив)"
ACTIVE = ROOT / "Законопроекты"
ACTIVE_HASHES = {
    301: "4f823a83c5c22c468496bcfa4cd7f48b4429bfbecb00fc91e454d9429ba89078",
    302: "6fd81a302a810b6b240880263cd222a75f0a5029387d274454e91be638d80ec1",
    303: "8dd8dc6cdd745c9623a58347a4d8facc3257c185304785c34c7dc4cbf97b2037",
}
MANIFEST_SHA256 = "122c994bf8e7eb02710006e8cd121afe04aca4689396d943bbed117a2c86275f"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_files():
    result = {}
    for line in (ARCHIVE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError(relative)
        result[relative] = expected
    return result


class ActiveBillsAndArchiveTests(unittest.TestCase):
    def test_only_301_302_303_and_template_are_active(self):
        expected = {
            "Законопроекты 301 - освобождение и выход",
            "Законопроекты 302 - вызов и статус начальства",
            "Законопроекты 303 - режим территорий",
            "_ШАБЛОН",
        }
        self.assertEqual({p.name for p in ACTIVE.iterdir() if p.is_dir()}, expected)
        for number in (301, 302, 303):
            directory = next(ACTIVE.glob(f"Законопроекты {number} - *"))
            files = list(directory.glob("*.docx"))
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].name.startswith(f"ACT.{number}."))
            self.assertEqual(Document(files[0]).paragraphs[0].text, f"ACT. {number}")
            self.assertEqual(digest(files[0]), ACTIVE_HASHES[number])
            self.assertTrue((directory / "ПОЯСНЕНИЕ К ПАПКЕ.md").is_file())

    def test_six_archived_folders_and_original_bytes(self):
        expected = {299, 300, 304, 305, 306, 307}
        folders = [p for p in ARCHIVE.iterdir() if p.is_dir()]
        numbers = {int(re.match(r"Законопроекты (\d+) - ", p.name).group(1)) for p in folders}
        self.assertEqual(numbers, expected)
        self.assertEqual(len(folders), len(expected))
        manifest = ARCHIVE / "SHA256SUMS.txt"
        self.assertEqual(digest(manifest), MANIFEST_SHA256)
        files = manifest_files()
        self.assertEqual(len(files), 12)
        for folder in folders:
            actual = {p.name for p in folder.iterdir() if p.is_file()}
            self.assertEqual(len(actual), 2)
            self.assertEqual(len(list(folder.glob("*.docx"))), 1)
            self.assertIn("ПОЯСНЕНИЕ К ПАПКЕ.md", actual)
            expected_names = {Path(k).name for k in files if Path(k).parts[0] == folder.name}
            self.assertEqual(actual, expected_names)
        for relative, expected_hash in files.items():
            with self.subTest(file=relative):
                self.assertEqual(digest(ARCHIVE / relative), expected_hash)
        self.assertIn("не входят в текущий пакет", (ARCHIVE / "README.md").read_text(encoding="utf-8"))

    def test_archived_builders_are_not_active_and_cannot_recreate_projects(self):
        self.assertFalse((ROOT / "tools/build_sang_299_300.py").exists())
        self.assertFalse((ROOT / "tools/build_acts304_307.py").exists())
        code = ROOT / "Архив/Скрипты сборки законопроектов/Выпуски 299-300 и 304-307 (исторические)"
        for name in ("build_sang_299_300.py", "build_acts304_307.py", "test_sang_299_300.py",
                     "test_acts304_307.py", "test_bundle_compatibility.py"):
            self.assertTrue((code / name).is_file())
        before = {name: digest(ARCHIVE / name) for name in manifest_files()}
        with TemporaryDirectory() as temp:
            target = Path(temp)
            with patch.object(releases, "OUT", target), patch.object(
                territory, "OUT", target / "Законопроекты 303 - режим территорий"
            ), redirect_stdout(StringIO()):
                releases.main()
                territory.main()
            docx = sorted(p.name for p in target.rglob("*.docx"))
            self.assertEqual(len(docx), 3)
            self.assertEqual([int(re.match(r"ACT\.(\d+)\.", x).group(1)) for x in docx],
                             [301, 302, 303])
        self.assertEqual(before, {name: digest(ARCHIVE / name) for name in manifest_files()})

    def test_remaining_proposals_target_distinct_provisions(self):
        active = [b for _, b in releases.specs()] + [territory.specs()[0]]
        locators = {}
        for bill in active:
            for left, _ in bill["rows"]:
                title, locator, _ = territory.plain(left).split("\n", 2)
                key = title, locator
                self.assertNotIn(key, locators, (bill["num"], locators.get(key), key))
                locators[key] = bill["num"]
        _, patches, _ = territory.specs()
        self.assertFalse(any(p.source == territory.SANG and p.locator == "Статья 2, часть 7"
                             for p in patches))
        notes = (territory.OUT / "ПОЯСНЕНИЕ К ПАПКЕ.md").read_text(encoding="utf-8")
        self.assertIn("ACT. 300 перенесён в архив", notes)
        self.assertIn("ACT. 303 данное положение не изменяет", notes)


if __name__ == "__main__":
    unittest.main()
