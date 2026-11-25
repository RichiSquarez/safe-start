# -*- coding: utf-8 -*-
"""Render the campaign material: Instagram post, A4 poster, one page parent guide.

Everything is drawn as vectors and rasterised at the end. The phone screen is
drawn by hand (home_screen) instead of pasting a device screenshot, so the
material stays crisp and shows the tiles the way the product presents them.
"""
import os
import pymupdf as fitz
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "campaign")
ICONS = os.path.join(ROOT, "app", "res", "drawable-xxhdpi")
LOGO = os.path.join(ROOT, "brand", "safestart-symbol.png")


def C(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


PETROL = C("173B4D")
DEEP = C("0B2230")
TEAL = C("116B65")
TEAL2 = C("2BB98A")
PAPER = C("F7FAF8")
MINT = C("DDF1E9")
MINT2 = C("C8E2D8")
PEACH = C("FFD19A")
BODY = C("49636B")
MUTED = C("6E8586")
WHITE = C("FFFFFF")
DARKBODY = C("C5D8D8")
OLIVE = C("8A5A1F")

F = {False: fitz.Font("helv"), True: fitz.Font("hebo")}
_tint = {}
_glow = {}


# ----------------------------------------------------------------- painters
def tinted(name, rgb):
    key = (name, rgb)
    if key in _tint:
        return _tint[key]
    im = Image.open(os.path.join(ICONS, "ic_%s.png" % name)).convert("RGBA")
    px = im.load()
    r, g, b = [int(round(v * 255)) for v in rgb]
    w, h = im.size
    for y in range(h):
        for x in range(w):
            a = px[x, y][3]
            if a:
                px[x, y] = (r, g, b, a)
    p = os.path.join(OUT, "tint", "%s_%02X%02X%02X.png" % (name, r, g, b))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    _tint[key] = p
    return p


def glow_src(rgb, alpha=1.0):
    """Small radial falloff PNG used as a soft background light."""
    key = (rgb, round(alpha, 2))
    if key in _glow:
        return _glow[key]
    n = 160
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = im.load()
    r, g, b = [int(round(v * 255)) for v in rgb]
    cx = cy = (n - 1) / 2.0
    for y in range(n):
        for x in range(n):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / cx
            if d >= 1.0:
                continue
            a = (1.0 - d) ** 2.1 * alpha
            px[x, y] = (r, g, b, int(round(a * 255)))
    p = os.path.join(OUT, "tint", "glow_%02X%02X%02X_%d.png"
                     % (r, g, b, int(alpha * 100)))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)
    _glow[key] = p
    return p


def glow(page, cx, cy, r, color, alpha=0.5):
    page.insert_image(fitz.Rect(cx - r, cy - r, cx + r, cy + r),
                      filename=glow_src(color, alpha))


def tw(text, size, bold=False):
    return F[bold].text_length(text, fontsize=size)


def tracked(page, x, y, text, size, color, bold=True, tr=0.0):
    f = F[bold]
    for ch in text:
        page.insert_text((x, y), ch, fontname="hebo" if bold else "helv",
                         fontsize=size, color=color)
        x += f.text_length(ch, fontsize=size) + tr
    return x


def wrap(text, size, width, bold=False):
    out, cur = [], ""
    for wd in text.split(" "):
        trial = wd if not cur else cur + " " + wd
        if tw(trial, size, bold) <= width or not cur:
            cur = trial
        else:
            out.append(cur)
            cur = wd
    if cur:
        out.append(cur)
    return out


def para(page, x, y, w, text, size, color, bold=False, lh=1.35):
    for ln in wrap(text, size, w, bold):
        page.insert_text((x, y), ln, fontname="hebo" if bold else "helv",
                         fontsize=size, color=color)
        y += size * lh
    return y


def vgrad(page, x0, y0, x1, y1, c0, c1, bands=260):
    for i in range(bands):
        t = i / (bands - 1.0)
        col = tuple(c0[j] + (c1[j] - c0[j]) * t for j in range(3))
        page.draw_rect(fitz.Rect(x0, y0 + (y1 - y0) * i / bands,
                                 x1, y0 + (y1 - y0) * (i + 1) / bands + 0.8),
                       color=None, fill=col)


def card(page, rect, fill, radius=0.06, line=None, lw=1.2, opacity=None):
    kw = {}
    if opacity is not None:
        kw["fill_opacity"] = opacity
    page.draw_rect(fitz.Rect(*rect), color=line, fill=fill, width=lw,
                   radius=radius, **kw)


def pill(page, rect, fill, line=None, lw=1.4, radius=None):
    r = radius if radius is not None else 0.5
    page.draw_rect(fitz.Rect(*rect), color=line, fill=fill, width=lw, radius=r)


def dot(page, x, y, r, color):
    page.draw_circle((x, y), r, color=None, fill=color)


def chip(page, x, y, s, fill, icon, tint, ratio=0.54, radius=0.30):
    page.draw_rect(fitz.Rect(x, y, x + s, y + s), color=None, fill=fill, radius=radius)
    isz = s * ratio
    page.insert_image(fitz.Rect(x + (s - isz) / 2, y + (s - isz) / 2,
                                x + (s - isz) / 2 + isz, y + (s - isz) / 2 + isz),
                      filename=tinted(icon, tint))


def logo(page, x, y, s, plate=True):
    if plate:
        page.draw_rect(fitz.Rect(x - s * 0.16, y - s * 0.16, x + s * 1.16, y + s * 1.16),
                       color=None, fill=WHITE, radius=0.26)
    page.insert_image(fitz.Rect(x, y, x + s, y + s), filename=LOGO)


def eyebrow(page, x, y, text, size, color, accent=None, tr=2.6):
    if accent:
        dot(page, x + size * 0.24, y - size * 0.30, size * 0.24, accent)
        x += size * 0.8
    return tracked(page, x, y, text, size, color, True, tr)


def fit(text, size, width, bold=True, floor=40):
    """Shrink a single line until it fits width."""
    while size > floor and tw(text, size, bold) > width:
        size -= 1
    return size


# ----------------------------------------------------------------- phone screen
TILES = [("phone", "Ring", "Alltid tilgjengelig", TEAL2, WHITE, True),
         ("sms", "Meldinger", "Til kjente", C("C3D8F7"), PETROL, False),
         ("camera", "Kamera", "Ta bilder", C("DACCF3"), C("4B3F72"), False),
         ("map", "Kart", "Se hvor du er", C("CBE8C1"), C("2C5F3A"), False),
         ("bus", "Skyss", "Bussbillett", C("C2E5F1"), C("1F5C6B"), False),
         ("chess", "Sjakk", "Mot en bot", C("F1E2C8"), C("6B4F1F"), False)]


def home_screen(page, x, y, w):
    """Draw the Safestart home screen into the box (x, y, w), 9:16 aspect."""
    s = w / 360.0
    h = w * 16 / 9.0

    def X(v):
        return x + v * s

    def Y(v):
        return y + v * s

    def S(v):
        return v * s

    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=None, fill=PAPER)
    glow(page, X(330), Y(30), S(220), MINT2, 0.55)
    glow(page, X(20), Y(560), S(200), MINT2, 0.40)
    glow(page, X(300), Y(620), S(170), PEACH, 0.22)

    # status pill
    pill(page, (X(224), Y(12), X(344), Y(44)), WHITE)
    page.insert_text((X(234), Y(35)), "12:28", fontname="hebo", fontsize=S(15), color=PETROL)
    tracked(page, X(292), Y(33), "LÅST", S(6.6), MUTED, True, S(0.3))
    page.insert_image(fitz.Rect(X(322), Y(23), X(333), Y(34)), filename=tinted("lock", TEAL2))

    # shield + wordmark
    chip(page, X(16), Y(16), S(26), PETROL, "shield", WHITE, 0.58, 0.28)
    page.insert_text((X(48), Y(35)), "Safestart", fontname="hebo", fontsize=S(15), color=PETROL)

    page.insert_text((X(16), Y(96)), "Hei!", fontname="hebo", fontsize=S(30), color=PETROL)
    page.insert_text((X(16), Y(114)), "Hva vil du gjøre?", fontname="helv", fontsize=S(12),
                     color=MUTED)

    cols = [16, 187]
    rows = [130, 250, 370]
    cw, chh = 157, 110
    for i, (icon, label, sub, fill, tint, always) in enumerate(TILES):
        cx = X(cols[i % 2])
        cy = Y(rows[i // 2])
        card(page, (cx, cy, cx + S(cw), cy + S(chh)), WHITE, 0.16,
             line=MINT2 if always else C("E7F0EB"), lw=max(0.8, S(1.1)))
        chip(page, cx + S(10), cy + S(9), S(30), fill, icon, tint, 0.56, 0.30)
        # little arrow affordance
        page.draw_circle((cx + S(cw - 20), cy + S(24)), S(10), color=None,
                         fill=(0.09, 0.23, 0.30), fill_opacity=0.06)
        page.insert_image(fitz.Rect(cx + S(cw - 26), cy + S(18), cx + S(cw - 14), cy + S(30)),
                          filename=tinted("arrow", PETROL))
        page.insert_text((cx + S(10), cy + S(74)), label, fontname="hebo",
                         fontsize=S(13.5), color=PETROL)
        page.insert_text((cx + S(10), cy + S(90)), sub, fontname="helv",
                         fontsize=S(8.6), color=TEAL if always else BODY)

    # Mamma & Pappa
    card(page, (X(16), Y(492), X(344), Y(544)), C("FFD9AB"), 0.16)
    chip(page, X(26), Y(502), S(30), PEACH, "heart", OLIVE, 0.55, 0.30)
    page.insert_text((X(64), Y(517)), "Mamma & Pappa", fontname="hebo",
                     fontsize=S(12.5), color=PETROL)
    page.insert_text((X(64), Y(532)), "Ett trykk ringer hjem", fontname="helv",
                     fontsize=S(8.4), color=OLIVE)
    page.insert_image(fitz.Rect(X(322), Y(510), X(332), Y(520)), filename=tinted("lock", OLIVE))

    # footer
    card(page, (X(16), Y(556), X(344), Y(586)), WHITE, 0.18, line=MINT2, lw=max(0.6, S(0.9)))
    page.insert_image(fitz.Rect(X(26), Y(565), X(38), Y(577)), filename=tinted("shield", TEAL))
    dot(page, X(46), Y(571), S(2.4), PEACH)
    page.insert_text((X(54), Y(576)), "Telefonen virker alltid.", fontname="helv",
                     fontsize=S(8.4), color=BODY)
    page.insert_image(fitz.Rect(X(324), Y(566), X(333), Y(575)),
                      filename=tinted("lock", (0.4, 0.52, 0.53)))
    return h


def phone(page, x, y, w, frame=True):
    """Phone with a drawn Safestart screen inside."""
    fw = max(5, w * 0.028) if frame else 0
    if frame:
        page.draw_rect(fitz.Rect(x - fw, y - fw, x + w + fw, y + w * 16 / 9 + fw),
                       color=None, fill=WHITE, radius=0.072)
        page.draw_rect(fitz.Rect(x - fw, y - fw, x + w + fw, y + w * 16 / 9 + fw),
                       color=C("D7E7E1"), width=max(0.8, w * 0.004), radius=0.072)
    return home_screen(page, x, y, w)


# ----------------------------------------------------------------- instagram 4:5
def instagram(path):
    W, H = 1080, 1350
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    page.draw_rect(fitz.Rect(0, 0, W, H), color=None, fill=PAPER)

    HERO = 812
    vgrad(page, 0, 0, W, HERO, C("1B4457"), DEEP)
    glow(page, 960, 90, 380, MINT2, 0.30)
    glow(page, 60, 700, 300, TEAL2, 0.16)

    logo(page, 60, 56, 92)
    tracked(page, 182, 120, "SAFESTART", 31, WHITE, True, 3.4)

    eyebrow(page, 62, 236, "FØRSTE MOBIL  ·  BERGEN", 24, PEACH, accent=PEACH)

    hs = fit("Du har allerede", 92, 600)
    page.insert_text((60, 330), "Du har allerede", fontname="hebo", fontsize=hs, color=WHITE)
    page.insert_text((60, 330 + hs * 1.04), "mobilen.", fontname="hebo", fontsize=hs, color=WHITE)

    para(page, 62, 540, 520, "Gammel mobil, låst til det den skal kunne. "
         "Foreldrene har koden.", 29, DARKBODY, lh=1.42)

    pill(page, (62, 646, 404, 706), (0.06, 0.19, 0.25), line=TEAL2, lw=1.8)
    dot(page, 84, 676, 5, TEAL2)
    tracked(page, 100, 682, "INGEN NETTLESER", 20, MINT2, True, 2.0)

    phone(page, 640, 392, 370)

    rows = [("phone", "Ring er alltid tilgjengelig", "Kan ikke slås av"),
            ("sms", "Meldinger til kjente", "Ingen sosiale medier"),
            ("bus", "Kart og Skyss", "Kom seg hjem selv")]
    yy = 878
    for icon, t, sub in rows:
        chip(page, 62, yy - 46, 80, MINT, icon, TEAL, 0.54, 0.32)
        page.insert_text((170, yy - 6), t, fontname="hebo", fontsize=33, color=PETROL)
        page.insert_text((170, yy + 30), sub, fontname="helv", fontsize=24, color=BODY)
        yy += 106

    pill(page, (62, 1150, 1018, 1250), PEACH, radius=0.20)
    page.insert_text((100, 1200), "Mobilkveld for FAU", fontname="hebo", fontsize=41, color=PETROL)
    page.insert_text((100, 1234), "Vi setter opp mange mobiler på én kveld.", fontname="helv",
                     fontsize=24, color=OLIVE)
    page.draw_line(fitz.Point(62, 1284), fitz.Point(1018, 1284), color=MINT2, width=1.4)
    page.insert_text((62, 1318), "Safestart UB · Amalie Skram vgs, Bergen", fontname="helv",
                     fontsize=21, color=BODY)
    right = "Første mobil. På deres premisser."
    page.insert_text((1018 - tw(right, 21), 1318), right, fontname="helv", fontsize=21, color=TEAL)
    write(doc, path)


# ----------------------------------------------------------------- plakat A4
def plakat(path):
    W, H = 1240, 1754
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    page.draw_rect(fitz.Rect(0, 0, W, H), color=None, fill=PAPER)

    HERO = 780
    vgrad(page, 0, 0, W, HERO, C("1B4457"), DEEP)
    glow(page, 1080, 60, 420, MINT2, 0.30)
    glow(page, 40, 700, 320, TEAL2, 0.14)

    logo(page, 76, 62, 104)
    tracked(page, 208, 136, "SAFESTART  UB", 30, WHITE, True, 3.6)

    eyebrow(page, 78, 282, "FØRSTE MOBIL  ·  BERGEN", 26, PEACH, accent=PEACH)

    hs = fit("Skuffemobilen.", 152, 1088)
    page.insert_text((74, 424), "Skuffemobilen.", fontname="hebo", fontsize=hs, color=WHITE)
    ss = fit("Den ligger allerede der.", 62, 1088)
    page.insert_text((78, 424 + ss * 1.42), "Den ligger allerede der.", fontname="hebo",
                     fontsize=ss, color=PEACH)
    para(page, 78, 596, 660,
         "Vi gjør mobilen dere har lagt bort om til en trygg førstemobil: ringe, "
         "sende melding, ta bilde, bruke kart og Skyss.", 30, DARKBODY, lh=1.42)

    # left: three steps
    tracked(page, 78, 856, "SLIK GJØR VI DET", 25, TEAL, True, 2.8)
    steps = [("01", "Ta med mobilen", "Vi sjekker hva den kan brukes til."),
             ("02", "Vi setter den opp", "Sletting, låsing og flatene dere velger."),
             ("03", "Ta den i bruk", "Foreldrene beholder PIN-koden.")]
    yy = 892
    for n, t, d in steps:
        card(page, (76, yy, 690, yy + 132), WHITE, 0.10, line=MINT2, lw=1.5)
        page.draw_rect(fitz.Rect(76, yy, 82, yy + 132), color=None, fill=TEAL)
        page.insert_text((110, yy + 50), n, fontname="hebo", fontsize=29, color=TEAL)
        page.insert_text((168, yy + 54), t, fontname="hebo", fontsize=37, color=PETROL)
        page.insert_text((168, yy + 96), d, fontname="helv", fontsize=26, color=BODY)
        yy += 150

    card(page, (76, 1352, 690, 1512), PETROL, 0.12)
    page.insert_text((112, 1408), "Mobilkveld for FAU", fontname="hebo", fontsize=42, color=WHITE)
    para(page, 112, 1444, 540, "Vi setter opp mange mobiler på én kveld.", 26, DARKBODY, lh=1.3)

    phone(page, 760, 848, 372)

    page.draw_line(fitz.Point(76, 1620), fitz.Point(1164, 1620), color=MINT2, width=1.6)
    page.insert_image(fitz.Rect(76, 1644, 136, 1704), filename=LOGO)
    page.insert_text((156, 1682), "Safestart UB · Amalie Skram vgs, Bergen", fontname="helv",
                     fontsize=24, color=BODY)
    right = "Første mobil. På deres premisser."
    page.insert_text((1164 - tw(right, 24), 1682), right, fontname="helv", fontsize=24, color=TEAL)
    write(doc, path)


# ----------------------------------------------------------------- guide A4
def guide(path):
    W, H = 1240, 1754
    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    page.draw_rect(fitz.Rect(0, 0, W, H), color=None, fill=PAPER)
    page.draw_rect(fitz.Rect(0, 0, W, 16), color=None, fill=PETROL)

    logo(page, 76, 62, 84)
    tracked(page, 182, 122, "SAFESTART", 32, PETROL, True, 3.4)
    pill(page, (856, 74, 1164, 132), MINT)
    tracked(page, 890, 112, "ETT ARK TIL FORELDRE", 21, TEAL, True, 2.2)

    page.insert_text((72, 268), "Slik er mobilen", fontname="hebo", fontsize=94, color=PETROL)
    page.insert_text((72, 356), "satt opp.", fontname="hebo", fontsize=94, color=PETROL)
    para(page, 76, 410, 760,
         "Dette arket forklarer hva barnet kan bruke mobilen til, og hva dere "
         "bestemmer. Ta vare på PIN-koden.", 27, BODY, lh=1.4)

    # left card: what the child can use
    card(page, (76, 478, 620, 1096), WHITE, 0.04, line=MINT2, lw=1.5)
    tracked(page, 112, 528, "BARNET KAN", 23, TEAL, True, 2.6)
    items = [("phone", "Ring", "Alltid tilgjengelig"),
             ("sms", "Meldinger", "Til kjente nummer"),
             ("camera", "Kamera", "Ta bilder"),
             ("map", "Kart", "Se hvor du er"),
             ("bus", "Skyss", "Bussbillett"),
             ("chess", "Sjakk", "Spill mot en bot")]
    yy = 586
    for icon, t, d in items:
        chip(page, 112, yy - 40, 66, MINT, icon, TEAL, 0.56, 0.32)
        page.insert_text((200, yy + 2), t, fontname="hebo", fontsize=31, color=PETROL)
        page.insert_text((200, yy + 33), d, fontname="helv", fontsize=23, color=BODY)
        yy += 82

    # right card: what parents control
    card(page, (648, 478, 1164, 1096), MINT, 0.04)
    tracked(page, 684, 528, "DERE BESTEMMER", 23, TEAL, True, 2.6)
    rows = [("lock", "PIN-koden", "Dere er de eneste som kommer inn i innstillingene."),
            ("shield", "Hvilke flater", "Slå av og på det barnet får bruke."),
            ("phone", "Mamma & Pappa", "Ett trykk ringer hjem."),
            ("arrow", "Ny mobil", "Samme oppsett på hver mobil dere tar med.")]
    yy = 586
    for icon, t, d in rows:
        chip(page, 684, yy - 40, 62, WHITE, icon, PETROL, 0.56, 0.32)
        page.insert_text((760, yy + 2), t, fontname="hebo", fontsize=30, color=PETROL)
        para(page, 760, yy + 34, 360, d, 23, BODY, lh=1.3)
        yy += 120

    # pin strip
    card(page, (76, 1124, 1164, 1318), PEACH, 0.10)
    tracked(page, 112, 1170, "SLIK LÅSER DERE OPP", 23, PETROL, True, 2.6)
    steps = [("1", "Hold fingeren", "på logoen i tre sekunder"),
             ("2", "Skriv PIN", "fire siffer, deres kode"),
             ("3", "Velg flater", "slå av, på eller bytt PIN")]
    xs = 112
    for n, t, d in steps:
        page.draw_circle((xs + 25, 1230), 25, color=None, fill=PETROL)
        page.insert_text((xs + 17, 1240), n, fontname="hebo", fontsize=25, color=WHITE)
        page.insert_text((xs + 64, 1220), t, fontname="hebo", fontsize=29, color=PETROL)
        page.insert_text((xs + 64, 1254), d, fontname="helv", fontsize=21, color=OLIVE)
        xs += 352

    # one screen + a short checklist
    tracked(page, 76, 1352, "SLIK SER DET UT", 23, TEAL, True, 2.6)
    card(page, (72, 1372, 72 + 164, 1372 + 150 * 16 / 9 + 22), WHITE, 0.05,
         line=MINT2, lw=1.2)
    home_screen(page, 76, 1376, 156)
    page.insert_text((76, 1376 + 156 * 16 / 9 + 22), "Hjem", fontname="helv",
                     fontsize=21, color=MUTED)

    card(page, (272, 1372, 1164, 1660), MINT, 0.05)
    tracked(page, 308, 1418, "FØR DEN TAS I BRUK", 21, TEAL, True, 2.4)
    checks = ["Ring et nummer fra mobilen og hør at det ringer.",
              "Prøv Mamma & Pappa-knappen sammen med barnet.",
              "Skru på Skyss, og logg inn sammen første gang."]
    yy = 1462
    for t in checks:
        page.draw_rect(fitz.Rect(308, yy - 16, 328, yy + 4), color=TEAL, width=1.8, radius=0.30)
        page.draw_line(fitz.Point(312, yy - 6), fitz.Point(316, yy - 1), color=TEAL, width=2.2)
        page.draw_line(fitz.Point(316, yy - 1), fitz.Point(324, yy - 12), color=TEAL, width=2.2)
        page.insert_text((350, yy), t, fontname="helv", fontsize=24, color=PETROL)
        yy += 62

    page.draw_line(fitz.Point(76, 1698), fitz.Point(1164, 1698), color=MINT2, width=1.4)
    page.insert_image(fitz.Rect(76, 1712, 118, 1754), filename=LOGO)
    page.insert_text((142, 1738), "Safestart UB · Amalie Skram vgs, Bergen", fontname="helv",
                     fontsize=21, color=BODY)
    right = "Første mobil. På deres premisser."
    page.insert_text((1164 - tw(right, 21), 1738), right, fontname="helv", fontsize=21, color=TEAL)
    write(doc, path)


def write(doc, path):
    tmp = path + ".pdf"
    doc.save(tmp, garbage=4, deflate=True)
    doc.close()
    src = fitz.open(tmp)
    pix = src[0].get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
    pix.save(path)
    src.close()
    os.remove(tmp)
    print("%-14s %dx%d" % (os.path.basename(path), pix.width, pix.height))


def main():
    os.makedirs(OUT, exist_ok=True)
    instagram(os.path.join(OUT, "instagram.png"))
    plakat(os.path.join(OUT, "plakat.png"))
    guide(os.path.join(OUT, "guide.png"))


if __name__ == "__main__":
    main()
