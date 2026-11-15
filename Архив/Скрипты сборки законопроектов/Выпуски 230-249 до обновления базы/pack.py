# -*- coding: utf-8 -*-
import json, os, sys, re
ROOT = "/home/user/IADBoost"
sys.path.insert(0, os.path.join(ROOT, "tools"))
from make_acts import build

OUT = os.path.join(ROOT, "Законопроекты")
DATE = "OCTOBER 21, 2026"

_cache = {}
def sec(f, n):
    key = (f, n)
    if key not in _cache:
        d = json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
        _cache[key] = {s["n"]: (s["text"] or "") for s in d["sections"]}
    return _cache[key][n]

def pair(text, old, new):
    """left/right with markers around the changed fragment"""
    if text.count(old) != 1:
        raise ValueError("fragment not unique (%d): %r" % (text.count(old), old[:60]))
    return (text.replace(old, "[[R]]%s[[/R]]" % old),
            text.replace(old, "[[G]]%s[[/G]]" % new))

def multi(text, pairs):
    left = text
    for old, new in pairs:
        left = left.replace(old, "[[R]]%s[[/R]]" % old, 1)
    right = text
    for old, new in pairs:
        right = right.replace(old, "[[G]]%s[[/G]]" % new, 1)
    return left, right

def cut(text, first, last=None):
    i = text.find(first)
    if i < 0: raise ValueError("не найдено: %r" % first[:50])
    j = len(text) if last is None else text.find(last, i)
    return text[i:j].rstrip()

def bill(num, fname, subtitle, section1, section2, rows):
    return {"num": str(num), "date": DATE, "file": fname, "subtitle": subtitle,
            "section1": section1, "section2": section2, "rows": rows}
