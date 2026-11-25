# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck, slides

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(OUT, "build")
DECKDIR = os.path.join(OUT, "leveranse")
os.makedirs(DECKDIR, exist_ok=True)

sl = slides.build()
print("slides:", len(sl))

pptx_path = os.path.join(DECKDIR, "Safestart-UB-presentasjon.pptx")
deck.emit_pptx(sl, pptx_path)
print("pptx:", pptx_path, os.path.getsize(pptx_path))

pdf_path = os.path.join(BUILD, "preview.pdf")
deck.emit_preview(sl, pdf_path)
print("pdf ok")

pngs = deck.rasterize(pdf_path, os.path.join(BUILD, "png"), zoom=1.6)
print("pngs:", pngs)
