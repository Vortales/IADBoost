# -*- coding: utf-8 -*-
"""Проверка независимой базы и общих средств подготовки."""
import hashlib
import importlib.util
import json
import shutil
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import billkit
import legal_sources as sources

BASE = ROOT / "Законодательная база"

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
            shutil.copy2(BASE / f"{sources.PC}.json", root / "Законодательная база")
            spec = importlib.util.spec_from_file_location("portable_billkit", kit)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(Path(module.ROOT), root)
            self.assertEqual(module.load(sources.PC), billkit.load(sources.PC))

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
