# -*- coding: utf-8 -*-
"""Общие источники и адресные сравнительные фрагменты новых законопроектов.

Единственный источник действующих редакций - локальная законодательная база.
Исторические законопроекты не используются как действующее право.
"""
import billkit

PC = "Процессуальный кодекс штата Сан-Андреас"
PC_TITLE = "Процессуальный кодекс штата Сан-Андреас"
APP = "Приложение №1 к Уголовному кодексу штата Сан-Андреас О закрытых, охраняемых и особо охраня…"
APP_TITLE = "Приложение № 1 к Уголовному кодексу штата Сан-Андреас"
SANG = "Закон О Национальной Гвардии штата Сан-Андреас"
SANG_TITLE = "Закон «О Национальной Гвардии штата Сан-Андреас»"
AD = "Закон Об адвокатской деятельности и адвокатуре в штате Сан-Андреас"
AD_TITLE = "Закон «Об адвокатской деятельности и адвокатуре в штате Сан-Андреас»"
COURT = "Конституционный закон «О судебной системе штата Сан-Андреас»"
UK = "Уголовный Кодекс штата Сан-Андреас"
UK_TITLE = "Уголовный кодекс штата Сан-Андреас"


def clean(text):
    """Удаляет невидимый форумный символ и приводит тире к форме проекта."""
    return text.replace("\u200b", "").replace("—", "-").replace("–", "-")


def excerpt(section, start, end=None):
    """Извлекает единственный фрагмент исходной записи по неизменным границам."""
    if section.count(start) != 1:
        raise ValueError(f"Начало фрагмента не уникально: {start!r}")
    i = section.index(start)
    if end is None:
        result = section[i:]
    else:
        j = section.find(end, i + len(start))
        if j < 0:
            raise ValueError(f"Конец фрагмента не найден: {end!r}")
        result = section[i:j]
    return clean(result.strip())


def edited(act, locator, source, changes):
    """Строка с проверяемой исходной редакцией и цветными изменениями."""
    left, right = billkit.pair(source, changes)
    header = f"[[B]]{act}[[/B]]\n{locator}\n"
    return header + left, header + right


def new_part(act, locator, source, forbidden_marker, proposed):
    """Новая норма; проверяет, что она еще отсутствует в исходной редакции."""
    if forbidden_marker in source:
        raise ValueError(f"Норма уже существует: {act}, {locator}: {forbidden_marker}")
    header = f"[[B]]{act}[[/B]]\n{locator}\n"
    return (header + "В действующей редакции отсутствует.",
            header + "[[G]]" + proposed + "[[/G]]")
