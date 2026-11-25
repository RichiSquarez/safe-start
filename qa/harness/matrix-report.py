#!/usr/bin/env python3
"""Turns qa/results/api*-{baseline,fixed}/ into report tables.

    python3 qa/harness/matrix-report.py            # markdown to stdout
    python3 qa/harness/matrix-report.py --write    # ... and to qa/results/matrix-data.md

Only reads files the suite already wrote, so it can run at any time.
"""
import json
import os
import re
import sys
import time

ROOT = "/Users/panygolf/Documents/ub-mobil"
RESULTS = ROOT + "/qa/results"
# Android release per API level, from the task's "major versions only" list.
VERSIONS = [(24, "7.0"), (26, "8.0"), (28, "9"), (29, "10"), (30, "11"),
            (31, "12"), (33, "13"), (34, "14"), (35, "15")]
OK, BAD, NA = "✅", "❌", "–"


def load(api, label):
    d = f"{RESULTS}/api{api}-{label}"
    s = f"{d}/summary.json"
    if not os.path.exists(s):
        return None
    try:
        data = json.load(open(s))
    except Exception:
        return None
    log = f"{d}/steps.log"
    text = open(log, errors="replace").read() if os.path.exists(log) else ""
    data["_log"] = text
    m = re.search(r"allowlist \(\d+\): \[(.*?)\]", text)
    data["_allowlist"] = m.group(1) if m else ""
    data["_foreign_allowlist"] = [p.strip() for p in data["_allowlist"].split(",")
                                  if p.strip() and p.strip() != "no.safestart.kiosk"]
    mm = re.search(r"ro\.build\.version\.release = (\S+)", text)
    data["_release"] = mm.group(1) if mm else ""
    mm = re.search(r"ro\.build\.fingerprint = (\S+)", text)
    data["_fp"] = mm.group(1) if mm else ""
    data["_dpm_ok"] = "Success: Device owner set" in text
    data["_install_ok"] = text.count("Performing Streamed Install Success")
    data["_skipped_helper"] = "skipped, image has its own dialer+messaging" in text
    return data


def cell(flags, text):
    return (OK if flags else BAD) + (" " + text if text else "")


def launch_cell(summary, key):
    v = summary["steps"].get("launch_" + key)
    if v is None:
        return NA
    if v.startswith("opened"):
        return OK
    return BAD


def lock_state(summary):
    locks = summary.get("lock", {})
    if not locks:
        return NA
    bad = [k for k, v in locks.items() if not v]
    return OK if not bad else f"{BAD} ({len(bad)}/{len(locks)})"


def escapes(summary):
    keys = ["escape-home", "escape-recents", "escape-statusbar", "escape-back",
            "foreign-app"]
    fg = summary.get("foreground", {})
    home = bool(fg.get("home", "").startswith("no.safestart.kiosk"))
    leaked = [k for k in keys if fg.get(k) and not fg[k].startswith("no.safestart.kiosk")]
    if not home:
        return NA
    return OK if not leaked else BAD + " (" + ",".join(leaked) + ")"


def reboot_cell(summary):
    tiles = summary.get("tiles", {}).get("after_reboot")
    fg = summary.get("foreground", {}).get("after-reboot", "")
    if tiles is None and not fg:
        return NA
    if fg and fg.startswith("no.safestart.kiosk"):
        n = sum(1 for v in tiles.values() if v and v != "TILE MISSING") if tiles else 0
        return OK
    return BAD + (" " + fg if fg else "")


def main():
    rows = []
    for api, rel in VERSIONS:
        for label in ("baseline", "fixed"):
            d = load(api, label)
            if not d:
                continue
            steps = d.get("steps", {})
            tiles = d.get("tiles", {}).get("home", {}) or {}
            avail = sum(1 for v in tiles.values() if v and v != "Ikke her")
            rows.append({
                "api": api, "rel": rel, "label": label,
                "avail": f"{avail}/{len(tiles)}" if tiles else NA,
                "phone": launch_cell(d, "phone"),
                "sms": launch_cell(d, "sms"),
                "camera": launch_cell(d, "camera"),
                "skyss": launch_cell(d, "skyss"),
                "pin": OK if steps.get("pin_dialog") else BAD,
                "parent": OK if steps.get("parent_reached") else BAD,
                "no_pin": OK if steps.get("parent_refused_without_pin") else BAD,
                "lock": lock_state(d),
                "escape": escapes(d),
                "reboot": reboot_cell(d),
                "allow": ",".join(d["_foreign_allowlist"]) or NA,
                "power": (" ".join(steps.get("power_menu_texts", []))[:40]
                          if "power_menu_texts" in steps else NA),
                "release": d["_release"], "raw": d,
            })

    out = []
    out.append("### Hovedmatrise\n")
    out.append("| Android | API | Utgave | Fliser | Ring | SMS | Kamera | Skyss "
               "| PIN | Foreldre | Uten PIN | Låst hele tiden | Rømming | Reboot |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        out.append("| {rel} | {api} | {label} | {avail} | {phone} | {sms} | {camera} "
                   "| {skyss} | {pin} | {parent} | {no_pin} | {lock} | {escape} "
                   "| {reboot} |".format(**r))

    out.append("\n### Lock-task-allowlist per utgave\n")
    out.append("| Android | API | Utgave | Pakker i allowlist (utenom appen selv) |")
    out.append("|---|---|---|---|")
    for r in rows:
        out.append(f"| {r['rel']} | {r['api']} | {r['label']} | {r['allow']} |")

    out.append("\n### Avvik før → etter\n")
    devs = []
    for api, rel in VERSIONS:
        b, f = load(api, "baseline"), load(api, "fixed")
        if not b or not f:
            continue
        for key, getter in (("Ring", lambda d: launch_cell(d, "phone")),
                            ("SMS", lambda d: launch_cell(d, "sms")),
                            ("Kamera", lambda d: launch_cell(d, "camera")),
                            ("Skyss", lambda d: launch_cell(d, "skyss")),
                            ("Rømming", escapes),
                            ("Reboot", reboot_cell),
                            ("Allowlist", lambda d: ", ".join(d["_foreign_allowlist"]) or NA)):
            vb, vf = getter(b), getter(f)
            if vb != vf:
                devs.append(f"- **Android {rel} (API {api}) {key}**: {vb} → {vf}")
    out.append("\n".join(devs) if devs else "- (ingen avvik registrert)")

    # per-version reboot detail, because that is where the boot receiver matters
    out.append("\n### Reboot-detaljer\n")
    out.append("| Android | API | Utgave | Skjermbilde etter reboot | Fliser |")
    out.append("|---|---|---|---|---|")
    for r in rows:
        t = r["raw"].get("tiles", {}).get("after_reboot") or {}
        avail = sum(1 for v in t.values() if v and v != "Ikke her" and v != "TILE MISSING")
        out.append(f"| {r['rel']} | {r['api']} | {r['label']} | {r['reboot']} "
                   f"| {avail}/{len(t)} |" if t else
                   f"| {r['rel']} | {r['api']} | {r['label']} | {r['reboot']} | – |")

    text = "\n".join(out) + "\n"
    print(text)
    if "--write" in sys.argv:
        path = f"{RESULTS}/matrix-data.md"
        with open(path, "w") as f:
            f.write(f"<!-- generated {time.strftime('%Y-%m-%d %H:%M')} "
                    f"by qa/harness/matrix-report.py -->\n\n" + text)
        print("written to", path)


if __name__ == "__main__":
    main()
