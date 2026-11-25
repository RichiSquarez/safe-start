#!/usr/bin/env python3
"""One-version QA suite for the Safestart kiosk (no.safestart.kiosk).

usage: python3 suite.py API LABEL APK [--reboot]

Writes evidence (screenshots, UI dumps, dumpsys excerpts, steps.log,
summary.json) into qa/results/apiAPI-LABEL/ and prints the summary JSON.
"""
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = "/Users/panygolf/Documents/ub-mobil"
ADB = ROOT + "/.androidsdk/platform-tools/adb"
PKG = "no.safestart.kiosk"
TILES = [("Ring", "phone"), ("Meldinger", "sms"), ("Kamera", "camera"),
         ("Kart", "maps"), ("Skyss", "skyss"), ("Sjakk", "chess")]
# Stand-in apps: the AOSP "default" images ship no dialer, no messaging app and
# no Skyss, which would make the allowlist / package-visibility path untestable.
HELPERS = [ROOT + "/qa/artifacts/qadialer.apk", ROOT + "/qa/artifacts/qaskyss.apk"]
GRANT_TEXT = ("ALLOW", "Allow", "TILLAT", "Tillat", "While using the app")


def adb(*args, timeout=180, binary=False):
    return subprocess.run([ADB, *args], capture_output=True,
                          text=not binary, timeout=timeout)


class Suite:
    def __init__(self, api, label, apk, reboot):
        self.api, self.label, self.apk, self.reboot = api, label, apk, reboot
        self.dir = f"{ROOT}/qa/results/api{api}-{label}"
        os.makedirs(self.dir, exist_ok=True)
        self.log = open(f"{self.dir}/steps.log", "w")
        self.summary = {"api": api, "label": label, "tiles": {}, "steps": {},
                        "lock": {}, "foreground": {}}
        self.tiles = {}

    # ---------- plumbing ----------
    def say(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        self.log.write(line + "\n")
        self.log.flush()

    def sh(self, cmd, timeout=180):
        r = adb("shell", cmd, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")

    def shot(self, name):
        path = f"{self.dir}/{name}.png"
        with open(path, "wb") as f:
            adb("exec-out", "screencap", "-p", timeout=180, binary=True) \
                if False else subprocess.run(
                    [ADB, "exec-out", "screencap", "-p"], stdout=f, timeout=180)
        self.say("screenshot", name, os.path.getsize(path), "bytes")
        return path

    def ui(self, name):
        self.sh("uiautomator dump /sdcard/ui.xml")
        xml = self.sh("cat /sdcard/ui.xml")
        open(f"{self.dir}/ui-{name}.xml", "w").write(xml)
        nodes = []
        try:
            root = ET.fromstring(xml)
        except Exception as exc:                      # noqa: BLE001
            self.say("!! ui dump unusable for", name, type(exc).__name__)
            return nodes
        for n in root.iter("node"):
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds") or "")
            if not m:
                continue
            x1, y1, x2, y2 = (int(v) for v in m.groups())
            nodes.append({"text": n.get("text") or "", "cls": n.get("class") or "",
                          "id": n.get("resource-id") or "",
                          "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                          "cx": (x1 + x2) // 2, "cy": (y1 + y2) // 2})
        seen = [f"{n['text']!r} @{n['cx']},{n['cy']}" for n in nodes if n["text"]]
        open(f"{self.dir}/texts-{name}.txt", "w").write("\n".join(seen) + "\n")
        self.say("ui", name, "texts:", " | ".join(t.split(" @")[0] for t in seen)[:400])
        return nodes

    def tap(self, x, y, wait=1.2):
        self.sh(f"input tap {x} {y}")
        time.sleep(wait)

    def longpress(self, x, y, wait=1.5):
        self.sh(f"input swipe {x} {y} {x} {y} 1200")
        time.sleep(wait)

    def key(self, code, wait=1.5):
        self.sh(f"input keyevent {code}")
        time.sleep(wait)

    @staticmethod
    def center(nodes, text, cls=None):
        for n in nodes:
            if n["text"] == text and (cls is None or cls in n["cls"]):
                return n["cx"], n["cy"]
        return None

    # ---------- evidence ----------
    def capture_state(self, tag):
        out = []
        for name, cmd in (
                ("lock", "dumpsys activity | grep -i lock"),
                ("policy", "dumpsys device_policy | grep -i -E 'owner|lock task|status'"),
                ("fg", "dumpsys activity activities | grep -E 'mResumedActivity|mFocusedActivity|ResumedActivity'"),
        ):
            out.append(f"=== {name}: {cmd}")
            out.append(self.sh(cmd).strip())
        text = "\n".join(out)
        open(f"{self.dir}/state-{tag}.txt", "w").write(text + "\n")
        locked = bool(re.search(r"lock ?task[^\n]*(LOCKED|LOCK_TASK_MODE_LOCKED)", text, re.I))
        fg = ""
        m = re.search(r"(?:mResumedActivity|mFocusedActivity|ResumedActivity)[^\n]*?"
                      r"([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)", text)
        if m:
            fg = m.group(1)
        self.summary["lock"][tag] = locked
        self.summary["foreground"][tag] = fg
        self.say(f"[{tag}] lock_task={locked} foreground={fg or '?'}")
        return locked, fg

    def read_tiles(self, nodes, tag):
        found = {}
        for label, key in TILES:
            idx = next((i for i, n in enumerate(nodes) if n["text"] == label), None)
            if idx is None:
                found[key] = "TILE MISSING"
                continue
            lab = nodes[idx]
            sub = ""
            for n in nodes[idx + 1:idx + 6]:
                if n["text"] and n["text"] != label and n["y1"] >= lab["y2"] - 10:
                    sub = n["text"]
                    break
            found[key] = sub
        self.summary["tiles"][tag] = found
        self.say("tiles", tag, json.dumps(found, ensure_ascii=False))
        return found

    def dismiss_overlays(self, tag="00-overlay"):
        """Tap away Android's 'Viewing full screen — GOT IT' note.

        The immersive-mode confirmation covers the top half of the screen on
        first run (seen on 7.0), so every tap on the upper tiles would hit the
        overlay instead of the kiosk. Dismissing it is also a finding in its own
        right: the note tells the child to "swipe down from the top to exit".
        """
        for attempt in range(3):
            nodes = self.ui(f"{tag}-{attempt}" if attempt else tag)
            hit = next((n for n in nodes
                        if n["text"] in ("GOT IT", "Got it", "SKJØNNER",
                                         "Skjønner", "FORSTÅTT", "Continue")), None)
            if not hit:
                return nodes
            self.say("!! system overlay on screen:", hit["text"])
            self.tap(hit["cx"], hit["cy"], wait=1.8)
            self.shot(tag + "-dismissed")
        return self.ui(tag + "-clear")

    @staticmethod
    def on_screen(n):
        return 0 <= n["cy"] <= 1240 and 0 <= n["cx"] <= 700

    def find_tap(self, text, cls=None, tag="find", scrolls=6, wait=2.0):
        """Scroll the current screen until `text` is visible, then tap it."""
        for attempt in range(scrolls + 1):
            nodes = self.ui(f"{tag}-{attempt}" if attempt else tag)
            good = [n for n in nodes
                    if n["text"] == text and (cls is None or cls in n["cls"])
                    and self.on_screen(n)]
            if good:
                self.tap(good[0]["cx"], good[0]["cy"], wait=wait)
                return True
            if attempt < scrolls:
                self.say(f"!! '{text}' is not visible, scrolling down")
                self.sh("input swipe 360 900 360 420 300")
                time.sleep(1.2)
        self.say(f"!! '{text}' not found even after scrolling")
        return False

    def find_edit(self, tag="edit", scrolls=6, want=None):
        """Scroll until an editable field is visible; return (nodes, field).

        `want` matches the field's text/hint, because the parent screen has two
        EditTexts and the first on screen is the new-PIN field, not the phone
        number.
        """
        nodes = []
        for attempt in range(scrolls + 1):
            nodes = self.ui(f"{tag}-{attempt}")
            edits = [n for n in nodes
                     if "EditText" in n["cls"] and self.on_screen(n)]
            if want:
                edits = [n for n in edits if want.lower() in n["text"].lower()]
            if edits:
                return nodes, edits[-1]
            if attempt < scrolls:
                self.say("!! wanted edit field not visible, scrolling down")
                self.sh("input swipe 360 900 360 420 300")
                time.sleep(1.2)
        return nodes, None

    def has_handler(self, args):
        """True when the shell (no visibility filtering) resolves a default app."""
        out = self.sh("cmd package resolve-activity --brief " + args).strip()
        line = out.splitlines()[-1].strip() if out else ""
        return "/" in line and not line.startswith("android/")

    def logcat(self, tag):
        out = self.sh(f"logcat -d -s Safestart:V | tail -60")
        open(f"{self.dir}/logcat-{tag}.txt", "w").write(out + "\n")
        allow = [l for l in out.splitlines() if "allowlist" in l]
        if allow:
            self.say("logcat allowlist:", allow[-2].strip()[:300])
        return out

    def probe_tile(self, label, key, nodes):
        """Tap an app tile and record whether it actually opened."""
        nodes = self.dismiss_overlays("probe-" + key)
        c = self.center(nodes, label)
        if c is None:
            self.summary["steps"]["launch_" + key] = "TILE MISSING"
            self.say(f"!! tile {label} not on screen")
            return
        before = self.capture_state("tile-" + key + "-before")[1]
        self.tap(*c, wait=4.0)
        self.shot(f"tile-{key}")
        nodes = self.ui(f"tile-{key}")
        locked, fg = self.capture_state("tile-" + key)
        if fg and "GrantPermissions" in fg:
            # the target app itself asks for a runtime permission on first run;
            # answer it so the screenshot shows the app, not the system dialog
            for attempt in range(4):
                nodes = self.ui(f"tile-{key}-grant{attempt}")
                hit = next((n for n in nodes
                            if n["text"] in GRANT_TEXT and n["cls"].endswith("Button")),
                           None)
                if not hit:
                    break
                self.tap(hit["cx"], hit["cy"], wait=2.5)
                locked, fg = self.capture_state("tile-" + key + "-grant" + str(attempt))
                if fg and "GrantPermissions" not in fg:
                    break
            self.shot(f"tile-{key}-granted")
            self.ui(f"tile-{key}-granted")
        opened = bool(fg) and not fg.startswith(PKG) and fg != before
        self.summary["steps"]["launch_" + key] = "opened " + (fg or "?") if opened \
            else "BLOCKED (still " + (fg or "?") + ")"
        self.say(f"[tile {label}] -> {fg or '?'} opened={opened}")
        self.key(4, 2.0)                    # BACK out of the app if it opened
        self.sh(f"am start -n {PKG}/.HomeActivity")
        time.sleep(1.5)

    # ---------- steps ----------
    def choose_home(self, tag="00-chooser"):
        """Dismiss the 'Select a Home app' dialog if Android shows one."""
        for _ in range(3):
            nodes = self.ui(tag)
            if not any("Select a Home app" in n["text"] for n in nodes):
                return nodes
            self.say("!! home chooser on screen, picking Safestart")
            c = self.center(nodes, "Safestart")
            if c:
                self.tap(*c, wait=1.2)
            nodes = self.ui(tag + "-b")
            c = self.center(nodes, "ALWAYS") or self.center(nodes, "JUST ONCE")
            if c:
                self.tap(*c, wait=2.5)
        return self.dismiss_overlays(tag + "-c")

    def run(self):
        self.say("=== api", self.api, "label", self.label, "apk", os.path.basename(self.apk))
        for prop in ("ro.build.version.release", "ro.build.version.sdk",
                     "ro.build.version.security_patch", "ro.build.fingerprint"):
            self.say(prop, "=", self.sh("getprop " + prop).strip())

        inst = adb("install", "-r", "-g", self.apk, timeout=300)
        self.say("install:", (inst.stdout + inst.stderr).strip().replace("\n", " "))

        for helper in HELPERS:
            if not os.path.exists(helper):
                self.say("!! helper missing:", helper)
                continue
            base = os.path.basename(helper)
            # The stand-in dialer must only be installed when the image has no
            # real DIAL / APP_MESSAGING handler. With two handlers
            # PackageManager.resolveActivity() returns ResolverActivity, whose
            # package is "android", and the kiosk then allowlists the wrong
            # package — an artefact of the harness, not a real defect.
            if base.startswith("qadialer") and self.has_handler(
                    "-a android.intent.action.DIAL -c android.intent.category.DEFAULT -d tel:") \
                    and self.has_handler(
                    "-a android.intent.action.MAIN -c android.intent.category.APP_MESSAGING"):
                self.say("helper", base, ": skipped, image has its own dialer+messaging")
                continue
            r = adb("install", "-r", "-g", helper, timeout=300)
            self.say("helper", base, ":",
                     (r.stdout + r.stderr).strip().replace("\n", " "))

        # the AOSP camera asks for its runtime permission on first launch, which
        # would otherwise show a system dialog instead of the camera in the
        # lock-task screenshot
        cam = self.sh("cmd package resolve-activity --brief "
                      "-a android.media.action.STILL_IMAGE_CAMERA").strip()
        campkg = cam.split("/")[0].strip() if "/" in cam else ""
        for perm in ("android.permission.CAMERA", "android.permission.RECORD_AUDIO",
                     "android.permission.WRITE_EXTERNAL_STORAGE",
                     "android.permission.READ_EXTERNAL_STORAGE"):
            if campkg:
                self.sh("pm grant %s %s" % (campkg, perm))
        self.say("camera package:", campkg or "?")

        # Android 7/8 show a "Viewing full screen — To exit, swipe down from the
        # top — GOT IT" cling the first time an app hides the system bars. It is
        # a separate system window: uiautomator cannot see it, but it swallows
        # the taps on the top row of tiles. Pre-confirm it the way the framework
        # stores the user's tap. (Also a finding: the cling literally teaches the
        # child an exit gesture.)
        self.sh("settings put secure immersive_mode_confirmations confirmed")

        dpm = self.sh("dpm set-device-owner %s/.AdminReceiver" % PKG, timeout=120)
        self.say("dpm set-device-owner:", dpm.strip().replace("\n", " "))

        # 1. launch as HOME
        self.sh(f"am start -n {PKG}/.HomeActivity")
        time.sleep(3.0)
        self.choose_home()                   # settle the HOME-app chooser once
        self.sh(f"am force-stop {PKG}")
        self.key(3, 4)                       # KEYCODE_HOME
        nodes = self.choose_home("01-chooser")
        self.shot("01-home")
        self.tiles["home"] = self.read_tiles(nodes, "home")
        self.capture_state("home")
        self.logcat("home")

        # The app enters lock task from onResume, so a state read taken right
        # after HOME can catch it mid-flight and report "unlocked" even though
        # the kiosk is about to lock. Wait for the lock before measuring.
        for _ in range(15):
            if self.summary["lock"].get("home"):
                break
            time.sleep(1.0)
            self.capture_state("home")
        self.say("lock task after wait:", self.summary["lock"].get("home"))

        # 1b. the core promise: can the child still call and text? ----------
        self.summary["steps"]["lock_task_at_start"] = self.summary["lock"]["home"]
        for label, key in (("Ring", "phone"), ("Meldinger", "sms"),
                           ("Kamera", "camera"), ("Skyss", "skyss")):
            self.probe_tile(label, key, nodes)
        nodes = self.ui("01b-home-back")
        self.capture_state("after-tile-probes")

        # 2. internal ChessActivity must open inside lock task and come back
        c = self.center(nodes, "Sjakk")
        if c:
            self.tap(*c, wait=3.5)
            self.shot("02-chess")
            self.ui("02-chess")
            self.capture_state("chess")
            self.key(4, 2.5)                 # BACK
            self.capture_state("after-chess")

        # 3. escape attempts -------------------------------------------------
        self.key(3, 3)                       # HOME
        self.shot("03-after-home")
        nodes = self.ui("03-after-home")
        self.capture_state("escape-home")

        self.key(187, 2.5)                   # APP_SWITCH / recents
        self.shot("04-recents")
        self.ui("04-recents")
        self.capture_state("escape-recents")

        self.sh("input swipe 360 2 360 900 300")   # pull the status bar down
        time.sleep(2.5)
        self.shot("05-statusbar")
        self.ui("05-statusbar")
        self.capture_state("escape-statusbar")

        self.key(4, 2)                       # BACK
        self.capture_state("escape-back")

        # a foreign app must not be reachable
        self.sh("am start -n com.android.settings/.Settings")
        time.sleep(3)
        self.shot("06-foreign-app")
        self.ui("06-foreign-app")
        self.capture_state("foreign-app")
        self.key(4, 2)

        # 4. parent door: long press, PIN, settings ---------------------------
        self.key(3, 3)
        nodes = self.ui("07-home-again")
        door = self.center(nodes, "Safestart") or (200, 60)
        self.longpress(*door)
        nodes = self.ui("08-pin")
        self.shot("08-pin")
        self.summary["steps"]["pin_dialog"] = any("PIN" in n["text"] for n in nodes)
        for digit in "1234":
            c = self.center(nodes, digit, cls="Button")
            if c is None:
                self.say("!! PIN digit missing:", digit)
                break
            self.tap(*c, wait=0.7)
        time.sleep(2)
        nodes = self.ui("09-parent")
        self.shot("09-parent")
        self.summary["steps"]["parent_reached"] = any(
            n["text"] == "Innstillinger" for n in nodes)
        self.capture_state("parent")

        # direct start of the (unexported) parent activity must be refused.
        # Run it from HOME with the one-shot door token expired, otherwise the
        # test only proves that a door that was just opened is still open.
        close = self.center(nodes, "Lukk", cls="Button")
        if close:
            self.tap(*close, wait=3)
        self.key(3, 3)
        self.say("waiting for the 5 s parent door token to expire")
        time.sleep(7)
        self.capture_state("before-direct")
        self.sh(f"am start -n {PKG}/.ParentActivity")
        time.sleep(2.5)
        nodes2 = self.ui("10-parent-direct")
        self.shot("10-parent-direct")
        self.summary["steps"]["parent_refused_without_pin"] = not any(
            n["text"] == "Innstillinger" for n in nodes2)
        self.say("[parent-direct] refused =",
                 self.summary["steps"]["parent_refused_without_pin"])
        self.capture_state("parent-direct")

        # 5. set the parent number and close --------------------------------
        self.longpress(*(self.center(nodes, "Safestart") or (200, 60)))
        nodes3 = self.ui("10b-pin")
        for digit in "1234":
            c = self.center(nodes3, digit, cls="Button")
            if c is None:
                break
            self.tap(*c, wait=0.7)
        time.sleep(2)
        nodes, field = self.find_edit("10c-parent", want="Telefonnummer")
        self.summary["steps"]["parent_number_field"] = bool(field)
        if field:
            self.say("parent number field at", field["cx"], field["cy"])
            self.tap(field["cx"], field["cy"], wait=1)
            self.sh("input text 40001234")
            time.sleep(1)
            nodes = self.ui("10d-typed")
            typed = any("40001234" in n["text"] for n in nodes)
            self.summary["steps"]["parent_number_typed"] = typed
            self.say("[parent] number typed:", typed)
            if self.find_tap("Lagre nummer", cls="Button", tag="10e-save", wait=2.5):
                self.say("saved parent number")
        self.find_tap("Lukk", cls="Button", tag="10f-close", wait=3)

        # 6. Mamma & Pappa -> dialer (needs tel: visibility + CALL_PHONE) ----
        nodes = self.ui("11-home-number")
        call = self.center(nodes, "Mamma & Pappa")
        if call:
            self.tap(*call, wait=4)
            self.shot("12-call")
            self.ui("12-call")
            self.capture_state("call")
            self.key(4, 2.5)
            self.key(3, 3)

        # 7. unlock from the parent menu ------------------------------------
        nodes = self.ui("13-home-before-unlock")
        self.longpress(*(self.center(nodes, "Safestart") or (200, 60)))
        nodes = self.ui("14-pin2")
        for digit in "1234":
            c = self.center(nodes, digit, cls="Button")
            if c is None:
                break
            self.tap(*c, wait=0.7)
        time.sleep(2)
        self.summary["steps"]["unlock_tapped"] = self.find_tap(
            "Lås opp telefonen", cls="Button", tag="15-parent2", wait=3.5)
        if self.summary["steps"]["unlock_tapped"]:
            self.shot("16-unlocked")
            self.capture_state("unlocked")
        self.key(3, 4)                       # HOME should re-lock
        self.shot("17-relocked")
        self.ui("17-relocked")
        self.capture_state("relocked")

        # 7b. power menu on Android 9+ ---------------------------------------
        # Up to API 27 there is no setLockTaskFeatures, so the global actions
        # (Shut down / Restart / Emergency) come from the platform. From API 28
        # the kiosk can switch them off with LOCK_TASK_FEATURE_NONE — which the
        # fixed build does, and the old build does not.
        if int(self.api) >= 28:
            self.say("long-pressing power to look for the global actions ...")
            self.sh("input keyevent --longpress 26")
            time.sleep(3.0)
            nodes = self.ui("17b-power")
            self.shot("17b-power")
            texts = [n["text"] for n in nodes if n["text"]]
            self.summary["steps"]["power_menu_texts"] = texts
            self.say("[power] texts:", " | ".join(texts)[:240])
            self.key(4, 1.5)                       # BACK closes the dialog
            if "Asleep" in self.sh("dumpsys power | grep -m1 mWakefulness="):
                self.key(26, 1.5)                  # screen back on
                self.key(82, 1.0)
            self.sh(f"am start -n {PKG}/.HomeActivity")
            time.sleep(2)
            self.capture_state("after-power")

        # 8. reboot recovery -------------------------------------------------
        if self.reboot:
            self.say("rebooting ...")
            self.sh("reboot", timeout=30)
            time.sleep(20)
            ok = False
            for _ in range(150):
                r = adb("wait-for-device", timeout=30)
                b = self.sh("getprop sys.boot_completed").strip()
                if b == "1":
                    ok = True
                    break
                time.sleep(2)
            self.say("boot_completed after reboot:", ok)
            time.sleep(10)
            self.key(82, 2)                  # dismiss keyguard
            self.key(3, 4)
            nodes = self.ui("18-after-reboot")
            self.shot("18-after-reboot")
            self.summary["tiles"]["after_reboot"] = self.read_tiles(nodes, "after_reboot")
            self.capture_state("after-reboot")

        json.dump(self.summary, open(f"{self.dir}/summary.json", "w"),
                  ensure_ascii=False, indent=2)
        self.say("=== done", self.dir)
        print("SUMMARY " + json.dumps(self.summary, ensure_ascii=False))
        return self.summary


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("usage: suite.py API LABEL APK [--reboot]")
    api, label, apk = sys.argv[1], sys.argv[2], sys.argv[3]
    reboot = "--reboot" in sys.argv
    Suite(api, label, apk, reboot).run()
