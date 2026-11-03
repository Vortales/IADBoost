# -*- coding: utf-8 -*-
"""ACT. 268: Закон о Секретной Службе, ст. 7 ч. 2 — передача задержанных и обыск жилых помещений."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fulltext import article, build, resolve

SS = os.path.basename(resolve("Закон “О деятельности Секретной Службы в штате San-Andreas”.json"))

OUT = "Законопроекты 266–269 (устранение коллизий)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "Законопроекты", OUT)
os.makedirs(DIR, exist_ok=True)

a7 = article(SS, "7")
lines = a7.split("\n")
head = lines[0]                      # «Статья 7.»
title = lines[1]                     # «Обязанности Секретной Службы»
p2 = [l for l in lines if l.startswith("ч. 2 ")][0]

TAIL = "охраняемых Секретной Службой штата San-Andreas."
assert p2.endswith(TAIL)

ADD = (" Задержанные лица передаются сотрудникам Федерального Расследовательского Бюро, "
       "Департамента Полиции города Лос-Сантос или Департамента Шерифа округа Блэйн. "
       "Обыск жилых помещений производится на основаниях и в порядке, предусмотренных "
       "Процессуальным кодексом штата San-Andreas.")

left = "Статья 7, ч. 2\n" + p2.replace(TAIL, "[[R]]" + TAIL + "[[/R]]", 1)
right = "Статья 7, ч. 2\n" + p2 + "[[G]]" + ADD + "[[/G]]"

rows = [(left, right)]

SECTION1 = (
    "Законопроект направлен на устранение правовой коллизии путем установления порядка передачи "
    "задержанных лиц и оснований проведения обыска жилых помещений Секретной Службой."
)

fname = "ACT.268.Закон о Секретной Службе (передача задержанных).docx"
subtitle = "о внесении изменений в Закон «О деятельности Секретной Службы в штате San-Andreas»"
build([("SECTION. 2. ВНЕСЕНИЕ ПРАВКИ В Закон «О деятельности Секретной Службы в штате San-Andreas»", rows)],
      os.path.join(DIR, fname), "ACT. 268", subtitle, SECTION1)
