# -*- coding: utf-8 -*-
"""Campaign mock-ups for Safestart UB: one Instagram post and one stand poster.

Rendered with PyMuPDF so the deck can embed them as real images.
No invented facts: no price, no date, no URL, no promises beyond the guide.
"""
import os
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "brand", "safestart-symbol.png")
OUT = os.path.join(ROOT, "campaign")

PETROL = (0x17 / 255, 0x3B / 255, 0x4D / 255)
TEAL = (0x11 / 255, 0x6B / 255, 0x65 / 255)
PAPER = (0xF7 / 255, 0xFA / 255, 0xF8 / 255)
MINT = (0xDD / 255, 0xF1 / 255, 0xE9 / 255)
MINTL = (0xEE / 255, 0xF7 / 255, 0xF3 / 255)
MINTL2 = (0xE6 / 255, 0xF3 / 255, 0xED / 255)
PEACH = (0xFF / 255, 0xD1 / 255, 0x9A / 255)
WHITE = (1, 1, 1)
BODY = (0x49 / 255, 0x63 / 255, 0x6B / 255)
MUTED = (0x6E / 255, 0x85 / 255, 0x86 / 255)
RULE = (0xD9 / 255, 0xE8 / 255, 0xE3 / 255)


def text(page, x, y, s, size, font="helv", color=PETROL, tracking=0.0):
    """Draw one line, baseline at y. tracking in points per character."""
    if tracking:
        cx = x
        for ch in s:
            page.insert_text((cx, y), ch, fontname=font, fontsize=size, color=color)
            cx += fitz.get_text_length(ch, fontname=font, fontsize=size) + tracking
    else:
        page.insert_text((x, y), s, fontname=font, fontsize=size, color=color)


def width(s, size, font="helv"):
    return fitz.get_text_length(s, fontname=font, fontsize=size)


def para(page, x, y, s, size, maxw, font="helv", color=BODY, lh=1.45):
    """Naive word wrap; returns the y after the last line."""
    words, line, out = s.split(), "", []
    for w in words:
        trial = (line + " " + w).strip()
        if width(trial, size, font) <= maxw:
            line = trial
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    step = size * lh
    for i, ln in enumerate(out):
        page.insert_text((x, y + i * step), ln, fontname=font, fontsize=size, color=color)
    return y + (len(out) - 1) * step


def eyebrow(page, x, y, s, size=6.5, color=TEAL):
    page.draw_circle(fitz.Point(x + 1.6, y - 2.0), 1.6, color=None, fill=PEACH)
    text(page, x + 7.5, y, s, size, "hebo", color, tracking=1.1)


def logo(page, x, y, size):
    page.insert_image(fitz.Rect(x, y, x + size, y + size), filename=LOGO, keep_proportion=True)
    text(page, x + size + 9, y + size * 0.70, "Safestart", size * 0.52, "hebo", PETROL)


def ticks(page, x, y, items, size=10.5, gap=36):
    for i, t in enumerate(items):
        yy = y + i * gap
        page.draw_circle(fitz.Point(x + 5, yy - size * 0.32), 3.2, color=None, fill=PEACH)
        text(page, x + 17, yy, t, size, "helv", PETROL)


def pill(page, x, y, w, h, fill, r=18):
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=None, fill=fill,
                   radius=min(0.5, float(r) / min(w, h)))


def render(path, w, h, zoom, draw):
    doc = fitz.open()
    page = doc.new_page(width=w, height=h)
    page.draw_rect(page.rect, color=None, fill=PAPER)
    draw(page)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(path)
    doc.close()
    print("%s  %dx%d" % (os.path.relpath(path, ROOT), pix.width, pix.height))


# --------------------------------------------------------------- instagram 4:5
def instagram(page):
    W, H = page.rect.width, page.rect.height

    # soft mint blobs, solid tints so the PNG needs no alpha
    page.draw_circle(fitz.Point(W + 40, 60), 250, color=None, fill=MINTL)
    page.draw_circle(fitz.Point(-30, H + 60), 240, color=None, fill=(0xF4 / 255, 0xFA / 255, 0xF7 / 255))

    logo(page, 40, 38, 34)
    eyebrow(page, 42, 108, "F\u00d8RSTE MOBIL \u00b7 BERGEN")

    text(page, 40, 168, "Du har allerede", 40, "hebo", PETROL, tracking=-0.9)
    text(page, 40, 210, "mobilen.", 40, "hebo", PETROL, tracking=-0.9)

    para(page, 40, 250,
         "Vi gj\u00f8r skuffemobilen om til en trygg f\u00f8rstemobil. Ringe, SMS, kamera, "
         "kart og Skyss \u2014 uten sosiale medier og fritt nett.",
         11.5, 448, "helv", BODY, 1.55)

    ticks(page, 40, 326, [
        "Ring er alltid tilgjengelig",
        "Foreldrene setter opp og har PIN-koden",
        "Gammel mobil f\u00e5r nytt liv",
    ], 10.5, 34)

    pill(page, 40, 452, 460, 100, PEACH, 20)
    text(page, 62, 490, "MOBILKVELD FOR FAU", 12, "hebo", PETROL, tracking=0.6)
    para(page, 62, 514, "Vi setter opp mange mobiler p\u00e5 \u00e9n kveld, sammen med foreldrene.",
         9.5, 416, "helv", (0x8A / 255, 0x5A / 255, 0x1F / 255), 1.4)

    page.draw_rect(fitz.Rect(40, 600, W - 40, 600.7), color=None, fill=RULE)
    text(page, 40, 622, "Safestart UB \u00b7 Amalie Skram vgs, Bergen", 8.5, "helv", MUTED)
    text(page, W - 40 - width("F\u00f8rste mobil. P\u00e5 deres premisser.", 8.5), 622,
         "F\u00f8rste mobil. P\u00e5 deres premisser.", 8.5, "helv", MUTED)


# ------------------------------------------------------------------- A4 plakat
def plakat(page):
    W, H = page.rect.width, page.rect.height

    page.draw_circle(fitz.Point(W + 30, 90), 300, color=None, fill=MINTL)
    page.draw_circle(fitz.Point(-40, H + 20), 260, color=None, fill=(0xF4 / 255, 0xFA / 255, 0xF7 / 255))

    logo(page, 48, 46, 40)
    eyebrow(page, 50, 132, "SAFESTART UB \u00b7 AMALIE SKRAM VGS")

    text(page, 48, 226, "Skuffemobilen.", 58, "hebo", PETROL, tracking=-1.4)
    text(page, 48, 282, "Den ligger allerede der.", 23, "helv", TEAL, tracking=-0.4)

    para(page, 48, 330,
         "Vi gj\u00f8r en gammel mobil om til en trygg f\u00f8rstemobil: ringe, SMS, kamera, "
         "kart og Skyss. Foreldrene bestemmer hva barnet f\u00e5r, og f\u00e5r PIN-koden "
         "og en kort guide p\u00e5 ett ark.",
         13, 470, "helv", BODY, 1.55)

    ticks(page, 48, 432, [
        "Ring er alltid tilgjengelig",
        "Ingen sosiale medier, ikke fritt nett",
        "Foreldrene setter opp mobilen",
    ], 12.5, 40)

    pill(page, 48, 574, W - 96, 132, PETROL, 24)
    text(page, 76, 620, "Mobilkveld for FAU", 24, "hebo", WHITE, tracking=-0.4)
    para(page, 76, 648,
         "Vi kommer til skolen og setter opp mange mobiler p\u00e5 \u00e9n kveld. "
         "Foreldrene g\u00e5r hjem med ferdig telefon, PIN-kode og guide.",
         11.5, W - 152, "helv", (0xC5 / 255, 0xD8 / 255, 0xD8 / 255), 1.5)

    page.draw_rect(fitz.Rect(48, 790, W - 48, 790.7), color=None, fill=RULE)
    text(page, 48, 812, "Safestart UB \u00b7 Amalie Skram vgs, Bergen", 9, "helv", MUTED)
    text(page, W - 48 - width("F\u00f8rste mobil. P\u00e5 deres premisser.", 9), 812,
         "F\u00f8rste mobil. P\u00e5 deres premisser.", 9, "helv", MUTED)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    render(os.path.join(OUT, "instagram.png"), 540, 675, 1.6, instagram)
    render(os.path.join(OUT, "plakat.png"), 595, 842, 1.6, plakat)
