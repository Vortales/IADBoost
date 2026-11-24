# -*- coding: utf-8 -*-
"""Созыв 25.11 повторяет образец 19.11 с заменой даты и не меняет его."""
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

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_senat_session_19_11 as template
import make_senat_session_25_11 as convocation
import make_senat_session_png as layout

SESSION = ROOT / "Повестка" / "25.11.26"
OUT = SESSION / "01 Созыв"
OLD = ROOT / "Повестка" / "19.11.2026" / "01 Созыв"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_date(text):
    return (text.replace("19 ноября 2026 года", "25 ноября 2026 года")
                .replace("19 НОЯБРЯ 2026 ГОДА", "25 НОЯБРЯ 2026 ГОДА"))


class ConvocationTests(unittest.TestCase):
    def test_text_and_bbcode_match_sample_except_date(self):
        plain = (OUT / convocation.PLAIN_FILENAME).read_text(encoding="utf-8")
        markdown = (OUT / f"{convocation.BASENAME}.md").read_text(encoding="utf-8")
        bb = (OUT / convocation.BB_FILENAME).read_text(encoding="utf-8")
        old_md = (OLD / f"{template.BASENAME}.md").read_text(encoding="utf-8")
        old_bb = (OLD / template.BB_FILENAME).read_text(encoding="utf-8")
        self.assertEqual(markdown, replace_date(old_md))
        self.assertEqual(bb, replace_date(old_bb))
        self.assertEqual(markdown, convocation.markdown())
        self.assertEqual(bb, convocation.bbcode())
        self.assertEqual(plain, convocation.plain_text())
        bb_plain = re.sub(r"\[/?[^\]]+\]", "", bb)
        for text in (plain, markdown, bb_plain):
            for item in (convocation.TITLE, convocation.DATE_LINE, convocation.RIGHT_META,
                         convocation.LEAD, convocation.BAND, convocation.CLOSING):
                self.assertIn(item, text)
            self.assertIn("25 ноября 2026 года в 19:00", text)
            self.assertIn("Marcus Nomad", text)
            self.assertIn("номер паспорта 85028", text)
            self.assertIn("Капитолий штата Сан-Андреас, город Лос-Сантос", text)
            self.assertNotIn("19 ноября 2026 года", text)
            self.assertNotIn("19 НОЯБРЯ 2026 ГОДА", text)
            self.assertNotIn("UTC", text)
            self.assertNotIn("GMT", text)
        for heading, paragraphs in convocation.SECTIONS:
            self.assertIn(heading, plain)
            self.assertIn(heading, bb_plain)
            for number, fragments in paragraphs:
                paragraph = f"{number} {''.join(value for value, _ in fragments)}"
                self.assertIn(paragraph, plain)
                self.assertIn(paragraph, bb_plain)
        self.assertIn("пункт «а» части 4 статьи 3", plain)
        self.assertIn("пунктом «и» части 4 статьи 3", plain)
        self.assertIn("часть 1 статьи 9", plain)

    def test_bbcode_tags_are_balanced(self):
        bb = (OUT / convocation.BB_FILENAME).read_text(encoding="utf-8")
        self.assertTrue(bb.startswith("[FONT=Times New Roman]\n"))
        self.assertIn(f'[IMG width="320px"]{convocation.LOGO_URL}[/IMG]', bb)
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

    def test_readme_warns_about_copied_details_and_legal_references(self):
        readme = (SESSION / "README.md").read_text(encoding="utf-8")
        self.assertIn("25 ноября 2026 года в 19:00", readme)
        self.assertIn("подписант Marcus Nomad перенесены без изменений", readme)
        self.assertIn("применимость к заседанию 25.11 отдельно не подтверждена", readme)
        self.assertIn("Часовой пояс не указан", readme)
        self.assertIn("Перед публикацией нужна правовая сверка", readme)
        self.assertIn("части 4 статьи 3", readme)
        self.assertIn("части 1 статьи 9", readme)
        self.assertIn("статье 25 с округлением вниз", readme)
        self.assertIn("статья 38", readme)
        links = re.findall(r"\]\(([^)]+)\)", readme)
        self.assertGreaterEqual(len(links), 4)
        for link in links:
            if not link.startswith(("http://", "https://")):
                self.assertTrue((SESSION / unquote(link)).is_file(), link)

        path = ROOT / "Законодательная база/Конституционный закон «О Сенате штата Сан-Андреас».json"
        data = json.loads(path.read_text(encoding="utf-8"))
        articles = {(section.get("text") or "").split("\n", 1)[0]: section.get("text") or ""
                    for section in data["sections"]}
        self.assertIn("Сенаторами являются", articles["Статья 3."])
        self.assertIn("ответственность за проведение, созыв", articles["Статья 9."])
        self.assertIn("округляется в меньшую сторону", articles["Статья 25."])
        self.assertIn("на 2 заседаниях подряд", articles["Статья 38."])

    def test_rebuild_preserves_sample_and_template_globals(self):
        try:
            template.font_faces()
        except SystemExit:
            self.skipTest("Times New Roman не установлен; укажите SENATE_FONT_DIR")
        template_files = [OLD / f"{template.BASENAME}.png", OLD / f"{template.BASENAME}.md",
                          OLD / template.BB_FILENAME]
        before = [sha256(path) for path in template_files]
        layout_names = ("FR", "FB", "FI", "DATE_LINE", "RIGHT_META", "TITLE", "SUBTITLE",
                        "LEAD", "BAND", "body", "SECTIONS")
        layout_before = {name: getattr(layout, name) for name in layout_names}
        base_before = {name: getattr(layout.base, name) for name in ("FR", "FB", "FI")}
        template_before = {name: getattr(template, name) for name in ("DATE_LINE", "BAND", "SECTIONS")}
        observed = {}
        original_render = layout.render

        def capture_render(size):
            observed.update({name: getattr(layout, name) for name in ("DATE_LINE", "RIGHT_META", "BAND")})
            return original_render(size)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(layout, "para", wraps=layout.para) as para, \
                 patch.object(layout, "render", side_effect=capture_render):
                convocation.build(output)
            rendered = ["".join(run[0] for run in call.args[2]) for call in para.call_args_list]
            self.assertIn(convocation.LEAD, rendered)
            self.assertIn(convocation.CLOSING, rendered)
            for _, paragraphs in convocation.SECTIONS:
                for number, fragments in paragraphs:
                    self.assertIn(f"{number} {''.join(value for value, _ in fragments)}", rendered)
            self.assertTrue(all("19 ноября 2026 года" not in text for text in rendered))
            self.assertEqual(observed, {"DATE_LINE": convocation.DATE_LINE,
                                        "RIGHT_META": convocation.RIGHT_META,
                                        "BAND": convocation.BAND})
            self.assertEqual((output / convocation.PLAIN_FILENAME).read_text(encoding="utf-8"),
                             convocation.plain_text())
            self.assertEqual((output / convocation.BB_FILENAME).read_text(encoding="utf-8"),
                             convocation.bbcode())
            with Image.open(output / f"{convocation.BASENAME}.png") as image:
                self.assertEqual(image.size, (3000, 4225))
        self.assertEqual([sha256(path) for path in template_files], before)
        self.assertEqual({name: getattr(layout, name) for name in layout_before}, layout_before)
        self.assertEqual({name: getattr(layout.base, name) for name in base_before}, base_before)
        self.assertEqual({name: getattr(template, name) for name in template_before}, template_before)


if __name__ == "__main__":
    unittest.main()
