# -*- coding: utf-8 -*-
"""Content for Safestart UB deck."""
import os
from deck import (Slide, C, W, H, ML, MR, CW, ROOT)

LOGO = os.path.join(ROOT, "brand", "safestart-symbol.png")
TOTAL = 18


def eyebrow(s, x, y, t, color="teal", dot="peach", size=7.5):
    s.rect(x, y + 0.045, 0.055, 0.055, fill=dot, r=0.5)
    s.txt(x + 0.15, y, 6.5, 0.22,
          [{"t": t, "size": size, "bold": True, "color": color, "tr": 1.7}])


def footer(s, n, dark=False):
    c = "darkmuted" if dark else "muted"
    rule = "2B4E5F" if dark else "rule"
    s.rect(ML, 6.95, CW, 0.007, fill=rule)
    s.txt(ML, 7.05, 5, 0.2,
          [{"t": "SAFESTART UB", "size": 7, "bold": True, "color": c, "tr": 1.5}])
    s.txt(W - MR - 1.4, 7.05, 1.4, 0.2,
          [{"t": f"{n:02d} / {TOTAL}", "size": 7, "bold": True, "color": c, "tr": 1.2}],
          align="r")


def head(s, kicker, headline, dark=False, y=0.86, size=30, w=None, sub=None,
         sub_y=None, sub_color="body"):
    eyebrow(s, ML, 0.58, kicker, color="mint2" if dark else "teal")
    s.txt(ML, y, w or CW - 0.6, 1.3,
          [{"t": headline, "size": size, "bold": True,
            "color": "white" if dark else "petrol", "lh": 1.05, "tr": -size * 0.022}])
    if sub:
        s.txt(ML, sub_y or 1.72, w or CW - 1.6, 0.6,
              [{"t": sub, "size": 12.5, "color": sub_color, "lh": 1.45}])


def rule(s, y, x=ML, w=CW, color="rule"):
    s.rect(x, y, w, 0.007, fill=color)


# ------------------------------------------------------------------ 01 cover
def s01():
    s = Slide("paper", notes=(
        "Åpning (30 sek). «Vi heter Safestart UB. Vi selger ikke en telefon — vi selger en trygg overgang. "
        "Om fem minutter skal dere kunne gjenta ideen vår, og vite hva vi faktisk har belegg for.»"))
    eyebrow(s, ML, 0.72, "SAFESTART UB  ·  AMALIE SKRAM VGS  ·  BERGEN")
    s.txt(ML, 1.50, 8.3, 2.6, [
        {"t": "Første mobil.", "size": 51, "bold": True, "color": "petrol", "lh": 1.0, "tr": -1.4},
        {"t": "På deres premisser.", "size": 51, "bold": True, "color": "teal", "lh": 1.0, "tr": -1.4},
    ])
    s.txt(ML, 3.40, 7.6, 0.4,
          [{"t": "Muntlig vurdering i kommunikasjon og markedsføring", "size": 13, "color": "body"}])
    rule(s, 5.96)
    s.txt(ML, 6.14, 7.4, 0.9, [
        {"t": "Pavlo Larichev", "size": 11, "bold": True, "color": "petrol", "sa": 4},
        {"t": "Bærekraftig innovasjon  ·  Markedsundersøkelser  ·  Merkevarebygging  ·  Markedsføringskampanje",
         "size": 9.5, "color": "muted"},
    ])
    s.img(LOGO, 9.62, 1.42, 2.55, 2.55)
    s.txt(9.30, 4.28, 3.2, 1.0,
          [{"t": "En god start med mobilen dere allerede har.", "size": 10.5, "color": "muted",
            "lh": 1.4}], align="c")
    s.txt(W - MR - 1.9, 6.14, 1.9, 0.3,
          [{"t": "[dato]", "size": 9, "color": "muted"}], align="r")
    return s


# ------------------------------------------------------------------ 02 rød tråd
def s02():
    s = Slide("paper", notes=(
        "Rød tråd (40 sek). «Fire temaer, fire spørsmål. Hvert svar er forutsetningen for det neste: "
        "vi må vite hva ideen er, før vi kan undersøke markedet; vi må vite hva markedet sier, før vi kan "
        "posisjonere merkevaren; og først da kan vi lage en kampanje som treffer.»"))
    head(s, "RØD TRÅD", "Vi selger ikke en telefon.\nVi selger en trygg overgang.", size=33, y=0.86)
    s.txt(ML, 2.16, 9.4, 0.5,
          [{"t": "Fire temaer, ett spørsmål hver. Svaret i det ene temaet er forutsetningen for det neste.",
            "size": 12, "color": "body"}])
    rows = [
        ("01", "Bærekraftig innovasjon", "Hva er ideen — og hvorfor er den en innovasjon?", "idé og begrunnelse"),
        ("02", "Markedsundersøkelser", "Hva vet vi — og hvordan vet vi det?", "belegg"),
        ("03", "Merkevarebygging", "Hvordan skal foreldre forstå hvem vi er?", "posisjon"),
        ("04", "Markedsføringskampanje", "Hvordan når vi dem — og med hvilket budskap?", "handling"),
    ]
    y = 2.74
    rule(s, y, color="rule")
    for i, (n, tema, spm, tag) in enumerate(rows):
        yy = y + 0.12 + i * 0.82
        s.txt(ML, yy + 0.03, 0.5, 0.3, [{"t": n, "size": 9, "bold": True, "color": "teal", "tr": 1.2}])
        s.txt(ML + 0.55, yy, 3.0, 0.6, [{"t": tema, "size": 13.5, "bold": True, "color": "petrol", "lh": 1.2}])
        s.txt(ML + 3.65, yy + 0.01, 5.5, 0.6, [{"t": spm, "size": 11.5, "color": "body", "lh": 1.3}])
        s.txt(W - MR - 1.95, yy + 0.04, 1.95, 0.4,
              [{"t": tag, "size": 9, "bold": True, "color": "muted", "tr": 1.1}], align="r")
        rule(s, y + 0.82 + i * 0.82, color="rule")
    s.txt(ML, 6.28, CW, 0.35,
          [{"t": "Til sammen: en tjeneste som gjør en mobil familien allerede eier om til en trygg førstemobil.",
            "size": 11, "bold": True, "color": "teal"}])
    footer(s, 2)
    return s


# ------------------------------------------------------------------ team
def s_team():
    s = Slide("paper", notes=(
        "Teamet (35 sek). Vi er seks elever fra Amalie Skram, og alle har et ansvarsområde. "
        "Det er derfor vi kan levere både en enkelt mobil og en hel mobilkveld — det er ikke én person "
        "som gjør alt. Kort: hvem gjør hva."))
    head(s, "SAFESTART UB  /  TEAMET", "Seks personer, seks ansvar.")
    s.txt(ML, 2.06, 9.8, 0.5,
          [{"t": "Alle har et ansvarsområde. Derfor kan vi levere både en enkelt mobil og en hel mobilkveld.",
            "size": 11.5, "color": "body"}])
    team = [
        ("Isak Nesse", "DAGLIG LEDER", "Fremdrift, beslutninger og kontakt utad."),
        ("Ronja Branum", "INNKJØP OG SALG", "Tar imot mobiler, avtaler og levering."),
        ("Emil Storaas", "MARKED OG KOMMUNIKASJON", "Nettside, Instagram og materiell."),
        ("Emilie Lillefosse", "PERSONAL OG ØKONOMI", "Oppgaver, timer og regnskap."),
        ("Milena Belchenko", "ØKONOMI OG PRODUKSJON", "Kalkyle, pris og flyt i oppsettet."),
        ("Pavlo Larichev", "IT OG BÆREKRAFT", "Teknisk oppsett, kildekontroll og bærekraft."),
    ]
    for i, (name, role, what) in enumerate(team):
        x = ML + (i % 3) * 3.98
        y = 2.60 + (i // 3) * 1.94
        s.rect(x, y, 3.72, 1.66, fill="white", line="rule2", lw=0.75, r=0.03)
        s.txt(x + 0.30, y + 0.24, 3.2, 0.32, [{"t": role, "size": 7, "bold": True, "color": "teal", "tr": 1.5}])
        s.txt(x + 0.30, y + 0.52, 3.2, 0.35, [{"t": name, "size": 13, "bold": True, "color": "petrol"}])
        s.txt(x + 0.30, y + 0.92, 3.15, 0.7, [{"t": what, "size": 9, "color": "body", "lh": 1.42}])
    s.txt(ML, 6.46, CW, 0.3,
          [{"t": "Rollene følger ansvarsfordelingen i forretningsplanen vår.",
            "size": 8.5, "color": "muted"}])
    footer(s, 3)
    return s


# ------------------------------------------------------------------ 03 problem + tre steg
def s03():
    s = Slide("paper", notes=(
        "Tema 1, del 1 (60 sek). Problemet: foreldre vil ha kontakt og bussbillett, ikke fritt nett. "
        "Løsningen ligger ofte i skuffen hjemme. Deretter de tre trinnene — og understrek at foreldrene "
        "beholder PIN-koden: vi gir dem oversikt, ikke avhengighet."))
    head(s, "01 / BÆREKRAFTIG INNOVASJON", "Mobilen ligger allerede i skuffen.")
    s.txt(ML, 2.10, 5.5, 1.8, [
        {"t": "Mange foreldre vil at barnet skal kunne ringe hjem og kjøpe bussbillett — men ikke ha en "
              "smarttelefon med fritt nett og sosiale medier.", "size": 11, "color": "body", "lh": 1.5, "sa": 10},
        {"t": "Løsningen finnes ofte hjemme: en mobil familien har lagt bort.", "size": 11, "color": "body", "lh": 1.5},
    ])
    eyebrow(s, ML, 3.86, "KORT SAGT", color="teal")
    s.txt(ML, 4.08, 5.4, 1.05,
          [{"t": "Vi gjør skuffemobilen om til en trygg førstemobil.", "size": 21, "bold": True,
            "color": "petrol", "lh": 1.15, "tr": -0.45}])
    rule(s, 5.02, w=5.0)
    s.txt(ML, 5.12, 5.3, 0.95,
          [{"t": "Kunden betaler per mobil. FAU kan i tillegg kjøpe en mobilkveld der vi setter opp mange mobiler "
                "på én kveld.", "size": 10, "color": "muted", "lh": 1.5}])

    s.rect(6.98, 2.10, 5.57, 4.38, fill="mint", r=0.025)
    s.txt(7.42, 2.40, 4.6, 0.3, [{"t": "SLIK GJØR VI DET", "size": 7.5, "bold": True, "color": "teal", "tr": 1.7}])
    steps = [
        ("01", "Ta med mobilen", "Vi sjekker modell, oppdateringer og hva den faktisk kan brukes til."),
        ("02", "Vi setter den opp", "Sletting, låsing og de funksjonene dere velger — testet på den mobilen."),
        ("03", "Ta med oversikten hjem", "Foreldrene beholder PIN-koden og får en guide på ett ark."),
    ]
    for i, (n, t, d) in enumerate(steps):
        yy = 2.88 + i * 1.26
        s.txt(7.42, yy + 0.04, 0.4, 0.3, [{"t": n, "size": 9, "bold": True, "color": "teal", "tr": 1.2}])
        s.txt(7.86, yy, 4.2, 0.34, [{"t": t, "size": 12.5, "bold": True, "color": "petrol"}])
        s.txt(7.86, yy + 0.32, 4.25, 0.72, [{"t": d, "size": 10, "color": "body", "lh": 1.42}])
    footer(s, 3)
    return s

# ------------------------------------------------------------------ 04 prosess
def s04():
    s = Slide("paper", notes=(
        "Prosessen (60 sek). Vi laget ikke ideen i et vakuum: vi vurderte mange kandidater mot åtte krav og "
        "en terskel på 28 av 40 poeng. Restefrukt fikk 30, men ble parkert fordi Mattilsynet forbyr skadet frukt "
        "og to lag gjorde det samme i NM 2025. Vi valgte ideen med lavest risiko og høyest læring."))
    head(s, "01 / BÆREKRAFTIG INNOVASJON", "Fra mange ideer til én.")
    s.txt(ML, 2.18, 6.1, 1.3, [
        {"t": "Vi grillet hver idé mot åtte krav: dokumenterbart problem, prototype, tre bærekraftsdimensjoner, "
              "betalende kunde, partner, lav produksjonskostnad, skalerbarhet og kategorier. Terskelen var 28 av 40 poeng.",
         "size": 11, "color": "body", "lh": 1.5},
    ])
    ideas = [("Sorteringsskilt", 33), ("Bydelspass", 33), ("Restefrukt", 30),
             ("Bukettmansjett", 30), ("Sansemappe", 28)]
    scale = 2.55 / 40.0
    x0, bw = 2.62, 2.55
    s.rect(x0 + 28 * scale, 3.62, 0.008, 2.02, fill="mint2")
    s.txt(x0 + 28 * scale - 0.34, 3.38, 1.2, 0.2,
          [{"t": "terskel 28", "size": 7, "bold": True, "color": "muted"}])
    for i, (name, v) in enumerate(ideas):
        yy = 3.66 + i * 0.40
        s.txt(ML, yy - 0.02, 1.75, 0.3, [{"t": name, "size": 9.5, "color": "body"}])
        s.rect(x0, yy + 0.04, 2.62, 0.10, fill="mint")
        s.rect(x0, yy + 0.04, v * scale, 0.10, fill="teal")
        s.txt(x0 + 2.66, yy - 0.02, 0.5, 0.3,
              [{"t": str(v), "size": 9, "bold": True, "color": "petrol"}])
    yy = 3.66 + 5 * 0.40
    s.txt(ML, yy - 0.02, 1.75, 0.3, [{"t": "Skuffemobil", "size": 9.5, "bold": True, "color": "petrol"}])
    s.rect(x0, yy + 0.04, 2.62, 0.10, fill=None, line="mint2", lw=1.0, dash=True)
    s.txt(x0 + 2.66, yy - 0.02, 1.4, 0.3, [{"t": "valgt", "size": 9, "bold": True, "color": "teal"}])
    s.txt(ML, 6.42, 6.1, 0.25,
          [{"t": "Poengsummer fra idévurderingen 14.10.2026. Skuffemobilen ble valgt senere og er ikke scoret i samme skala.",
            "size": 7.5, "color": "muted", "lh": 1.3}])

    rule(s, 2.18, x=7.05, w=0.007, color="rule")
    s.rect(7.05, 2.18, 0.007, 4.1, fill="rule")
    s.txt(7.55, 2.18, 5.0, 0.3, [{"t": "HVORFOR SKUFFEMOBILEN VANT", "size": 7.5, "bold": True, "color": "teal", "tr": 1.6}])
    reasons = [
        ("Et område med mange fallgruver.", " Vi vil ta en helhetlig tilnærming til forretningen, ikke bare selge en duppeditt."),
        ("Vi tror på IT som verktøy.", " Vi mener vi kan levere dette, og interessen vår er faglig — ikke bare kreativ."),
        ("Problemet er ekte.", " Barn på nett er en reell risiko for foreldre. Vi tror på ideen, og det er derfor vi står her."),
    ]
    for i, (b, rest) in enumerate(reasons):
        yy = 2.60 + i * 1.02
        s.txt(7.55, yy, 0.45, 0.3, [{"t": f"0{i+1}", "size": 9, "bold": True, "color": "peach"}])
        s.txt(8.05, yy, 4.6, 0.85, [{"t": b + rest, "size": 10.5, "color": "body", "lh": 1.45}])
    s.rect(7.55, 5.66, 4.95, 0.74, fill="paper", line="mint2", lw=0.75)
    s.txt(7.74, 5.78, 4.55, 0.6,
          [{"t": "Vi har ikke dokumentert betalingsvilje, og vi har ingen avtale med FAU eller skolen ennå.",
            "size": 9, "color": "muted", "lh": 1.4}])
    footer(s, 4)
    return s


# ------------------------------------------------------------------ 05 innovasjon
def s05():
    s = Slide("paper", notes=(
        "Innovasjon (60 sek). Fagbegrepet: innovasjon er noe nytt som tas i bruk og skaper verdi. Vi har ingen "
        "ny teknologi — vi har en ny kombinasjon. Det er tjeneste-, prosess- og forretningsmodellinnovasjon, "
        "og den er inkrementell. Konsekvensen er at den er lett å kopiere — derfor må merkevaren bære."))
    head(s, "01 / BÆREKRAFTIG INNOVASJON", "Ny kombinasjon, ikke ny teknologi.")
    s.txt(ML, 2.12, 11.2, 0.4,
          [{"t": "Innovasjon er en ny idé som tas i bruk og skaper verdi. Vi spurte derfor: hva er egentlig nytt hos oss?",
            "size": 11, "color": "body"}])
    hdr = 2.60
    s.txt(ML, hdr, 3.2, 0.25, [{"t": "INNOVASJONSTYPE", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    s.txt(ML + 4.15, hdr, 1.0, 0.25, [{"t": "HOS OSS", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    s.txt(ML + 5.05, hdr, 6.0, 0.25, [{"t": "BEGRUNNELSE", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    rule(s, hdr + 0.24)
    rows = [
        ("Produktinnovasjon", "Nei", "Vi lager ingen ny mobil og ingen ny programvare.", False),
        ("Tjenesteinnovasjon", "Ja", "Oppsett, sletting, låsing og en guide blir en tjeneste familien kjøper.", True),
        ("Prosessinnovasjon", "Ja", "En standardisert rutine per modell: test, slett, lås, dokumenter.", True),
        ("Forretningsmodell", "Ja", "Betalt per mobil, pluss mobilkveld for FAU som ny kanal.", True),
    ]
    for i, (type_, ja, why, is_yes) in enumerate(rows):
        yy = hdr + 0.44 + i * 0.78
        s.txt(ML, yy, 3.9, 0.35, [{"t": type_, "size": 12, "bold": True, "color": "petrol"}])
        s.txt(ML + 4.15, yy, 0.9, 0.35,
              [{"t": ja, "size": 10, "bold": True, "color": "teal" if is_yes else "muted"}])
        s.txt(ML + 5.05, yy + 0.03, 6.9, 0.6, [{"t": why, "size": 10, "color": "body", "lh": 1.4}])
        rule(s, yy + 0.64)
    s.rect(ML, 6.04, CW, 0.66, fill="mint", r=0.03)
    s.txt(ML + 0.30, 6.12, CW - 0.60, 0.5, [
        {"t": "Inkrementell innovasjon: kjent teknologi, kjent råvare, nytt tilbud. Fordi den er lett å kopiere, "
              "må tillit og merkevare være forsvaret vårt.",
         "size": 10, "color": "petrol", "lh": 1.42}])
    footer(s, 5)
    return s

# ------------------------------------------------------------------ 06 bærekraft
def s06():
    s = Slide("paper", notes=(
        "Bærekraft (70 sek). Tre dimensjoner, og jeg er like ærlig på alle tre. Miljø: lengre brukstid er et "
        "anerkjent tiltak, men gevinsten er betinget — den finnes bare hvis mobilen erstatter et nykjøp. Vi har "
        "ikke målt utslipp, og oppgir derfor ingen klimabesparelse. Sosialt: foreldrekontroll er ikke full "
        "beskyttelse, og Skyss krever nett. Økonomi: ingen pris eller betalingsvilje er dokumentert."))
    head(s, "01 / BÆREKRAFTIG INNOVASJON", "Tre dimensjoner, tre ærlige svar.")
    cols = [
        ("MILJØ", "Lengre brukstid er et anerkjent miljøtiltak. Gevinsten er betinget: den oppstår bare hvis "
                  "mobilen erstatter et nykjøp. Vi har ikke målt utslipp, og oppgir derfor ingen klimabesparelse."),
        ("SOSIALT", "Barnet kan ringe hjem, og foreldrene velger funksjonene. Men foreldrekontroll gir ikke full "
                    "beskyttelse, og Skyss krever nett. Guiden forklarer grensene i stedet for å love mer."),
        ("ØKONOMISK", "Vi måler tid, materiell og reise per mobil og sammenligner med prisen kunden betaler. "
                      "Verken pris, betalingsvilje eller overskudd er dokumentert ennå."),
    ]
    hvad = ["Ingen klimagevinst før den er målt.",
            "Grensene forklares i guiden.",
            "Prisen settes etter at tid er målt."]
    xs = [ML, ML + 4.10, ML + 8.20]
    for i, (t, body) in enumerate(cols):
        x = xs[i]
        s.txt(x, 2.16, 3.6, 0.28, [{"t": f"0{i+1}", "size": 9, "bold": True, "color": "peach", "tr": 1.2}])
        s.txt(x, 2.42, 3.6, 0.32, [{"t": t, "size": 12.5, "bold": True, "color": "petrol", "tr": 0.9}])
        rule(s, 2.80, x=x, w=3.45)
        s.txt(x, 2.96, 3.5, 1.7, [{"t": body, "size": 10, "color": "body", "lh": 1.46}])
        rule(s, 4.74, x=x, w=3.45, color="mint2")
        s.txt(x, 4.86, 3.45, 0.7, [{"t": hvad[i], "size": 9, "bold": True, "color": "teal", "lh": 1.4}])
    s.rect(ML, 5.62, CW, 0.78, fill="peach", r=0.03)
    s.txt(ML + 0.30, 5.70, CW - 0.60, 0.52, [
        {"t": "FNs bærekraftsmål 12 — ansvarlig forbruk og produksjon. Bidraget vårt er betinget, ikke bevist: "
              "vi kan først dokumentere det når familier faktisk har tatt mobilene i bruk igjen.",
         "size": 10, "color": "petrol", "lh": 1.42}])
    footer(s, 6)
    return s

# ------------------------------------------------------------------ 07 metode
def s07():
    s = Slide("paper", notes=(
        "Tema 2, del 1 (50 sek). Hvilken undersøkelse: dokumentanalyse. Slik gikk vi fram: først formulerte vi "
        "spørsmålet, så valgte vi kilder, leste og noterte, og sorterte alt i fire funn. Kildene var "
        "Skyss, NSM, Medietilsynet, Helsedirektoratet, EEA, Miljødirektoratet og Ungt Entreprenørskap. "
        "Målet var å avklare om ideen er teknisk og juridisk gjennomførbar før vi brukte penger. "
        "Svakheten er at dette er sekundærdata: den sier hva som er mulig, ikke hva kundene vil betale for."))
    head(s, "02 / MARKEDSUNDERSØKELSER", "Vi begynte med å etterprøve ideen.")
    s.txt(ML, 2.04, 5.6, 0.25,
          [{"t": "SLIK GJORDE VI DET", "size": 7.5, "bold": True, "color": "teal", "tr": 1.6}])
    steps = [
        ("01", "Spørsmålet", "Hva må være sant for at vi kan selge dette?"),
        ("02", "Kildene", "Myndighet, leverandør og bransje."),
        ("03", "Lesingen", "Krav og grenser notert med dato og lenke."),
        ("04", "Sorteringen", "Alt ble fire funn som endret produktet."),
    ]
    for i, (n, t, d) in enumerate(steps):
        y = 2.32 + i * 0.74
        s.txt(ML, y + 0.02, 0.4, 0.22, [{"t": n, "size": 7.5, "bold": True, "color": "peach", "tr": 1.2}])
        s.txt(ML + 0.38, y - 0.02, 5.2, 0.26, [{"t": t, "size": 10, "bold": True, "color": "petrol"}])
        s.txt(ML + 0.38, y + 0.24, 5.2, 0.3, [{"t": d, "size": 8.5, "color": "body", "lh": 1.3}])
    rule(s, 5.44, x=ML, w=5.55)
    s.txt(ML, 5.52, 5.45, 0.3,
          [{"t": "Sekundærdata: kvalitativ og ikke representativ.", "size": 9, "color": "body", "lh": 1.4}])
    s.txt(ML, 5.80, 5.45, 0.3,
          [{"t": "Målet: finne kravene før vi brukte penger.", "size": 9, "bold": True, "color": "teal", "lh": 1.4}])
    s.rect(ML, 6.14, 0.035, 0.74, fill="peach")
    s.txt(ML + 0.30, 6.14, 5.1, 0.22,
          [{"t": "I TILLEGG: SAMTALE MED LÆRERE", "size": 6.5, "bold": True, "color": "teal", "tr": 1.5}])
    s.txt(ML + 0.30, 6.36, 5.25, 0.5,
          [{"t": "De mente ideen har mening, men at detaljer må avklares før salg.", "size": 8.5, "color": "body", "lh": 1.35}])
    s.rect(6.62, 2.16, 0.007, 4.05, fill="rule")
    s.txt(7.05, 2.16, 5.4, 0.3, [{"t": "KILDENE VI LESTE", "size": 7.5, "bold": True, "color": "teal", "tr": 1.6}])
    src = [
        ("Skyss", "krav til OS og nett"),
        ("NSM", "sikkerhetsoppdateringer"),
        ("Medietilsynet", "foreldrekontrollens grenser"),
        ("Helsedirektoratet", "skjermråd til familier"),
        ("EEA", "lengre levetid som miljøtiltak"),
        ("Miljødirektoratet", "retur av EE-avfall"),
        ("Ungt Entreprenørskap", "hva juryene belønner"),
    ]
    for i, (name, d) in enumerate(src):
        yy = 2.52 + i * 0.56
        s.txt(7.05, yy, 2.20, 0.28, [{"t": name, "size": 9, "bold": True, "color": "petrol"}])
        s.txt(9.35, yy + 0.02, 3.20, 0.26, [{"t": d, "size": 8.5, "color": "body"}])
        rule(s, yy + 0.46, x=7.05, w=5.5)
    s.txt(7.05, 6.42, 5.5, 0.3,
          [{"t": "Alle kilder er lest 11.11.2026 og oppgitt med lenke bakerst.", "size": 7.5, "color": "muted"}])
    footer(s, 7)
    return s

# ------------------------------------------------------------------ 08 funn
def s08():
    s = Slide("paper", notes=(
        "Funn (70 sek). Fire funn gjorde at vi endret produktet — dette er det viktigste med hele undersøkelsen. "
        "Ett: Skyss trenger nett, så vi kan ikke selge «uten nett». To: Skyss krever iOS 16.4 eller Android 6.0, "
        "så mange skuffemobiler faller utenfor. Tre: barn under 15 kan ikke ha egen profil. Fire: foreldrekontroll "
        "er ikke full beskyttelse. Hvert funn ble et produktkrav."))
    head(s, "02 / MARKEDSUNDERSØKELSER", "Fire funn endret produktet.")
    s.txt(ML, 2.12, 9.0, 0.35,
          [{"t": "Undersøkelsen ga ikke bare informasjon — den ga fire konkrete krav til tjenesten.",
            "size": 11, "color": "body"}])
    s.txt(ML, 2.62, 4.7, 0.25, [{"t": "FUNN", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    s.txt(5.72, 2.62, 6.6, 0.25, [{"t": "KONSEKVENS FOR OSS", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    rule(s, 2.86)
    rows = [
        ("Skyss trenger internett for kjøp og visning av billett.",
         "Vi kan ikke selge «uten nett». Vi lover begrenset tilgang, ikke frakobling."),
        ("Skyss krever iOS 16.4 eller Android 6.0.",
         "Mange skuffemobiler faller utenfor. Vi tester modellen før vi tar imot den."),
        ("Barn under 15 kan ikke ha egen Skyss-profil.",
         "Forelderen kjøper og sender billetten. Det må stå i guiden."),
        ("Foreldrekontroll gir ikke full beskyttelse.",
         "Vi viser hva som er satt opp — og hva foreldrene fortsatt må følge opp."),
    ]
    for i, (f, k) in enumerate(rows):
        yy = 3.02 + i * 0.94
        s.txt(ML, yy, 4.55, 0.75, [{"t": f, "size": 11, "bold": True, "color": "petrol", "lh": 1.35}])
        s.txt(5.42, yy + 0.02, 0.3, 0.3, [{"t": "»", "size": 15, "bold": True, "color": "teal"}])
        s.txt(5.80, yy + 0.04, 6.4, 0.75, [{"t": k, "size": 10.5, "color": "body", "lh": 1.42}])
        rule(s, yy + 0.78)
    s.txt(ML, 6.70, 9.0, 0.25,
          [{"t": "Kilder: Skyss, NSM og Medietilsynet, lest 11.11.2026.", "size": 8, "color": "muted"}])
    footer(s, 8)
    return s


# ------------------------------------------------------------------ 09 primærdata
def s09():
    s = Slide("paper", notes=(
        "Veien videre (40 sek). Vi vet hva som er mulig — nå må vi vite hva folk faktisk vil ha og betale for. "
        "Fire grep: intervju for språk og behov, spørreskjema for betalingsvilje, pilot for tid og feil, og en "
        "pristest. Hovedregelen vår: skille hva folk sier fra hva de betaler."))
    head(s, "02 / MARKEDSUNDERSØKELSER", "Neste steg er primærdata.")
    s.txt(ML, 2.12, 9.2, 0.35,
          [{"t": "Sekundærdata sier hva som er mulig. Bare egne data kan si hva foreldre faktisk vil ha og betale for.",
            "size": 11, "color": "body"}])
    cards = [
        ("01", "INTERVJU", "5–8 foreldre + 3 barn",
         "Semistrukturert. Forstå behov, språk og hva de frykter."),
        ("02", "SPØRRESKJEMA", "40–60 svar via FAU",
         "Kvantitativt. Test betalingsvilje og prisintervall."),
        ("03", "KOMPATIBILITETSTEST", "3–5 skuffemobiler",
         "Vi tester Skyss-kravene mot faktiske modeller før vi tar imot en eneste."),
        ("04", "PRISTEST", "Van Westendorp",
         "Fire spørsmål som gir et prisintervall — ikke et ønsketall."),
    ]
    for i, (n, t, meta, d) in enumerate(cards):
        x = ML + (i % 2) * 6.02
        y = 2.62 + (i // 2) * 1.62
        s.rect(x, y, 5.75, 1.44, fill="white", line="rule2", lw=0.75, r=0.03)
        s.txt(x + 0.34, y + 0.26, 0.5, 0.3, [{"t": n, "size": 8.5, "bold": True, "color": "peach", "tr": 1.2}])
        s.txt(x + 0.82, y + 0.24, 3.0, 0.3, [{"t": t, "size": 10, "bold": True, "color": "teal", "tr": 1.4}])
        s.txt(x + 0.82, y + 0.52, 4.5, 0.3, [{"t": meta, "size": 12.5, "bold": True, "color": "petrol"}])
        s.txt(x + 0.82, y + 0.84, 4.55, 0.7, [{"t": d, "size": 9.5, "color": "body", "lh": 1.4}])
    s.txt(ML, 5.98, CW, 0.3,
          [{"t": "Hovedregel: vi skiller hva folk sier fra hva de faktisk betaler.", "size": 10.5,
            "bold": True, "color": "teal"}])
    footer(s, 9)
    return s


# ------------------------------------------------------------------ 10 merkevarekonsept
def s10():
    s = Slide("paper", notes=(
        "Tema 3, del 1 (55 sek). Merkevarekonseptet: «en god start» — ikke et kontrollsystem. Kjernen er "
        "trygghet uten kontrollmaskeri. Posisjoneringssetningen sier hvem, hva og hvorfor. Legg merke til at vi "
        "ikke lover beskyttelse; vi lover oversikt. Vi testet også navnet og tilbudet på et par voksne: "
        "de forsto nytten, men ikke omfanget. Derfor forklarer vi tjenesten før teknologien."))
    head(s, "03 / MERKEVAREBYGGING", "En god start — ikke et kontrollsystem.")
    s.txt(ML, 2.10, 6.3, 0.3, [{"t": "MERKEVAREKJERNE", "size": 7.5, "bold": True, "color": "teal", "tr": 1.6}])
    s.txt(ML, 2.34, 6.25, 0.4,
          [{"t": "Trygghet uten kontrollmaskeri.", "size": 17, "bold": True, "color": "petrol",
            "lh": 1.2, "tr": -0.3}])
    s.txt(ML, 2.76, 6.25, 0.7,
          [{"t": "Vi lover ikke at barnet er beskyttet mot alt. Vi lover at foreldrene vet nøyaktig hva som er "
                "satt opp — og hva de må følge opp selv.", "size": 10.5, "color": "body", "lh": 1.5}])
    s.txt(ML, 3.54, 6.3, 0.3, [{"t": "POSISJONERING", "size": 7.5, "bold": True, "color": "teal", "tr": 1.6}])
    s.rect(ML, 3.78, 0.035, 1.16, fill="peach")
    s.txt(ML + 0.30, 3.78, 5.95, 1.2, [
        {"t": "For foreldre i Bergen som vil gi barnet en første mobil uten full smarttelefon, gjør Safestart "
              "mobilen dere allerede eier klar til å ringe, reise og komme hjem — en god start er enkel, "
              "ærlig og på deres premisser.", "size": 10.5, "color": "petrol", "lh": 1.48}])

    s.txt(ML, 5.14, 6.3, 0.3,
          [{"t": "TEST AV FORSTÅELSE", "size": 7.5, "bold": True, "color": "teal", "tr": 1.6}])
    s.rect(ML, 5.38, 0.035, 0.86, fill="teal")
    s.txt(ML + 0.30, 5.38, 5.95, 0.9, [
        {"t": "Vi viste navnet og tilbudet til et par voksne: «Hva tror du vi selger?» De forsto nytten, "
              "men ikke omfanget — derfor forklarer vi tjenesten før teknologien.", "size": 9.5, "color": "body", "lh": 1.42}])

    s.txt(ML, 6.36, 11.0, 0.28,
          [{"t": "Navnet er ikke endelig godkjent i Brønnøysundregistrene — her brukes det som arbeidstittel.",
            "size": 8.5, "color": "muted"}])
    s.rect(7.42, 2.10, 5.13, 4.06, fill="mint", r=0.025)
    s.img(LOGO, 9.02, 2.40, 1.55, 1.55)
    s.txt(7.72, 4.06, 4.55, 0.8, [
        {"t": "FØRSTE STEG", "size": 8, "bold": True, "color": "teal", "tr": 1.8, "sa": 6},
        {"t": "«Første mobil.\nPå deres premisser.»", "size": 15, "bold": True, "color": "petrol",
         "lh": 1.3, "tr": -0.2},
    ], align="c")
    s.txt(7.72, 5.34, 4.55, 0.55,
          [{"t": "Symbolet er en mobilramme med en avrundet dør, et første trinn og en varm startprikk.",
            "size": 8.5, "color": "body", "lh": 1.4}], align="c")
    footer(s, 10)
    return s

# ------------------------------------------------------------------ 11 merkeelementer
def s11():
    s = Slide("paper", notes=(
        "Merkeelementer (60 sek). Fem elementer: navn, symbol, slagord, farger og tone. Poenget er konsistens — "
        "de samme fem går igjen på nettsiden, i guiden og på stand. Og en ærlig innrømmelse: navnet er ikke "
        "godkjent, og profilen er ikke testet på kunder ennå."))
    head(s, "03 / MERKEVAREBYGGING", "Fem elementer som gjør oss gjenkjennelige.")
    cards = [
        ("NAVN", "Safestart", "Safe + start. Navnet sier løftet uten å love beskyttelse."),
        ("SYMBOL", "Første steg", "Mobilramme, avrundet dør, første trinn og en varm startprikk."),
        ("SLAGORD", "På deres premisser", "«Første mobil. På deres premisser.» — foreldrenes valg, ikke vårt."),
    ]
    for i, (lab, t, d) in enumerate(cards):
        x = ML + i * 3.98
        s.rect(x, 2.14, 3.72, 1.46, fill="white", line="rule2", lw=0.75, r=0.03)
        s.txt(x + 0.28, 2.32, 3.2, 0.28, [{"t": lab, "size": 7, "bold": True, "color": "teal", "tr": 1.6}])
        s.txt(x + 0.28, 2.54, 3.2, 0.34, [{"t": t, "size": 13, "bold": True, "color": "petrol"}])
        s.txt(x + 0.28, 2.94, 3.18, 0.6, [{"t": d, "size": 8.5, "color": "body", "lh": 1.38}])

    s.rect(ML, 3.78, 6.52, 1.84, fill="white", line="rule2", lw=0.75, r=0.03)
    s.txt(ML + 0.28, 3.94, 5.9, 0.28, [{"t": "FARGER", "size": 7, "bold": True, "color": "teal", "tr": 1.6}])
    sw = [("173B4D", "Petrol"), ("116B65", "Teal"), ("F7FAF8", "Papir"), ("DDF1E9", "Mint"), ("FFD19A", "Fersken")]
    for i, (h, name) in enumerate(sw):
        x = ML + 0.28 + i * 1.20
        s.rect(x, 4.20, 0.94, 0.50, fill=h, line="rule2" if h in ("F7FAF8", "DDF1E9") else None, lw=0.75, r=0.06)
        s.txt(x, 4.78, 1.08, 0.42, [{"t": f"#{h}", "size": 7, "bold": True, "color": "petrol", "sa": 1},
                                    {"t": name, "size": 6.5, "color": "muted"}])
    s.rect(7.05, 3.78, 5.50, 1.84, fill="mint", r=0.03)
    s.txt(7.35, 3.94, 4.9, 0.28, [{"t": "TONE", "size": 7, "bold": True, "color": "teal", "tr": 1.6}])
    s.txt(7.35, 4.20, 5.0, 0.6,
          [{"t": "Kort, konkret og ærlig. Vi sier hva vi vet, hva vi ikke vet, og hva foreldrene må gjøre selv.",
            "size": 9, "color": "petrol", "lh": 1.45}])
    rule(s, 4.94, x=7.35, w=4.9, color="mint2")
    s.txt(7.35, 5.02, 4.9, 0.5,
          [{"t": "«Vi lover ikke at alt er beskyttet. Vi lover at du vet hva som er satt opp.»",
            "size": 8.5, "color": "petrol", "lh": 1.42}])
    s.txt(ML, 5.86, CW, 0.5,
          [{"t": "Navnet er ikke godkjent ennå — vi bruker det som arbeidstittel. Profilen finnes på nettsiden, "
                "men er ikke testet på kunder.", "size": 8.5, "color": "muted", "lh": 1.4}])
    footer(s, 11)
    return s

# ------------------------------------------------------------------ 12 fem P
def s12():
    s = Slide("paper", notes=(
        "Markedsstrategi (60 sek). De fem P-ene, rangert. Produkt er mest sentralt fordi tjenesten er produktet: "
        "et oppsett som ikke virker, reddes ikke av annonser. Personale er nesten like viktig: foreldrene kjøper "
        "tillit av jevnaldrende. Plass er lokal. Pris er viktig men uavklart. Påvirkning er minst viktig i bred "
        "kanal, fordi vi ikke kan konkurrere med annonsebudsjetter og målgruppen nås gjennom skole og FAU."))
    head(s, "03 / MERKEVAREBYGGING", "De fem P-ene, rangert.")
    s.txt(ML, 2.08, 9.6, 0.3,
          [{"t": "Rangeringen er et strategisk valg: hvilke P-er må være gode for at tjenesten skal selge?",
            "size": 10.5, "color": "body"}])
    s.txt(ML, 2.54, 3.6, 0.25, [{"t": "P", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    s.txt(3.15, 2.54, 2.4, 0.25, [{"t": "VEKT", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    s.txt(5.80, 2.54, 6.0, 0.25, [{"t": "BEGRUNNELSE", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    rule(s, 2.78)
    rows = [
        ("1", "PRODUKT", 1.00, "Tjenesten er produktet. Et oppsett som ikke virker, reddes ikke av annonser."),
        ("2", "PERSONALE", 0.86, "Foreldrene kjøper tillit av jevnaldrende. Vi møter dem ansikt til ansikt."),
        ("3", "PLASS", 0.70, "Skolen, FAU og mobilkvelden. Tillit reiser ikke langt."),
        ("4", "PRIS", 0.54, "Viktig, men uavklart: per mobil og per mobilkveld."),
        ("5", "PÅVIRKNING", 0.34, "Minst viktig i bred kanal: vi kan ikke konkurrere med annonsebudsjett."),
    ]
    for i, (n, name, wgt, why) in enumerate(rows):
        yy = 2.94 + i * 0.72
        s.txt(ML, yy + 0.04, 0.4, 0.28, [{"t": n, "size": 8.5, "bold": True, "color": "peach", "tr": 1.2}])
        s.txt(ML + 0.42, yy, 1.95, 0.3,
              [{"t": name, "size": 11.5, "bold": True, "color": "petrol", "tr": 0.8}])
        s.rect(3.15, yy + 0.14, 2.25, 0.10, fill="mint")
        s.rect(3.15, yy + 0.14, 2.25 * wgt, 0.10, fill="teal")
        s.txt(5.80, yy, 6.55, 0.52, [{"t": why, "size": 9.2, "color": "body", "lh": 1.32}])
        rule(s, yy + 0.64)
    s.txt(ML, 6.58, CW, 0.26,
          [{"t": "Rekkefølgen er ikke en fasit — den skal testes mot primærdata i tema 2.", "size": 8.5, "color": "muted"}])
    footer(s, 12)
    return s

# ------------------------------------------------------------------ 13 kampanje
def s13():
    s = Slide("paper", notes=(
        "Tema 4, del 1 (60 sek). Kampanjen heter Skuffemobilen. Det er en lokal relasjonskampanje med et "
        "arrangement som kjerne — ikke rabatt og ikke betalt annonsering. Målgruppen er foreldre til barn i 5. til "
        "8. trinn i Bergen. Budskapet er «du har allerede mobilen». Målene er hentet fra forretningsplanen."))
    head(s, "04 / MARKEDSFØRINGSKAMPANJE", "Skuffemobilen starter i et klasserom.")
    blocks = [
        ("KAMPANJETYPE", 2.14, "Lokal relasjonskampanje med et arrangement som kjerne. Ikke rabatt — tillit "
                               "bygges med bevis, ikke med tilbud."),
        ("MÅLGRUPPE", 3.42, "Foreldre til barn i 5.–8. trinn i Bergen som har en brukbar mobil liggende. "
                            "Sekundært FAU ved lokale skoler."),
    ]
    for lab, y, body in blocks:
        s.txt(ML, y, 6.4, 0.25, [{"t": lab, "size": 7, "bold": True, "color": "teal", "tr": 1.6}])
        s.txt(ML, y + 0.24, 6.3, 0.7, [{"t": body, "size": 10.5, "color": "body", "lh": 1.45}])
        rule(s, y + 1.14, w=6.3)
    s.txt(ML, 4.72, 6.4, 0.25, [{"t": "BUDSKAP", "size": 7, "bold": True, "color": "teal", "tr": 1.6}])
    s.txt(ML, 4.96, 6.3, 0.9,
          [{"t": "«Du har allerede mobilen. Vi hjelper dere å gjøre den klar.»", "size": 14, "bold": True,
            "color": "petrol", "lh": 1.4}])

    s.rect(7.30, 2.14, 5.25, 3.97, fill="petrol", r=0.025)
    s.txt(7.64, 2.40, 4.5, 0.3, [{"t": "MÅL FØRSTE HALVÅR", "size": 7.5, "bold": True, "color": "peach", "tr": 1.6}])
    goals = [("10–15", "mobiler satt opp"), ("1–2", "mobilkvelder for FAU"),
             ("10", "betalende kunder"), ("100", "følgere på Instagram"),
             ("5", "kunder som gir tilbakemelding")]
    for i, (num, lab) in enumerate(goals):
        yy = 2.82 + i * 0.60
        s.txt(7.64, yy, 1.20, 0.32, [{"t": num, "size": 13, "bold": True, "color": "white"}])
        s.txt(8.86, yy + 0.04, 3.3, 0.32, [{"t": lab, "size": 9.5, "color": "darkbody"}])
    s.txt(7.64, 5.82, 4.6, 0.25, [{"t": "Fra forretningsplanens markedsmål.", "size": 7.5, "color": "darkmuted"}])
    s.txt(ML, 5.72, 6.2, 0.22, [{"t": "KANALER", "size": 7, "bold": True, "color": "muted", "tr": 1.5}])
    s.txt(ML, 5.94, 6.3, 0.20,
          [{"t": "Mobilkveld, plakat, Instagram og guiden \u2014 i den rekkef\u00f8lgen.",
            "size": 10.5, "color": "body"}])
    rule(s, 6.24, x=ML, w=6.3)
    s.txt(ML, 6.32, 6.3, 0.32,
          [{"t": "Materiellet som bærer budskapet er laget — se neste side.", "size": 9.5, "color": "muted"}])
    footer(s, 13)
    return s

# ------------------------------------------------------------------ 14 materiell
def s14():
    s = Slide("paper", notes=(
        "Materiell (45 sek). Tre av fire flater er laget som utkast: et Instagram-innlegg, en standplakat og "
        "ett-arks guiden foreldrene får med seg hjem. Alle tre bruker de samme fem merkeelementene \u2014 navn, "
        "symbol, slagord, farger og tone \u2014 så de henger sammen med nettsiden og appen. Mobilkvelden er "
        "den fjerde flaten og er ikke laget ennå. Legg merke til at ingen av flatene lover mer enn systemet "
        "holder: ingen pris, ingen dato, ingen full beskyttelse."))
    head(s, "04 / MARKEDSF\u00d8RINGSKAMPANJE", "Fire flater, ett budskap.")
    s.txt(ML, 1.80, 11.2, 0.3,
          [{"t": "Tre av fire er laget som utkast \u2014 og alle bygger på de samme fem merkeelementene.",
            "size": 10.5, "color": "body"}])

    top = 2.22
    H = 3.00
    wi = H * 1080.0 / 1350.0
    wa = H * 1240.0 / 1754.0
    xs = [ML, ML + wi + 0.26, ML + wi + wa + 0.52]
    sizes = [(wi, H), (wa, H), (wa, H)]
    files = ["instagram.png", "plakat.png", "guide.png"]
    caps = ["INSTAGRAM 4:5", "STANDPLAKAT A4", "ETT-ARKS GUIDE A4"]
    unders = ["Innlegg som forklarer tilbudet.",
              "Én setning, én vei videre.",
              "Arket de tar med hjem."]
    for i, (xf, (wf, hf)) in enumerate(zip(xs, sizes)):
        s.rect(xf - 0.05, top - 0.05, wf + 0.10, hf + 0.10,
               fill="white", line="rule2", lw=0.75, r=0.02)
        s.img(os.path.join(ROOT, "campaign", files[i]), xf, top, wf, hf)
        s.txt(xf, top + H + 0.14, wf, 0.2,
              [{"t": caps[i], "size": 7.5, "bold": True, "color": "teal", "tr": 1.5}])
        s.txt(xf, top + H + 0.34, wf + 0.12, 0.34,
              [{"t": unders[i], "size": 8.4, "color": "muted", "lh": 1.35}])

    # right column: the four surfaces and their status
    x = 8.42
    s.txt(x, top, 4.1, 0.25, [{"t": "FLATENE I KAMPANJEN", "size": 7, "bold": True,
                               "color": "muted", "tr": 1.5}])
    rule(s, top + 0.26, x=x, w=4.12)
    rows = [
        ("01", "ETT-ARKS GUIDE", "Det kunden tar med hjem \u2014 vårt sterkeste salgsargument.",
         "Laget", True),
        ("02", "INSTAGRAM", "Myte, utdrag fra guiden, kundens historie.", "Laget", True),
        ("03", "STANDPLAKAT", "Til skolens stand: én setning, ingen støy.", "Laget", True),
        ("04", "MOBILKVELD", "Invitasjon til FAU med program og påmelding.", "Neste", False),
    ]
    for i, (n, t, d, status, done) in enumerate(rows):
        y = top + 0.42 + i * 0.94
        if i:
            rule(s, y - 0.12, x=x, w=4.12)
        s.txt(x, y + 0.02, 0.4, 0.22, [{"t": n, "size": 8, "bold": True,
                                       "color": "peach", "tr": 1.2}])
        s.txt(x + 0.40, y - 0.02, 2.00, 0.24,
              [{"t": t, "size": 10.5, "bold": True, "color": "petrol"}])
        s.txt(x + 0.40, y + 0.24, 3.72, 0.40, [{"t": d, "size": 8.6, "color": "body", "lh": 1.35}])
        s.txt(x + 2.62, y + 0.02, 1.50, 0.22,
              [{"t": status, "size": 7.5, "bold": done,
                "color": "teal" if done else "muted"}], align="r")

    s.rect(ML, 6.02, CW, 0.56, fill="mint", r=0.03)
    s.txt(ML + 0.26, 6.15, CW - 0.52, 0.32, [
        {"t": "Plakaten skaper oppmerksomhet, mobilkvelden tillit, guiden holder løftet "
              "\u2014 og Instagram gjør oss kjent.",
         "size": 9.5, "color": "petrol", "lh": 1.4}])
    s.txt(ML, 6.70, CW, 0.3,
          [{"t": "Status: tre av fire flater er laget som utkast. Mobilkvelden er den siste.",
            "size": 8.5, "color": "muted"}])
    footer(s, 14)
    return s

def s15():
    s = Slide("petrol", notes=(
        "Refleksjon (50 sek). Dette er den viktigste sliden for fagsamtalen. Vi skiller tydelig mellom det vi har "
        "dokumentert og det vi bare tror. Alt i høyre kolonne er ting vi må måle før vi kan si noe om det. "
        "Det er ikke en svakhet vi skjuler — det er arbeidsplanen vår."))
    eyebrow(s, ML, 0.56, "OPPSUMMERING  ·  REFLEKSJON", color="mint2")
    s.txt(ML, 0.84, 10.6, 0.64,
          [{"t": "Det vi vet — og det vi ikke vet.", "size": 33, "bold": True, "color": "white",
            "lh": 1.05, "tr": -0.7}])
    s.txt(ML, 1.62, 9.6, 0.34,
          [{"t": "Vi lover ikke det vi ikke har målt. Det er også en del av merkevaren.", "size": 12,
            "color": "darkbody"}])
    s.txt(ML, 2.38, 5.4, 0.28, [{"t": "DOKUMENTERT", "size": 7.5, "bold": True, "color": "peach", "tr": 1.7}])
    s.rect(ML, 2.64, 5.35, 0.007, fill="2B4E5F")
    vet = ["Skyss krever nett og iOS 16.4 / Android 6.0.",
           "Foreldrekontroll gir ikke full beskyttelse.",
           "Ideen er tjeneste-, prosess- og forretningsmodellinnovasjon.",
           "Profil, nettside og ett-arks guide finnes."]
    for i, t in enumerate(vet):
        s.txt(ML, 2.86 + i * 0.82, 5.3, 0.6, [{"t": t, "size": 10.5, "color": "white", "lh": 1.4}])

    s.txt(6.90, 2.38, 5.4, 0.28, [{"t": "IKKE DOKUMENTERT", "size": 7.5, "bold": True, "color": "peach", "tr": 1.7}])
    s.rect(6.90, 2.64, 5.35, 0.007, fill="2B4E5F")
    ikke = ["Hva foreldre vil betale, og hva et oppsett koster i tid.",
            "Hvor mange skuffemobiler som støtter Skyss.",
            "Om familiene faktisk tar mobilen i bruk.",
            "Om tjenesten gir miljøgevinst eller bare mulighet."]
    for i, t in enumerate(ikke):
        s.txt(6.90, 2.86 + i * 0.82, 5.3, 0.6, [{"t": t, "size": 10.5, "color": "darkbody", "lh": 1.4}])
    s.txt(ML, 6.06, 10.4, 0.4,
          [{"t": "Det vi ikke vet, er arbeidsplanen vår — ikke noe vi skjuler.",
            "size": 14, "bold": True, "color": "peach"}])
    footer(s, 15, dark=True)
    return s

# ------------------------------------------------------------------ 16 kilder
def s16():
    s = Slide("paper", notes=(
        "Kilder (20 sek). Alle kilder er lest 11.11.2026 og står med lenke i forretningsplanen. "
        "KI er brukt til researchoppsummering, kildekontroll og utforming — det er merket her, og alle påstander "
        "er kontrollert mot kilden. Tall vi ikke har dokumentert, er ikke oppgitt."))
    head(s, "KILDER", "Kilder og KI-bruk.")
    left = [
        ("Skyss", "Spørsmål og svar om appen Skyss — minstekrav og nettilgang."),
        ("NSM", "13 råd for bedre sikkerhet på mobile enheter."),
        ("Medietilsynet", "Foreldrekontroll — hva den dekker og ikke dekker."),
        ("Helsedirektoratet", "Skjermråd for barn og unge."),
    ]
    right = [
        ("EEA", "Europe's consumption in a circular economy — longer-lasting electronics."),
        ("Miljødirektoratet", "Elektronisk og elektrisk avfall — returordninger."),
        ("Ungt Entreprenørskap", "Resultater og jurybegrunnelser, NM 2025 og Oslo 2025."),
        ("Forbrukertilsynet", "Veiledning om bærekraftpåstander i markedsføring."),
    ]
    for col, items in ((ML, left), (6.70, right)):
        for i, (name, d) in enumerate(items):
            yy = 2.16 + i * 0.94
            s.txt(col, yy, 4.6, 0.3, [{"t": name, "size": 10.5, "bold": True, "color": "petrol"}])
            s.txt(col, yy + 0.26, 5.15, 0.6, [{"t": d, "size": 8.8, "color": "body", "lh": 1.38}])
    s.rect(ML, 6.04, CW, 0.66, fill="mint", r=0.03)
    s.txt(ML + 0.30, 6.12, 5.7, 0.50, [
        {"t": "KI-BRUK", "size": 6.5, "bold": True, "color": "teal", "tr": 1.6, "sa": 2},
        {"t": "Brukt til research, kildekontroll og utforming.", "size": 8.5, "color": "petrol"}])
    s.txt(7.05, 6.14, 5.4, 0.46, [
        {"t": "Alle påstander er kontrollert mot kilden. Tall vi ikke har dokumentert, er ikke oppgitt.",
         "size": 8.5, "color": "petrol", "lh": 1.35}])
    footer(s, 16)
    return s



# ------------------------------------------------------------------ prototyp
def s_proto():
    s = Slide("paper", notes=(
        "Belegg (55 sek). Dette er ikke en tegning — det er en app vi har bygd og kjørt på en ekte "
        "Android 6.0. Vi gjorde det for å svare på ett spørsmål: lar kombinasjonen seg bygge i det "
        "hele tatt? Tre skjermer: hjem, PIN for foreldre, og en av appene barnet får. Legg merke til at "
        "«Ring» ikke kan slås av noe sted — det er hele poenget. Nederst skiller vi det vi har "
        "testet fra det som gjenstår. Og merk den siste setningen: uten Device Owner er dette bare en "
        "hjemmeskjerm."))
    head(s, "01 / BÆREKRAFTIG INNOVASJON", "Vi bygde den for å se om det går.")
    s.txt(ML, 1.62, 11.0, 0.4,
          [{"t": "En prototype er ikke et produkt. Den svarer på om kombinasjonen lar seg bygge.",
            "size": 10, "color": "body", "lh": 1.4}])

    shots = [
        ("proof/deck-home.png", "HJEM", "Ingen nettleser."),
        ("proof/deck-pin.png", "FORELDRE", "PIN, ikke meny."),
        ("proof/deck-chess.png", "SJAKK", "Spill, ikke scroll."),
    ]
    for i, (path, cap, under) in enumerate(shots):
        x = ML + i * 1.96
        s.rect(x - 0.04, 2.16 - 0.04, 1.80 + 0.08, 3.20 + 0.08,
               fill="white", line="rule2", lw=0.75, r=0.05)
        s.img(os.path.join(ROOT, path), x, 2.16, 1.80, 3.20)
        s.txt(x, 5.42, 1.80, 0.20, [{"t": cap, "size": 7.5, "bold": True, "color": "teal", "tr": 1.6}])
        s.txt(x, 5.62, 1.86, 0.26, [{"t": under, "size": 8, "color": "muted"}])

    s.rect(6.86, 2.16, 5.69, 3.20, fill="petrol", r=0.025)
    s.txt(7.14, 2.34, 5.0, 0.25, [{"t": "TEKNISK", "size": 7.5, "bold": True, "color": "mint2", "tr": 1.8}])
    rows = [
        ("01", "Android 6.0 · API 23", "Samme minstekrav som Skyss stiller."),
        ("02", "Ren Java, ingen bibliotek", "Under 100 kB uten avhengigheter."),
        ("03", "Ring kan ikke slås av", "Verken av barnet eller i innstillingene."),
        ("04", "Testet med Device Owner", "Ikke bare på papiret — kjørt og verifisert."),
    ]
    for i, (n, t, d) in enumerate(rows):
        y = 2.66 + i * 0.68
        s.txt(7.14, y, 0.4, 0.22, [{"t": n, "size": 8, "bold": True, "color": "peach", "tr": 1.2}])
        s.txt(7.56, y - 0.03, 4.7, 0.24, [{"t": t, "size": 10, "bold": True, "color": "white"}])
        s.txt(7.56, y + 0.21, 4.65, 0.3, [{"t": d, "size": 8.5, "color": "darkbody", "lh": 1.35}])

    s.rect(ML, 5.86, 5.85, 0.66, fill="mint")
    s.rect(ML, 5.86, 0.05, 0.66, fill="teal")
    s.txt(ML + 0.24, 5.92, 5.4, 0.20,
          [{"t": "BEVIST I TESTEN", "size": 6.5, "bold": True, "color": "teal", "tr": 1.6}])
    s.txt(ML + 0.24, 6.12, 5.45, 0.30,
          [{"t": "Alltid ringbar. HOME, BACK og Innstillinger er stengt ute.", "size": 8.8, "color": "petrol"}])

    s.rect(ML + 6.02, 5.86, 5.75, 0.66, fill="white", line="rule2", lw=0.75)
    s.rect(ML + 6.02, 5.86, 0.05, 0.66, fill="peach")
    s.txt(ML + 6.26, 5.92, 5.3, 0.20,
          [{"t": "GJENSTÅR FØR SALG", "size": 6.5, "bold": True, "color": "petrol", "tr": 1.6}])
    s.txt(ML + 6.26, 6.12, 5.35, 0.30,
          [{"t": "Device Owner i oppsettet. Skyss er en hel app.", "size": 8.8, "color": "body"}])

    rule(s, 6.66)
    s.txt(ML, 6.72, CW, 0.28,
          [{"t": "Uten Device Owner er Safestart bare en hjemmeskjerm. Med Device Owner er telefonen faktisk låst.",
            "size": 10, "bold": True, "color": "petrol"}])
    footer(s, 99)
    return s

TIMING = [8, 20, 8, 35, 25, 25, 35, 55, 30, 25, 20, 30, 20, 30, 35, 35, 30, 4]


def build():
    import re
    sl = [s01(), s02(), s_team(), s03(), s04(), s05(), s06(), s_proto(),
          s07(), s08(), s09(), s10(), s11(), s12(), s13(), s14(), s15(), s16()]
    total = len(sl)
    acc = 0
    for i, sl_ in enumerate(sl):
        sec = TIMING[i] if i < len(TIMING) else 20
        acc += sec
        clean = re.sub(r"\s*\(\d+ sek\)", "", sl_.notes)
        sl_.notes = ("TID: %d sek  (totalt %d:%02d av 8:00)\n\n" % (sec, acc // 60, acc % 60)) + clean
    import re
    for i, sl_ in enumerate(sl, 1):
        for e in sl_.els:
            if e["k"] != "txt":
                continue
            t = e["blocks"][0].get("t", "")
            if re.fullmatch(r"\d\d / \d\d", t):
                e["blocks"][0]["t"] = "%02d / %02d" % (i, total)
    return sl
