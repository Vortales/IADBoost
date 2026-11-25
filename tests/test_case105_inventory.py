# -*- coding: utf-8 -*-
"""Инвентарь дела № 105: уникальные файлы и сохранность различных источников."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "Компромат на Jonny Zakonov/Текущая работа/Иск № 105 и связанные дела"
PACKAGE = CASE / "Ответ суду и протоколы"
INVENTORY = CASE / "README.md"
SOURCES = CASE / "07 Источники из архива"


class Case105InventoryTests(unittest.TestCase):
    def test_canonical_filings_exist_without_the_old_duplicate_copies(self):
        for retained in (PACKAGE / "01 Ответ на запрос - BB-код.txt",
                         PACKAGE / "02 Возражения - BB-код.txt"):
            with self.subTest(retained=retained):
                self.assertTrue(retained.is_file())
        for removed in (CASE / "04 Ответ на запрос суда - BB-код.txt",
                        CASE / "05 Возражения по существу и срокам - BB-код.txt"):
            with self.subTest(removed=removed):
                self.assertFalse(removed.exists())

    def test_no_byte_identical_files_in_case_directory(self):
        seen = {}
        for path in sorted(CASE.rglob("*")):
            if not path.is_file():
                continue
            digest = hashlib.sha256(path.read_bytes()).digest()
            with self.subTest(path=path):
                self.assertNotIn(digest, seen, f"Повтор {path}: совпадает с {seen.get(digest)}")
                seen[digest] = path

    def test_inventory_links_to_every_retained_file(self):
        links = set()
        for href in re.findall(r"\]\(([^)]+)\)", INVENTORY.read_text(encoding="utf-8")):
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (INVENTORY.parent / unquote(parsed.path)).resolve()
            try:
                target.relative_to(CASE.resolve())
            except ValueError:
                continue
            if target.is_file() and target != INVENTORY.resolve():
                links.add(target)
        files = {path.resolve() for path in CASE.rglob("*") if path.is_file() and path != INVENTORY}
        self.assertSetEqual(links, files)

    def test_distinct_archived_snapshots_retain_their_ocr_difference(self):
        nested = SOURCES / "Иск № 105 - вложенный срез.json"
        root = SOURCES / "Иск № 105 - корневой срез.json"
        self.assertNotEqual(nested.read_bytes(), root.read_bytes())
        nested_page = json.loads(nested.read_text(encoding="utf-8"))["posts"][3]["blocks"][1]
        root_page = json.loads(root.read_text(encoding="utf-8"))["posts"][3]["blocks"][1]
        self.assertTrue(nested_page["ocr_text"])
        self.assertIsNone(root_page["ocr_text"])
        self.assertTrue(root_page["ocr_pending"])


if __name__ == "__main__":
    unittest.main()
