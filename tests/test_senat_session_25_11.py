# -*- coding: utf-8 -*-
"""Созыв 25.11: подтверждённые сведения, общий текст и изоляция от образца."""
import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_senat_session_25_11 as convocation
import make_senat_session_png as layout

SESSION = ROOT / "Повестка" / "25.11.26"
OUT = SESSION / "01 Созыв"
OLD = ROOT / "Повестка" / "19.11.2026" / "01 Созыв"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ConvocationTests(unittest.TestCase):
    def test_confirmed_data_and_common_text(self):
        plain = (OUT / convocation.PLAIN_FILENAME).read_text(encoding="utf-8")
        markdown = (OUT / f"{convocation.BASENAME}.md").read_text(encoding="utf-8")
        bb = (OUT / convocation.BB_FILENAME).read_text(encoding="utf-8")
        self.assertEqual(plain, convocation.plain_text())
        self.assertEqual(markdown, convocation.markdown())
        self.assertEqual(bb, convocation.bbcode())
        for text in (plain, markdown, bb):
            for item in (convocation.TITLE, convocation.DATE_META, convocation.TIME_META,
                         convocation.LEAD, convocation.BAND):
                self.assertIn(item, text)
            for heading, number, paragraph in convocation.SECTIONS:
                self.assertIn(heading, text)
                self.assertIn(number, text)
                self.assertIn(paragraph, text)
            self.assertIn("25 ноября 2026 года в 19:00", text)
            for unsupported in ("Marcus", "Спикер", "Лос-Сантос", "Капитолий", "паспорт",
                                "кворум", "статья", "штраф", "UTC", "GMT",
                                "19 ноября 2026", "13 ноября 2026"):
                self.assertNotIn(unsupported.casefold(), text.casefold())

    def test_bbcode_tags_are_balanced(self):
        bb = (OUT / convocation.BB_FILENAME).read_text(encoding="utf-8")
        self.assertTrue(bb.startswith("[FONT=Times New Roman]\n"))
        self.assertIn(f'[IMG width="320px"]{convocation.LOGO_URL}[/IMG]', bb)
        tag = re.compile(r"\[(/?)(FONT|CENTER|IMG|I|B|COLOR|SIZE)(?:[ =][^\]]*)?\]", re.I)
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

    def test_text_only_needs_neither_font_nor_pillow_and_keeps_png(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            png = output / f"{convocation.BASENAME}.png"
            png.write_bytes(b"unchanged image")
            with patch.object(convocation, "render_png", side_effect=AssertionError("PNG rebuild")):
                paths = convocation.build_texts(output)
            self.assertEqual({p.name for p in paths},
                             {convocation.PLAIN_FILENAME, f"{convocation.BASENAME}.md",
                              convocation.BB_FILENAME})
            (output / convocation.BB_FILENAME).write_text("outdated", encoding="utf-8")
            # -I -S исключает site-packages: текст не требует Pillow и шрифтов.
            subprocess.run([sys.executable, "-I", "-S",
                            str(ROOT / "tools" / "make_senat_session_25_11.py"),
                            "--text-only", "--output-dir", str(output)],
                           check=True, capture_output=True, text=True)
            self.assertEqual((output / convocation.BB_FILENAME).read_text(encoding="utf-8"),
                             convocation.bbcode())
            self.assertEqual(png.read_bytes(), b"unchanged image")

    def test_structure_and_png_design(self):
        self.assertTrue(OUT.is_dir())
        self.assertEqual(convocation.OUT_DIR, OUT)
        expected = {convocation.PLAIN_FILENAME, f"{convocation.BASENAME}.md",
                    f"{convocation.BASENAME}.png", convocation.BB_FILENAME}
        names = {p.name for p in OUT.iterdir() if p.is_file()}
        self.assertTrue(expected.issubset(names))
        for name in expected:
            self.assertFalse((ROOT / "Повестка" / name).exists(), name)
        for name in ("02 Повестка", "03 Итоги", "04 Журнал", "05 Исходные данные"):
            self.assertTrue((SESSION / name).is_dir(), name)
        self.assertFalse(any("протокол" in path.name.casefold() for path in SESSION.rglob("*")))
        with Image.open(OUT / f"{convocation.BASENAME}.png") as image:
            self.assertEqual(image.size, (3000, 4225))
            self.assertEqual(image.mode, "RGB")
            self.assertEqual(image.getpixel((116, 92)), layout.GREEN)
            self.assertAlmostEqual(image.info["dpi"][0], 300, delta=1)
            self.assertNotIn("http", str(image.info).lower())

    def test_readme_links_and_pending_materials(self):
        readme = (SESSION / "README.md").read_text(encoding="utf-8")
        self.assertIn("25 ноября 2026 года в 19:00", readme)
        self.assertIn("Место проведения, часовой пояс и подписант не указаны", readme)
        links = re.findall(r"\]\(([^)]+)\)", readme)
        self.assertGreaterEqual(len(links), 4)
        for link in links:
            if not link.startswith(("http://", "https://")):
                self.assertTrue((SESSION / unquote(link)).is_file(), link)

    def test_rebuild_preserves_template_and_layout_globals(self):
        try:
            import make_senat_session_19_11 as previous
            previous.font_faces()
        except SystemExit:
            self.skipTest("Times New Roman не установлен; укажите SENATE_FONT_DIR")
        template_files = [OLD / "Созыв заседания Сената - 19.11.2026.png",
                          OLD / "Созыв заседания Сената - 19.11.2026.md",
                          OLD / "Созыв заседания Сената - 19.11.2026 - BB-код.txt"]
        before = [sha256(path) for path in template_files]
        layout_before = {name: getattr(layout, name) for name in ("FR", "FB", "FI", "BAND")}
        base_before = {name: getattr(layout.base, name) for name in ("FR", "FB", "FI")}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(layout, "para", wraps=layout.para) as para:
                convocation.build(output)
            rendered_text = ["".join(run[0] for run in call.args[2]) for call in para.call_args_list]
            self.assertEqual(rendered_text, [convocation.LEAD] +
                             [f"{number} {paragraph}" for _, number, paragraph in convocation.SECTIONS])
            self.assertEqual((output / convocation.PLAIN_FILENAME).read_text(encoding="utf-8"),
                             convocation.plain_text())
            self.assertEqual((output / convocation.BB_FILENAME).read_text(encoding="utf-8"),
                             convocation.bbcode())
            with Image.open(output / f"{convocation.BASENAME}.png") as image:
                self.assertEqual(image.size, (3000, 4225))
        self.assertEqual([sha256(path) for path in template_files], before)
        self.assertEqual({name: getattr(layout, name) for name in layout_before}, layout_before)
        self.assertEqual({name: getattr(layout.base, name) for name in base_before}, base_before)


if __name__ == "__main__":
    unittest.main()
