# -*- coding: utf-8 -*-
"""Новый созыв: подтверждённые данные, оформление и изоляция от 13.11."""
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_senat_session_19_11 as convocation

SESSION = ROOT / "Повестка" / "19.11.2026"
OUT = SESSION / "01 Созыв"
OLD = ROOT / "Повестка" / "13.11.2026" / "01 Созыв"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ConvocationTests(unittest.TestCase):
    def test_confirmed_data_and_common_text(self):
        content = (OUT / f"{convocation.BASENAME}.md").read_text(encoding="utf-8")
        self.assertEqual(content, convocation.markdown())
        self.assertIn("19 ноября 2026 года, г. Лос-Сантос", content)
        self.assertIn("**19 НОЯБРЯ 2026 ГОДА, 19:00**", content)
        self.assertIn("19 ноября 2026 года в 19:00", content)
        self.assertIn("в зале заседаний Сената, Капитолий штата Сан-Андреас, город Лос-Сантос", content)
        self.assertIn("Marcus Nomad", content)
        self.assertIn("номер паспорта 85028", content)
        self.assertIn("Спикер Сената", content)
        self.assertNotIn("13 ноября 2026 года", content)
        self.assertNotIn("12 ноября 2026 года", content)
        self.assertNotRegex(content + convocation.RIGHT_META, r"\bID\b")
        self.assertNotIn("http://", content)
        self.assertNotIn("https://", content)
        self.assertNotIn("Google Docs", content)

    def test_legal_references_match_the_new_base(self):
        law = ROOT / "Законодательная база" / "Конституционный закон «О Сенате штата Сан-Андреас».json"
        data = json.loads(law.read_text(encoding="utf-8"))
        articles = {(s.get("text") or "").split("\n", 1)[0]: s.get("text") or ""
                    for s in data["sections"]}
        self.assertIn("назначает заседания Сената", articles["Статья 3."])
        self.assertIn("неявку на плановое заседание", articles["Статья 3."])
        self.assertIn("не менее половины действующих сенаторов", articles["Статья 9."])
        content = convocation.markdown()
        self.assertEqual(content.count(f"**{convocation.LAW}**"), 3)
        self.assertIn("При неявке на плановое заседание", content)
        self.assertIn("вправе применить меры", content)
        self.assertIn("часть 1 статьи 9", content)

    def test_structure_and_no_new_protocol(self):
        self.assertEqual({p.name for p in SESSION.iterdir() if p.is_dir()},
                         {"01 Созыв", "02 Повестка", "03 Итоги", "04 Журнал", "05 Исходные данные"})
        self.assertFalse(any("протокол" in p.name.casefold() for p in SESSION.rglob("*")))
        for name in ("02 Повестка", "03 Итоги", "04 Журнал", "05 Исходные данные"):
            self.assertEqual({p.name for p in (SESSION / name).iterdir()}, {".gitkeep"})
        readme = (SESSION / "README.md").read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", readme):
            self.assertTrue((SESSION / unquote(link)).is_file(), link)

    def test_png_dimensions_and_design(self):
        png = OUT / f"{convocation.BASENAME}.png"
        with Image.open(png) as image:
            self.assertEqual(image.size, (3000, 4225))
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.getpixel((116, 92)), convocation.layout.GREEN)
            self.assertAlmostEqual(image.info["dpi"][0], 300, delta=1)
            self.assertNotIn("http", str(image.info).lower())

    def test_rebuild_with_times_new_roman_does_not_touch_13_11(self):
        try:
            faces = convocation.font_faces()
        except SystemExit:
            self.skipTest("Times New Roman не установлен; укажите SENATE_FONT_DIR")
        self.assertEqual([ImageFont.truetype(str(p), 12).getname() for p in faces],
                         [("Times New Roman", "Regular"), ("Times New Roman", "Bold"),
                          ("Times New Roman", "Italic")])
        originals = [OLD / "Созыв заседания Сената - 13.11.2026.png",
                     OLD / "Созыв заседания Сената - 13.11.2026.md"]
        before = [sha256(p) for p in originals]
        names = ("FR", "FB", "FI", "DATE_LINE", "RIGHT_META", "TITLE", "SUBTITLE",
                 "LEAD", "BAND", "body", "SECTIONS")
        layout_before = {name: getattr(convocation.layout, name) for name in names}
        base_before = {name: getattr(convocation.layout.base, name) for name in ("FR", "FB", "FI")}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            convocation.build(output)
            self.assertEqual({p.name for p in output.iterdir()},
                             {f"{convocation.BASENAME}.md", f"{convocation.BASENAME}.png"})
            self.assertEqual((output / f"{convocation.BASENAME}.md").read_text(encoding="utf-8"),
                             convocation.markdown())
            with Image.open(output / f"{convocation.BASENAME}.png") as image:
                self.assertEqual(image.size, (3000, 4225))
        self.assertEqual([sha256(p) for p in originals], before)
        self.assertEqual({name: getattr(convocation.layout, name) for name in names}, layout_before)
        self.assertEqual({name: getattr(convocation.layout.base, name) for name in base_before}, base_before)


if __name__ == "__main__":
    unittest.main()
