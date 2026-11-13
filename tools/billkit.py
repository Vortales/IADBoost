# -*- coding: utf-8 -*-
"""Общие средства сборки законопроектов ACT. 289 и далее.

Образец структуры и содержания — ACT.260: номер, шапка Сената, дата,
«ЗАКОНОПРОЕКТ», предмет правки, SECTION 1 (суть в одном абзаце),
SECTION 2, таблица «настоящая редакция / предложенный вариант».

Разметка: [[R]]…[[/R]] — действующий текст (красный),
[[G]]…[[/G]] — новая редакция (зелёный).
"""
import json
import os
import re

ROOT = "/home/user/IADBoost"
BASE = os.path.join(ROOT, "Законодательная база")


def load(name):
    """Возвращает карту text по номеру записи для акта из «Законодательной базы»."""
    path = os.path.join(BASE, name if name.endswith(".json") else name + ".json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {s["n"]: (s["text"] or "") for s in data["sections"]}


def art(sec, n, with_punish=False):
    """Статья целиком; при with_punish — вместе с наказанием (следующая запись)."""
    head = sec[n].rstrip()
    if not with_punish:
        return head
    assert head.endswith("Наказание:"), head[-40:]
    return head[:-len("Наказание:")] + "Наказание:\n" + sec[n + 1].strip()


def pair(src, edits):
    """Собирает левую и правую колонки по списку правок.

    ("R", old, new) — замена; ("D", old, "") — удаление;
    ("I", anchor, text) — вставка после anchor (слева без изменений).
    """
    pos, left, right = 0, [], []
    for kind, old, new in edits:
        i = src.find(old, pos)
        if i < 0:
            raise ValueError("не найдено: %r" % old[:80])
        cut = i + len(old)
        left.append(src[pos:cut])
        right.append(src[pos:cut])
        if kind == "D":
            left[-1] = src[pos:i] + "[[R]]%s[[/R]]" % old
            if new:
                raise ValueError("D не принимает new")
        elif kind == "R":
            left[-1] = src[pos:i] + "[[R]]%s[[/R]]" % old
            if new:
                right[-1] = src[pos:i] + "[[G]]%s[[/G]]" % new
        elif kind == "I":
            if new:
                right[-1] = src[pos:cut] + "[[G]]%s[[/G]]" % new
        else:
            raise ValueError(kind)
        pos = cut
    left.append(src[pos:])
    right.append(src[pos:])
    return "".join(left), "".join(right)


HEAD = re.compile(r"^\s*Статья\s+(\d+(?:\.\d+)*)\.?\s*$")


def strip_head(src, locator=""):
    """Убирает заголовок статьи из начала текста: он уже назван в локаторе.

    «Статья 2.\nОбщее положение\n…» → «Общее положение\n…»;
    «Статья 2\n. Охраняемые объекты\n…» → «Охраняемые объекты\n…».
    """
    m = re.search(r"Статья\s+(\d+(?:\.\d+)*)", locator)
    lines = src.split("\n")
    if not m or not lines:
        return src
    h = HEAD.match(lines[0])
    if not h or h.group(1) != m.group(1):
        return src
    rest = lines[1:]
    if rest and rest[0].lstrip().startswith("."):
        rest[0] = rest[0].lstrip()[1:].lstrip()
    return "\n".join(rest).lstrip("\n")


def row(locator, src, edits, act=None):
    """Строка таблицы: локатор (при необходимости с названием акта) и обе колонки."""
    src = strip_head(src, locator)
    left, right = pair(src, edits)
    head = ("[[B]]%s[[/B]]\n" % act if act else "") + locator + "\n"
    return head + left, head + right


def bill(num, date, filename, subtitle, section1, section2, rows):
    return {
        "num": num,
        "date": date,
        "file": filename,
        "subtitle": subtitle,
        "section1": section1,
        "section2": section2,
        "rows": rows,
    }
