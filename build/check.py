# -*- coding: utf-8 -*-
"""Flag likely collisions: a text block that grows past the next element below it."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck import measure, wrap_text, fs
import slides as S

def text_bottom(e):
    y = e["y"] * 72
    maxw = e["w"] * 72 * 0.965
    for b in e["blocks"]:
        size = round(fs(b["size"]) * 2) / 2
        lh = size * b["lh"]
        n = 0
        for ch in b["t"].split("\n"):
            n += len(wrap_text(ch, size, b["bold"], maxw))
        y += n * lh + b["sa"]
    return y / 72

def hor_overlap(a, b):
    lo = max(a["x"], b["x"]); hi = min(a["x"] + a["w"], b["x"] + b["w"])
    if hi <= lo: return 0.0
    return (hi - lo) / min(a["w"], b["w"])

def check():
    bad = []
    for i, s in enumerate(S.build(), 1):
        for e in s.els:
            if e["k"] != "txt":
                continue
            bot = text_bottom(e)
            if bot > e["y"] + e["h"] + 0.03:
                bad.append((i, "TALL", round(e["y"], 2), round(bot, 2),
                            round(e["y"] + e["h"], 2), e["blocks"][0]["t"][:40]))
            if bot > 7.02:
                bad.append((i, "PH", round(e["y"], 2), round(bot, 2), e["blocks"][0]["t"][:44]))
            for o in s.els:
                if o is e or o["y"] <= e["y"] + 0.02:
                    continue
                if hor_overlap(e, o) < 0.55:
                    continue
                # only the nearest element below matters
                d = o["y"] - e["y"]
                if d > 3.2:
                    continue
                if bot > o["y"] + 0.03:
                    kind = "IMG" if o["k"] == "img" else ("BOX" if o["k"] == "rect" else "TXT")
                    bad.append((i, kind, round(e["y"], 2), round(bot, 2),
                                round(o["y"], 2), e["blocks"][0]["t"][:40]))
    seen = set(); out = []
    for b in sorted(bad):
        if b in seen: continue
        seen.add(b); out.append(b)
    for b in out:
        if b[1] not in ("PH", "TALL"):
            print(b)
    print("--- own-box overflows ---")
    for b in out:
        if b[1] == "TALL":
            print(b)
    print("issues:", len(out))

check()
