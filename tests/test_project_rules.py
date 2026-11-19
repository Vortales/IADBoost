# -*- coding: utf-8 -*-
"""Инвентаризация установленных исходных файлов и служебного порядка работы."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "Правила проекта"


class RulesSnapshotTests(unittest.TestCase):
    def test_manifest_matches_all_nineteen_json_files(self):
        records = (RULES / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(records), 19)
        manifest = {}
        for record in records:
            digest, name = record.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertNotIn(name, manifest)
            self.assertEqual(Path(name).name, name)
            manifest[name] = digest
        files = list(RULES.glob("*.json"))
        self.assertEqual({p.name for p in files}, set(manifest))
        urls = set()
        for path in files:
            with self.subTest(path=path.name):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), manifest[path.name])
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(data["sections"])
                self.assertTrue(data["posts"][0]["text"].strip())
                self.assertRegex(data["parsed_at"], r"^2026-11-(15|18) ")
                url = data.get("norm_url") or data["url"]
                self.assertTrue(url.startswith("https://"))
                self.assertNotIn(url, urls)
                urls.add(url)

    def test_archive_removed_and_private_workflow_is_durable(self):
        self.assertFalse((ROOT / "Правила проекта.7z").exists())
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for expected in ("Перед каждой новой редакцией", "`Правила проекта/`",
                         "не упоминайте в законопроектах", "в личном ответе пользователю",
                         "не создавайте отдельный файл", "52 JSON"):
            self.assertIn(expected, instructions)


if __name__ == "__main__":
    unittest.main()
