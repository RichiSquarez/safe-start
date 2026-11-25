# -*- coding: utf-8 -*-
"""Safestart UB — muntlig vurdering. Layout spec -> PPTX + preview PDF."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- palette
C = {
    "petrol": "173B4D",
    "petrol2": "0E2C3A",
    "teal": "116B65",
    "teal_d": "0B5752",
    "paper": "F7FAF8",
    "mint": "DDF1E9",
    "mint2": "C8E2D8",
    "peach": "FFD19A",
    "white": "FFFFFF",
    "ink": "173B4D",
    "body": "49636B",
    "body2": "526B70",
    "muted": "6E8586",
    "rule": "D9E8E3",
    "rule2": "DDE9E5",
    "darkbody": "C5D8D8",
    "darkmuted": "8FAEAE",
}

# Type scale: small text grows the most so nothing is unreadable when projected.
SCALE_STEPS = [(8, 1.55), (10, 1.48), (14, 1.30), (20, 1.22), (999, 1.16)]


def fs(size):
    """Final point size for a design size (before half-point rounding)."""
    for limit, k in SCALE_STEPS:
        if size < limit:
            return size * k
    return size * 1.16


W, H = 13.333, 7.5          # inches
ML = 0.78                    # left margin
MR = 0.78
CW = W - ML - MR             # content width


def col(v):
    """Accept palette name or literal hex."""
    return C[v] if v in C else v


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


# ---------------------------------------------------------------- elements
class Slide:
    def __init__(self, bg="paper", notes=""):
        self.bg = bg
        self.notes = notes
        self.els = []

    def rect(self, x, y, w, h, fill=None, line=None, lw=0.75, r=0.0, dash=None):
        self.els.append(dict(k="rect", x=x, y=y, w=w, h=h, fill=fill, line=line,
                             lw=lw, r=r, dash=dash))

    def img(self, path, x, y, w, h):
        self.els.append(dict(k="img", path=path, x=x, y=y, w=w, h=h))

    def txt(self, x, y, w, h, blocks, align="l"):
        for b in blocks:
            b.setdefault("size", 12)
            b.setdefault("bold", False)
            b.setdefault("color", "body")
            b.setdefault("sa", 0)
            b.setdefault("lh", 1.36)
            b.setdefault("tr", 0)
        self.els.append(dict(k="txt", x=x, y=y, w=w, h=h, blocks=blocks, align=align))


# ---------------------------------------------------------------- emitters
def emit_pptx(slides, path):
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    for s in slides:
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        bgfill = sl.background.fill
        bgfill.solid()
        bgfill.fore_color.rgb = RGBColor(*[int(c * 255) for c in hexrgb(col(s.bg))])
        for e in s.els:
            if e["k"] == "rect":
                shp = sl.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE if e["r"] > 0 else MSO_SHAPE.RECTANGLE,
                    Inches(e["x"]), Inches(e["y"]), Inches(e["w"]), Inches(e["h"]))
                if e["r"] > 0:
                    try:
                        shp.adjustments[0] = e["r"]
                    except Exception:
                        pass
                if e["fill"]:
                    shp.fill.solid()
                    shp.fill.fore_color.rgb = RGBColor(*[int(c * 255) for c in hexrgb(col(e["fill"]))])
                else:
                    shp.fill.background()
                if e["line"]:
                    shp.line.color.rgb = RGBColor(*[int(c * 255) for c in hexrgb(col(e["line"]))])
                    shp.line.width = Pt(e["lw"])
                    if e["dash"]:
                        from pptx.enum.dml import MSO_LINE_DASH_STYLE
                        shp.line.dash_style = MSO_LINE_DASH_STYLE.DASH
                else:
                    shp.line.fill.background()
                shp.shadow.inherit = False
                tf = shp.text_frame
                tf.text = ""
            elif e["k"] == "img":
                sl.shapes.add_picture(e["path"], Inches(e["x"]), Inches(e["y"]),
                                      Inches(e["w"]), Inches(e["h"]))
            else:
                tb = sl.shapes.add_textbox(Inches(e["x"]), Inches(e["y"]),
                                           Inches(e["w"]), Inches(e["h"]))
                tf = tb.text_frame
                tf.word_wrap = True
                tf.margin_left = 0
                tf.margin_right = 0
                tf.margin_top = 0
                tf.margin_bottom = 0
                tf.vertical_anchor = MSO_ANCHOR.TOP
                # disable autofit
                bodyPr = tf._txBody.bodyPr
                for tag in ("a:normAutofit", "a:spAutoFit"):
                    for el in bodyPr.findall(qn(tag)):
                        bodyPr.remove(el)
                bodyPr.append(bodyPr.makeelement(qn("a:noAutofit"), {}))
                first = True
                for b in e["blocks"]:
                    chunks = b["t"].split("\n")
                    for ci, ch in enumerate(chunks):
                        p = tf.paragraphs[0] if first else tf.add_paragraph()
                        first = False
                        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER,
                                       "r": PP_ALIGN.RIGHT, "j": PP_ALIGN.JUSTIFY}[e["align"]]
                        p.line_spacing = b["lh"]
                        p.space_after = Pt(b["sa"] if ci == len(chunks) - 1 else 0)
                        p.space_before = Pt(0)
                        r = p.add_run()
                        r.text = ch
                        f = r.font
                        f.name = "Helvetica Neue"
                        f.size = Pt(round(fs(b["size"]) * 2) / 2)
                        f.bold = b["bold"]
                        f.color.rgb = RGBColor(*[int(c * 255) for c in hexrgb(col(b["color"]))])
                        rPr = r._r.get_or_add_rPr()
                        if b["tr"]:
                            rPr.set("spc", str(int(b["tr"] * 100)))
        if s.notes:
            sl.notes_slide.notes_text_frame.text = s.notes
    prs.save(path)


FONT_R = pymupdf.Font("helv")
FONT_B = pymupdf.Font("hebo")


def measure(t, size, bold):
    return (FONT_B if bold else FONT_R).text_length(t, fontsize=size)


def wrap_text(t, size, bold, width):
    words = t.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if measure(trial, size, bold) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines


def emit_preview(slides, path, zoom=2.0):
    doc = pymupdf.open()
    for s in slides:
        page = doc.new_page(width=W * 72, height=H * 72)
        page.draw_rect(pymupdf.Rect(0, 0, W * 72, H * 72),
                       color=None, fill=hexrgb(col(s.bg)))
        for e in s.els:
            if e["k"] == "rect":
                rect = pymupdf.Rect(e["x"] * 72, e["y"] * 72,
                                    (e["x"] + e["w"]) * 72, (e["y"] + e["h"]) * 72)
                page.draw_rect(rect,
                               color=hexrgb(col(e["line"])) if e["line"] else None,
                               fill=hexrgb(col(e["fill"])) if e["fill"] else None,
                               width=e["lw"], radius=e["r"] if e["r"] else None,
                               dashes="[3 2] 0" if e["dash"] else None)
            elif e["k"] == "img":
                rect = pymupdf.Rect(e["x"] * 72, e["y"] * 72,
                                    (e["x"] + e["w"]) * 72, (e["y"] + e["h"]) * 72)
                page.insert_image(rect, filename=e["path"])
            else:
                y = e["y"] * 72
                maxw = e["w"] * 72 * 0.965
                for b in e["blocks"]:
                    size = round(fs(b["size"]) * 2) / 2
                    lh = size * b["lh"]
                    for ch in b["t"].split("\n"):
                        for ln in wrap_text(ch, size, b["bold"], maxw):
                            wdt = measure(ln, size, b["bold"])
                            x = e["x"] * 72
                            if e["align"] == "c":
                                x += (e["w"] * 72 - wdt) / 2
                            elif e["align"] == "r":
                                x += e["w"] * 72 - wdt
                            page.insert_text((x, y + size * 0.78), ln,
                                             fontname="hebo" if b["bold"] else "helv",
                                             fontsize=size, color=hexrgb(col(b["color"])))
                            y += lh
                    y += b["sa"]
    doc.save(path)
    return path


def rasterize(pdf, outdir, zoom=1.6):
    doc = pymupdf.open(pdf)
    os.makedirs(outdir, exist_ok=True)
    for i, pg in enumerate(doc):
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        pix.save(os.path.join(outdir, f"s{i + 1:02d}.png"))
    return len(doc)
