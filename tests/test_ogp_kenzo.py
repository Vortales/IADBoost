# -*- coding: utf-8 -*-
"""Проверки формы и опорных источников обращения Kenzo Wane."""
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "Законодательная база"
CASE = ROOT / "Обращения" / "ОГП - Kenzo Wane против FIB 2660"
BB = CASE / "Обращение в ОГП от гражданина Kenzo Wane - BB-код (черновик).txt"
ANALYSIS = CASE / "00. Правовой разбор.md"
GUIDE = CASE / "01. Подача и проверка.md"


def topic(glob):
    paths = list(BASE.glob(glob + "*.json"))
    if len(paths) != 1:
        raise AssertionError(f"Ожидался один источник для {glob!r}: {paths}")
    return json.loads(paths[0].read_text(encoding="utf-8"))


def article(data, title):
    matches = [s["text"] for s in data["sections"]
               if s.get("title", "").strip().rstrip(".") == title]
    if len(matches) != 1:
        raise AssertionError(f"Ожидалась одна статья {title!r}")
    return matches[0]


class OgpKenzoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bb = BB.read_text(encoding="utf-8")
        cls.analysis = ANALYSIS.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")

    def test_recommended_form_and_identity(self):
        for name in (
            "1. Данные заявителя", "2. Представитель",
            "3. Лицо, действия которого обжалуются", "4. Обстоятельства обращения",
            "5. Просьба заявителя", "6. Доказательства и приложения", "7. Тайм-коды",
        ):
            self.assertIn(f"[B]{name}[/B]", self.bb)
        for item in ("Kenzo Wane", "48905", "2660", "79325182", "insideofdead@ds.com",
                     "https://i.imgur.com/pTU8irD.png", "https://www.youtube.com/watch?v=G1CjZtgN3hE"):
            self.assertIn(item, self.bb)
        self.assertIn("Обращение в ОГП от гражданина Kenzo Wane", self.guide)
        self.assertNotIn("Marcus Nomad", self.bb)
        self.assertNotRegex(self.bb, r"\bID\b")

    def test_bbcode_is_balanced_and_uses_short_dash(self):
        tag = re.compile(r"\[(/?)(FONT|CENTER|RIGHT|B|COLOR|SIZE|URL)(?:[ =][^\]]*)?\]", re.I)
        stack = []
        for match in tag.finditer(self.bb):
            close, name = match.group(1), match.group(2).upper()
            if close:
                self.assertTrue(stack, match.group(0))
                self.assertEqual(stack.pop(), name, match.group(0))
            else:
                stack.append(name)
        self.assertEqual(stack, [])
        self.assertTrue(self.bb.startswith("[FONT=Times New Roman]\n"))
        self.assertTrue(self.bb.rstrip().endswith("[/FONT]"))
        self.assertNotIn("—", self.bb)
        self.assertNotIn("–", self.bb)
        if "УКАЗАТЬ" in self.bb:
            self.assertIn("ЧЕРНОВИК", self.bb)

    def test_evidence_and_disputed_facts_are_not_overstated(self):
        for timestamp in ("00:00-00:10", "00:32-00:35", "01:00-02:13", "02:35-02:46",
                          "09:26", "21:30-22:39"):
            self.assertIn(timestamp, self.bb)
        self.assertIn("Отдельного вызова от № 2660", self.bb)
        self.assertIn("я не получал", self.bb)
        self.assertIn("которому была предоставлена видеофиксация", self.bb)
        self.assertIn("не счита", self.bb)
        self.assertIn("независимо не проверены", self.analysis)
        self.assertIn("206297", self.analysis)
        self.assertIn("20697", self.analysis)
        self.assertIn("182618", self.analysis)
        self.assertIn("18618", self.analysis)

    def test_regulation_and_miranda_support_the_checklist(self):
        reg = topic("Регламент подачи обращений")
        text = reg["posts"][0]["text"]
        for item in ("Обращение в ОГП от гражданина", "дата и подпись",
                     "Для видео длиннее двух минут", "существенные изменения подаются ходатайством"):
            self.assertIn(item, text)
        code = topic("Процессуальный кодекс")
        art9 = article(code, "Статья 9")
        self.assertIn("48 часа", art9)
        self.assertIn("Офис Генерального прокурора", art9)
        art17 = article(code, "Статья 17")
        for item in ("может и будет использовано против задержанного в суде",
                     "при необходимости адвокат будет запрошен", "дальнейшее разъяснение",
                     "все показания, данные задержанным после такого оглашения"):
            self.assertIn(item, art17)

    def test_fib_guarantee_and_intelligence_exception_are_conditional(self):
        law = topic("Закон О Федеральном Расследовательском Бюро")
        art23 = article(law, "Статья 23")
        self.assertIn("ч. 6 При исполнении сотрудником ФРБ", art23)
        self.assertIn("в случаях совершения им преступления", art23)
        all_text = "\n".join(s.get("text", "") for s in law["sections"])
        self.assertIn("задержание объекта надзора вне процессуальных действий допускается", all_text)
        self.assertIn("статьей 12.7 Уголовного кодекса", all_text)
        self.assertIn("Часть 6 статьи 23", self.analysis)
        self.assertIn("Не установлено, состоит ли № 2660 в IB", self.analysis)

    def test_sources_are_in_the_current_database(self):
        urls = {json.loads(p.read_text(encoding="utf-8"))["url"] for p in BASE.glob("*.json")}
        linked_sources = re.findall(r"\]\((https://forum\.majestic-rp\.ru/[^)]+)\)", self.analysis)
        self.assertGreaterEqual(len(linked_sources), 12)
        self.assertTrue(set(linked_sources).issubset(urls))
        self.assertIn("не удалось", self.analysis)
        self.assertIn("не просмотрены", self.guide)


if __name__ == "__main__":
    unittest.main()
