# -*- coding: utf-8 -*-
"""Один документ на акт: каждая правка — полная структурная единица."""
import os, re, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fulltext import article, chapter_line, build, sections, resolve

OUT = "Законопроекты 235–249 (по актам)"
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Законопроекты", OUT), exist_ok=True)

def A(f, n): return article(f, n)

def line(t, prefix, nth=0):
    hits = [l for l in t.split("\n") if l.startswith(prefix)]
    assert len(hits) > nth, (prefix, len(hits))
    return hits[nth]

def rep(text, pairs):
    for old, new in pairs:
        c = text.count(old)
        assert c == 1, "не уникально (%d): %r" % (c, old[:70])
        text = text.replace(old, new)
    return text

TOK = re.compile(r"\S+\s*|\s+")
def mark_diff(a, b):
    ta, tb = TOK.findall(a), TOK.findall(b)
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    L, R = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            L.append(("".join(ta[i1:i2]), None)); R.append(("".join(tb[j1:j2]), None))
        else:
            if i2 > i1: L.append(("".join(ta[i1:i2]), "R"))
            if j2 > j1: R.append(("".join(tb[j1:j2]), "G"))
    def emit(parts):
        out, cur, curmk = [], "", None
        for s, m in parts:
            if m != curmk and cur:
                out.append((cur, curmk)); cur = ""
            curmk = m; cur += s
        if cur: out.append((cur, curmk))
        return "".join(("[[%s]]%s[[/%s]]" % (m, s, m)) if m else s for s, m in out)
    return emit(L), emit(R)

def row(loc, left, right):
    head = (loc + "\n") if loc else ""
    if left is None:
        return (head + "В действующей редакции отсутствует.", head + "[[G]]" + right + "[[/G]]")
    L, R = mark_diff(left, right)
    return (head + L, head + R)

def new_act(loc, text):
    body = text
    for pref in (loc + ". ", loc + ".", loc):
        if body.startswith(pref):
            body = body[len(pref):].lstrip()
            break
    return (loc + "\nВ действующей редакции отсутствует.", loc + "\n" + "[[G]]" + body + "[[/G]]")
