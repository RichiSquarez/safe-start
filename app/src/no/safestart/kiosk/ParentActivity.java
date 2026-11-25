package no.safestart.kiosk;

import android.app.Activity;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

/** Everything the parent can change. Reachable only through the PIN pad. */
public class ParentActivity extends Activity {
    private Prefs prefs;
    private LinearLayout list;
    private TextView statusView;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        // Defence in depth: this screen must only be reached through the PIN pad.
        // Anyone starting the activity directly (adb, another app, a stale intent) gets nothing.
        if (!Kiosk.doorOpen()) {
            finish();
            return;
        }
        prefs = new Prefs(this);
        Ui.immersive(this);
        setContentView(build());
        rebuild();
    }

    private View build() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Ui.PAPER);
        int pad = Ui.dp(this, 24);
        root.setPadding(pad, Ui.dp(this, 22), pad, pad);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout titles = new LinearLayout(this);
        titles.setOrientation(LinearLayout.VERTICAL);
        titles.addView(Ui.eyebrow(this, "Foreldre"));
        TextView h = Ui.text(this, "Innstillinger", 26f, Ui.PETROL, true);
        h.setPadding(0, Ui.dp(this, 6), 0, 0);
        titles.addView(h);
        header.addView(titles, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Button close = new Button(this);
        close.setText("Lukk");
        close.setAllCaps(false);
        close.setTextColor(Ui.PETROL);
        close.setBackground(Ui.box(Ui.MINT, 0, 10f, this));
        close.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        header.addView(close, new LinearLayout.LayoutParams(Ui.dp(this, 88), Ui.dp(this, 44)));
        root.addView(header);

        statusView = Ui.text(this, "", 11f, Ui.MUTED, false);
        statusView.setPadding(0, Ui.dp(this, 10), 0, 0);
        root.addView(statusView);

        ScrollView scroll = new ScrollView(this);
        list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setPadding(0, Ui.dp(this, 16), 0, Ui.dp(this, 8));
        scroll.addView(list);
        root.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        return root;
    }

    private void rebuild() {
        list.removeAllViews();
        statusView.setText(Kiosk.statusLine(this));

        list.addView(sectionTitle("Hva barnet f\u00e5r bruke"));
        for (Catalog.Item it : Catalog.ALL) {
            if (it.always) {
                list.addView(rowLocked(it));
            } else {
                list.addView(row(it));
            }
        }

        list.addView(sectionTitle("PIN-kode"));
        final EditText pin = new EditText(this);
        pin.setHint("Ny PIN (4\u20138 siffer)");
        pin.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        pin.setTextSize(16f);
        pin.setTextColor(Ui.PETROL);
        pin.setBackground(Ui.box(Ui.WHITE, Ui.RULE, 10f, this));
        pin.setPadding(Ui.dp(this, 14), Ui.dp(this, 10), Ui.dp(this, 14), Ui.dp(this, 10));
        LinearLayout.LayoutParams pl = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        pl.topMargin = Ui.dp(this, 8);
        list.addView(pin, pl);

        Button savePin = button("Lagre ny PIN", Ui.PETROL, Ui.WHITE);
        savePin.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String v2 = pin.getText().toString().trim();
                if (v2.length() < 4 || v2.length() > 8) {
                    Toast.makeText(ParentActivity.this, "PIN m\u00e5 v\u00e6re 4\u20138 siffer",
                            Toast.LENGTH_SHORT).show();
                    return;
                }
                prefs.setPin(v2);
                pin.setText("");
                Toast.makeText(ParentActivity.this, "PIN er oppdatert", Toast.LENGTH_SHORT).show();
            }
        });
        list.addView(savePin);

        list.addView(sectionTitle("Mamma & Pappa"));
        final EditText parentNo = new EditText(this);
        parentNo.setHint("Telefonnummer til foreldrene");
        parentNo.setInputType(InputType.TYPE_CLASS_PHONE);
        parentNo.setTextSize(16f);
        parentNo.setTextColor(Ui.PETROL);
        parentNo.setText(prefs.parentNumber());
        parentNo.setBackground(Ui.box(Ui.WHITE, Ui.RULE, 10f, this));
        parentNo.setPadding(Ui.dp(this, 14), Ui.dp(this, 10), Ui.dp(this, 14), Ui.dp(this, 10));
        LinearLayout.LayoutParams nl = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        nl.topMargin = Ui.dp(this, 8);
        list.addView(parentNo, nl);

        Button saveNo = button("Lagre nummer", Ui.TEAL, Ui.WHITE);
        saveNo.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                prefs.setParentNumber(parentNo.getText().toString());
                Toast.makeText(ParentActivity.this,
                        "Nummeret ligger p\u00e5 Mamma & Pappa-knappen",
                        Toast.LENGTH_SHORT).show();
            }
        });
        list.addView(saveNo);

        Button allowCall = button("Tillat direkte oppringing", Ui.WHITE, Ui.PETROL);
        allowCall.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (android.os.Build.VERSION.SDK_INT >= 23) {
                    requestPermissions(new String[]{android.Manifest.permission.CALL_PHONE}, 7);
                }
            }
        });
        // As Device Owner the permission is granted by Kiosk.lock(), and asking
        // for it again would only bounce the parent to a system dialog that is
        // themselves blocked by lock task.
        if (Kiosk.isDeviceOwner(this)) {
            allowCall.setAlpha(0.45f);
            allowCall.setEnabled(false);
            TextView granted = Ui.text(this,
                    "Direkte oppringing er gitt av Device Owner. Knappen trengs bare "
                            + "n\u00e5r Safestart ikke er Device Owner.", 12f, Ui.MUTED, false);
            list.addView(granted);
        } else {
            list.addView(allowCall);
        }

        list.addView(sectionTitle("L\u00e5sing"));
        TextView explain = Ui.text(this,
                "Med Device Owner kan telefonen l\u00e5ses til Safestart: barnet kommer ikke ut, "
                        + "og du kommer inn med PIN-koden. Uten Device Owner er Safestart bare "
                        + "hjemmeskjermen, og barnet kan bytte til en annen skjerm.",
                12f, Ui.BODY, false);
        LinearLayout.LayoutParams el = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        el.topMargin = Ui.dp(this, 8);
        list.addView(explain, el);

        Button lock = button("L\u00e5s telefonen til Safestart", Ui.TEAL, Ui.WHITE);
        lock.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!Kiosk.isDeviceOwner(ParentActivity.this)) {
                    Toast.makeText(ParentActivity.this,
                            "Device Owner mangler \u2014 se notatet nederst",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                prefs.clearFails();
                // Lower the unlock flag so HomeActivity re-enters lock task as
                // soon as it resumes again.
                prefs.setUnlocked(false);
                finish();
            }
        });
        list.addView(lock);

        Button unlock = button("L\u00e5s opp telefonen", Ui.WHITE, Ui.PETROL);
        unlock.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Lock task mode belongs to HomeActivity's task, so ending it
                // here would be a no-op. Raise the flag and let HomeActivity
                // leave lock task when it resumes.
                prefs.setUnlocked(true);
                Toast.makeText(ParentActivity.this, "Telefonen er l\u00e5st opp",
                        Toast.LENGTH_SHORT).show();
                finish();
            }
        });
        list.addView(unlock);

        list.addView(sectionTitle("Skyss"));
        final EditText pkg = new EditText(this);
        pkg.setHint("Pakkenavn, f.eks. no.skyss.billett");
        pkg.setInputType(InputType.TYPE_CLASS_TEXT);
        pkg.setText(prefs.skyssPackage());
        pkg.setTextSize(14f);
        pkg.setTextColor(Ui.PETROL);
        pkg.setBackground(Ui.box(Ui.WHITE, Ui.RULE, 10f, this));
        pkg.setPadding(Ui.dp(this, 14), Ui.dp(this, 10), Ui.dp(this, 14), Ui.dp(this, 10));
        LinearLayout.LayoutParams kl = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        kl.topMargin = Ui.dp(this, 8);
        list.addView(pkg, kl);

        Button savePkg = button("Lagre pakkenavn", Ui.WHITE, Ui.PETROL);
        savePkg.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                getSharedPreferences("safestart", MODE_PRIVATE).edit()
                        .putString("skyss_pkg", pkg.getText().toString().trim()).apply();
                Toast.makeText(ParentActivity.this, "Lagret", Toast.LENGTH_SHORT).show();
            }
        });
        list.addView(savePkg);

        TextView note = Ui.text(this,
                "Testoppsett: adb shell dpm set-device-owner no.safestart.kiosk/.AdminReceiver "
                        + "(kun p\u00e5 en telefon uten kontoer).",
                10f, Ui.MUTED, false);
        note.setPadding(0, Ui.dp(this, 22), 0, 0);
        list.addView(note);
    }

    private TextView sectionTitle(String t) {
        TextView v = Ui.eyebrow(this, t);
        v.setPadding(0, Ui.dp(this, 22), 0, Ui.dp(this, 6));
        return v;
    }

    private View row(Catalog.Item it) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.HORIZONTAL);
        box.setGravity(Gravity.CENTER_VERTICAL);
        box.setBackground(Ui.box(Ui.WHITE, Ui.RULE, 12f, this));
        int p = Ui.dp(this, 14);
        box.setPadding(p, p, p, p);
        LinearLayout.LayoutParams bl = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        bl.topMargin = Ui.dp(this, 8);
        box.setLayoutParams(bl);

        LinearLayout texts = new LinearLayout(this);
        texts.setOrientation(LinearLayout.VERTICAL);
        texts.addView(Ui.text(this, it.label, 16f, Ui.PETROL, true));
        texts.addView(Ui.text(this, it.sub, 11f, Ui.MUTED, false));
        box.addView(texts, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        Switch sw = new Switch(this);
        sw.setChecked(prefs.isAllowed(it.key));
        sw.setOnCheckedChangeListener(new android.widget.CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(android.widget.CompoundButton b, boolean checked) {
                prefs.setAllowed(it.key, checked);
            }
        });
        box.addView(sw);
        return box;
    }

    private View rowLocked(Catalog.Item it) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.HORIZONTAL);
        box.setGravity(Gravity.CENTER_VERTICAL);
        box.setBackground(Ui.box(Ui.MINT, Ui.PEACH, 12f, this));
        int p = Ui.dp(this, 14);
        box.setPadding(p, p, p, p);
        LinearLayout.LayoutParams bl = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        bl.topMargin = Ui.dp(this, 8);
        box.setLayoutParams(bl);

        LinearLayout texts = new LinearLayout(this);
        texts.setOrientation(LinearLayout.VERTICAL);
        texts.addView(Ui.text(this, it.label, 16f, Ui.PETROL, true));
        texts.addView(Ui.text(this, "Kan ikke sl\u00e5s av \u2014 det er hele poenget",
                11f, Ui.TEAL, false));
        box.addView(texts, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView badge = Ui.text(this, "ALLTID", 10f, Ui.TEAL, true);
        badge.setLetterSpacing(0.12f);
        box.addView(badge);
        return box;
    }

    private Button button(String label, int bg, int fg) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(14f);
        b.setTextColor(fg);
        b.setBackground(Ui.box(bg, bg == Ui.WHITE ? Ui.RULE : 0, 12f, this));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 50));
        lp.topMargin = Ui.dp(this, 10);
        b.setLayoutParams(lp);
        return b;
    }
}
