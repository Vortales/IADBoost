# -*- coding: utf-8 -*-
"""Новый созыв: подтверждённые данные, оформление и изоляция от 13.11."""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_senat_session_19_11 as convocation
import make_senat_session_png as layout

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

    def test_bbcode_matches_png_source_and_is_balanced(self):
        path = OUT / convocation.BB_FILENAME
        bb = path.read_text(encoding="utf-8")
        self.assertEqual(bb, convocation.bbcode())
        self.assertTrue(bb.startswith("[FONT=Times New Roman]\n"))
        self.assertIn(f'[IMG width="320px"]{convocation.LOGO_URL}[/IMG]', bb)
        self.assertIn("STATE of SAN ANDREAS", bb)
        self.assertIn("SENATE OF THE STATE OF SAN ANDREAS", bb)
        self.assertIn("[B]Marcus Nomad[/B]", bb)
        self.assertIn("[I]Спикер Сената штата Сан-Андреас[/I]", bb)
        self.assertEqual(bb.count(f"[B]{convocation.LAW}[/B]"), 3)
        self.assertIn("[SIZE=6]", bb)
        self.assertIn("[SIZE=5]", bb)
        self.assertNotIn("13 ноября 2026 года", bb)
        self.assertNotRegex(bb, r"\bID\b")

        tag = re.compile(r"\[(/?)(FONT|CENTER|RIGHT|IMG|I|B|COLOR|SIZE)(?:[ =][^\]]*)?\]", re.I)
        stack = []
        for match in tag.finditer(bb):
            close, name = match.group(1), match.group(2).upper()
            if close:
                self.assertTrue(stack, match.group(0))
                self.assertEqual(stack.pop(), name, match.group(0))
            else:
                if name == "SIZE":
                    self.assertNotIn("SIZE", stack)
                stack.append(name)
        self.assertEqual(stack, [])
        plain = tag.sub("", bb)
        for text in (convocation.DATE_LINE, convocation.RIGHT_META, convocation.TITLE,
                     convocation.SUBTITLE.upper(), convocation.LEAD, convocation.BAND, convocation.CLOSING):
            self.assertIn(text, plain)
        for heading, paragraphs in convocation.SECTIONS:
            self.assertIn(heading, plain)
            for number, fragments in paragraphs:
                self.assertIn(f"{number} {''.join(value for value, _ in fragments)}", plain)

    def test_bb_only_does_not_rebuild_png_or_need_fonts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            png = output / f"{convocation.BASENAME}.png"
            md = output / f"{convocation.BASENAME}.md"
            png.write_bytes(b"unchanged image")
            md.write_text("unchanged text", encoding="utf-8")
            with patch.object(convocation, "font_faces", side_effect=AssertionError("PNG rebuild")):
                path = convocation.build_bb(output)
            self.assertEqual(path.name, convocation.BB_FILENAME)
            self.assertEqual(path.read_text(encoding="utf-8"), convocation.bbcode())
            path.write_text("outdated", encoding="utf-8")
            # -I -S исключает site-packages: для BB-кода не нужны Pillow и шрифты.
            subprocess.run([sys.executable, "-I", "-S",
                            str(ROOT / "tools" / "make_senat_session_19_11.py"),
                            "--bb-only", "--output-dir", str(output)],
                           check=True, capture_output=True, text=True)
            self.assertEqual(path.read_text(encoding="utf-8"), convocation.bbcode())
            self.assertEqual({p.name for p in output.iterdir()}, {png.name, md.name, path.name})
            self.assertEqual(png.read_bytes(), b"unchanged image")
            self.assertEqual(md.read_text(encoding="utf-8"), "unchanged text")

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
            self.assertEqual(image.getpixel((116, 92)), layout.GREEN)
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
        layout_before = {name: getattr(layout, name) for name in names}
        base_before = {name: getattr(layout.base, name) for name in ("FR", "FB", "FI")}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            convocation.build(output)
            self.assertEqual({p.name for p in output.iterdir()},
                             {f"{convocation.BASENAME}.md", f"{convocation.BASENAME}.png",
                              convocation.BB_FILENAME})
            self.assertEqual((output / f"{convocation.BASENAME}.md").read_text(encoding="utf-8"),
                             convocation.markdown())
            self.assertEqual((output / convocation.BB_FILENAME).read_text(encoding="utf-8"),
                             convocation.bbcode())
            with Image.open(output / f"{convocation.BASENAME}.png") as image:
                self.assertEqual(image.size, (3000, 4225))
        self.assertEqual([sha256(p) for p in originals], before)
        self.assertEqual({name: getattr(layout, name) for name in names}, layout_before)
        self.assertEqual({name: getattr(layout.base, name) for name in base_before}, base_before)


if __name__ == "__main__":
    unittest.main()
