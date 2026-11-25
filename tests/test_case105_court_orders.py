# -*- coding: utf-8 -*-
"""Стадия дела № 105 после текстов определений, переданных пользователем."""
import json
import re
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from tests.test_jonny_current_work import assert_balanced_bbcode


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "Компромат на Jonny Zakonov/Текущая работа"
CASE = WORK / "Иск № 105 и связанные дела"
PACKAGE = CASE / "Ответ суду и протоколы"
SOURCE = PACKAGE / "05 Определения 105-2 и 105-3 - текст пользователя.md"
RESPONSE = PACKAGE / "01 Ответ на запрос - BB-код.txt"
OBJECTIONS = PACKAGE / "02 Возражения - BB-код.txt"
GUIDANCE = PACKAGE / "README.md"
LAW = ROOT / "Законодательная база/Конституционный закон «О судебной системе штата Сан-Андреас».json"


class Case105CourtOrdersTests(unittest.TestCase):
    def test_user_transcription_is_separate_from_verified_source(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(text.count("## Документ "), 4)
        self.assertIn("текст и актуальность судебных актов независимо не проверены", text)
        self.assertIn("post-11849106", text)
        self.assertIn("календарная дата и часовой пояс этой отметки отдельно не подтверждены", text)
        for fragment in (
            "## Документ 1 (Определение № 105-2, стр. 1 из 2)",
            "## Документ 2 (Определение № 105-2, стр. 2 из 2)",
            "## Документ 3 (Определение № 105-3, стр. 1 из 2)",
            "## Документ 4 (Определение № 105-3, стр. 2 из 2)",
            "21.11.2026 в 13:19:35 UTC", "Приобщение не означает подтверждения изложенных фактов",
            "26 ноября 2026 года в 10:00 по времени штата Сан-Андреас",
            "Факт неявки и надлежащего извещения подлежит проверке в назначенное время",
            "ранее вынесенные судебные запросы",  # регистр нормализуется ниже
            "До разрешения иска по существу отдельно рассмотреть",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment.casefold(), text.casefold())

    def test_earlier_request_is_not_overwritten_by_written_procedure_deadline(self):
        text = GUIDANCE.read_text(encoding="utf-8")
        for fragment in (
            "26.11.2026 в 10:00 по времени штата Сан-Андреас",
            "до начала рассмотрения", "Запрос по определению № 105-1",
            "не отменён и не продлён", "48 часов с момента получения запроса",
            "23.11.2026 в 15:58", "25.11.2026 в 15:58 — условный ориентир",
            "только если это одновременно время официального получения запроса Сенатом",
            "не заменяйте его сроком 26.11",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_five_hour_motion_rule_has_its_own_conditional_time(self):
        law = json.loads(LAW.read_text(encoding="utf-8"))
        article = next(section["text"] for section in law["sections"]
                       if section["title"].strip() == "Статья 45.")
        self.assertIn("не позднее, чем за пять часов", article)
        self.assertIn("приобщении материалов", article)
        self.assertIn("суд вправе оставить ходатайство без рассмотрения", article)
        start = datetime(2026, 11, 26, 10, 0)
        self.assertEqual(start - timedelta(hours=5), datetime(2026, 11, 26, 5, 0))
        for path in (GUIDANCE, PACKAGE / "00 Перед подачей.md", CASE / "06 Перед подачей.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("05:00", text)
                self.assertIn("10:00", text)
                self.assertIn("если", text.lower())
                self.assertIn("письменн", text.lower())
                self.assertIn("суд вправе оставить", text.lower())

    def test_filings_account_for_new_orders_without_fictitious_absence_or_waiver(self):
        for path in (RESPONSE, OBJECTIONS):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("№ 105-2", text)
                self.assertIn("№ 105-3", text)
                self.assertIn("post-11849106", text)
                self.assertIn("[CENTER][B]В Верховный Суд", text)
                self.assertIn("Marcus Nomad", text)
                self.assertIn("Дата подачи: 25.11.2026", text)
                self.assertIn("Подпись: Nomad", text)
                self.assertNotRegex(text.lower(), r"прошу[^.\n]{0,120}рассмотреть[^.\n]{0,120}в мо[её] отсутствие")
                self.assertNotIn("заседание отменено", text.lower())
                assert_balanced_bbcode(self, text)
        response = RESPONSE.read_text(encoding="utf-8")
        self.assertIn("26 ноября 2026 года в 10:00", response)
        self.assertIn("Вопрос о заочном производстве без заслушивания сторон разрешается при наличии", response)
        self.assertIn("не подтверждает полномочий представлять Сенат", response)
        self.assertEqual(len(re.findall(r"\{\{[^{}]+\}\}", response)), 4)
        # Пункт 3 определения № 105-1 называет конкретные материалы дела № 97,
        # а не истребует весь комплект дела.
        self.assertIn("полный текст решения, первоначальный иск, определения от 12 и 19.11", response)
        self.assertNotIn("Полный комплект дела № 97 истребован", response)
        self.assertIn("не является автоматически просьбой", GUIDANCE.read_text(encoding="utf-8"))

    def test_objections_assess_claimants_timing_and_burden_fairly(self):
        text = OBJECTIONS.read_text(encoding="utf-8")
        for fragment in (
            "части 5 статьи 32", "обязанность доказывания законности",
            "Часть 2 статьи 25", "общий срок исковой давности 48 часов", "Части 6 и 7 статьи 31.1",
            "21.11.2026 в 13:19:35 UTC", "принято к сведению и подлежит проверке",
            "Истец ссылается на обращение по делу № 97", "не устанавливает автоматического приостановления срока",
            "Дополнительные обстоятельства, препятствовавшие своевременной подаче каждого требования",
            "отдельно по каждому требованию", "Не прошу автоматически считать все требования за эту дату просроченными",
            "до рассмотрения соответствующего требования по существу",
            "При установленном пропуске и отсутствии причин, признанных судом уважительными",
            "отказать в восстановлении срока по соответствующему требованию",
            "Период, к которому относится эта характеристика", "моментом её исполнения",

        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
