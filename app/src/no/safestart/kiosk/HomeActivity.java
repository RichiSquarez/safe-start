package no.safestart.kiosk;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/** The screen the child lives in. Replaces the normal home screen. */
public class HomeActivity extends Activity {
    private Prefs prefs;
    private LinearLayout grid;
    private TextView clock;
    private TextView status;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            updateClock();
            handler.postDelayed(this, 20000L);
        }
    };

    /**
     * Per-tile chip colour. Every chip is a pastel wash of one hue and the glyph
     * is always a darker shade of the same hue, so the grid stays colourful
     * without ever fighting the petrol text.
     */
    private static int accentFor(String key) {
        if (Prefs.KEY_PHONE.equals(key)) {
            return 0xFF2BB98A;   // green, the one tile that is always on
        }
        if (Prefs.KEY_SMS.equals(key)) {
            return 0xFFC3D8F7;   // light blue
        }
        if (Prefs.KEY_CAMERA.equals(key)) {
            return 0xFFDACCF3;   // lavender
        }
        if (Prefs.KEY_MAPS.equals(key)) {
            return 0xFFCBE8C1;   // light green
        }
        if (Prefs.KEY_SKYSS.equals(key)) {
            return 0xFFC2E5F1;   // light cyan
        }
        return 0xFFF1E2C8;       // sand, for the chess bot
    }

    private static int glyphOn(String key) {
        if (Prefs.KEY_PHONE.equals(key)) {
            return Ui.WHITE;     // the only saturated chip, so it takes white
        }
        if (Prefs.KEY_SMS.equals(key)) {
            return 0xFF173B4D;
        }
        if (Prefs.KEY_CAMERA.equals(key)) {
            return 0xFF4B3F72;
        }
        if (Prefs.KEY_MAPS.equals(key)) {
            return 0xFF2C5F3A;
        }
        if (Prefs.KEY_SKYSS.equals(key)) {
            return 0xFF1F5C6B;
        }
        return 0xFF6B4F1F;
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        prefs = new Prefs(this);
        Ui.immersive(this);
        setContentView(build());
        updateClock();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            Ui.immersive(this);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        Ui.immersive(this);
        rebuildGrid();
        updateStatus();
        if (Kiosk.isDeviceOwner(this)) {
            // Lock task mode can only be left by the task that started it, so
            // the parent screen raises Prefs#isUnlocked() and comes back here.
            if (prefs.isUnlocked()) {
                Kiosk.unlock(this);
            } else {
                Kiosk.enter(this, prefs);
            }
        }
        handler.removeCallbacks(tick);
        handler.post(tick);
    }

    @Override
    protected void onPause() {
        super.onPause();
        handler.removeCallbacks(tick);
    }

    @Override
    public void onBackPressed() {
        // The child does not get to leave this screen.
    }

    // ------------------------------------------------------------------ ui
    private View build() {
        FrameLayout root = new FrameLayout(this);
        root.addView(new Backdrop(this), new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        int side = Ui.dp(this, 22);
        col.setPadding(side, Ui.dp(this, 12), side, Ui.dp(this, 10));
        root.addView(col, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        col.addView(header());
        col.addView(greeting());

        ScrollView scroll = new ScrollView(this);
        scroll.setVerticalScrollBarEnabled(false);
        scroll.setClipToPadding(false);
        // fillViewport + weighted rows: the cards stretch to fill the screen
        // instead of leaving a dead band above the footer.
        scroll.setFillViewport(true);
        grid = new LinearLayout(this);
        grid.setOrientation(LinearLayout.VERTICAL);
        grid.setPadding(0, Ui.dp(this, 8), 0, Ui.dp(this, 4));
        grid.setLayoutParams(new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        scroll.addView(grid);
        col.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        col.addView(parentsButton(), new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        col.addView(footer());
        return root;
    }

    /** Shield + wordmark on the left, the clock in a white pill on the right. */
    private View header() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);

        LinearLayout brand = new LinearLayout(this);
        brand.setOrientation(LinearLayout.HORIZONTAL);
        brand.setGravity(Gravity.CENTER_VERTICAL);
        View shield = Ui.icon(this, R.drawable.ic_shield, 19f, Ui.TEAL);
        brand.addView(shield);
        TextView mark = Ui.text(this, "Safestart", 18f, Ui.PETROL, true);
        mark.setLetterSpacing(-0.01f);
        LinearLayout.LayoutParams markLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        markLp.leftMargin = Ui.dp(this, 7);
        brand.addView(mark, markLp);
        row.addView(brand, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        LinearLayout pill = new LinearLayout(this);
        pill.setOrientation(LinearLayout.HORIZONTAL);
        pill.setGravity(Gravity.CENTER_VERTICAL);
        pill.setBackground(Ui.pill(0xF2FFFFFF, 0xFFE7F0EB, this));
        int ph = Ui.dp(this, 11), pv = Ui.dp(this, 6);
        pill.setPadding(ph, pv, ph, pv);

        LinearLayout times = new LinearLayout(this);
        times.setOrientation(LinearLayout.VERTICAL);
        clock = Ui.text(this, "", 16f, Ui.PETROL, true);
        clock.setGravity(Gravity.END);
        times.addView(clock);
        status = Ui.text(this, "", 8f, Ui.MUTED, false);
        status.setGravity(Gravity.END);
        status.setLetterSpacing(0.08f);
        times.addView(status);
        pill.addView(times);

        View lockTiny = Ui.icon(this, R.drawable.ic_lock, 10f, Ui.TEAL);
        LinearLayout.LayoutParams lockLp = new LinearLayout.LayoutParams(
                Ui.dp(this, 10), Ui.dp(this, 10));
        lockLp.leftMargin = Ui.dp(this, 6);
        pill.addView(lockTiny, lockLp);
        row.addView(pill);

        secret(row);
        secret(shield);
        secret(mark);
        secret(pill);
        secret(clock);
        secret(status);
        secret(lockTiny);
        return row;
    }

    private View greeting() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = Ui.dp(this, 10);
        box.setLayoutParams(lp);

        TextView hei = Ui.text(this, "Hei!", 26f, Ui.PETROL, true);
        hei.setLetterSpacing(-0.02f);
        box.addView(hei);
        TextView sub = Ui.text(this, "Hva vil du gj\u00f8re?", 13f, Ui.MUTED, false);
        sub.setPadding(0, Ui.dp(this, 2), 0, 0);
        box.addView(sub);
        secret(box);
        secret(hei);
        secret(sub);
        return box;
    }

    private void rebuildGrid() {
        if (grid == null) {
            return;
        }
        grid.removeAllViews();
        java.util.List<Catalog.Item> items = Catalog.visible(this, prefs);

        // Cards stay the size of their content; the leftover height becomes even
        // breathing room between the rows, so the grid always fills the screen.
        java.util.List<LinearLayout> rows = new java.util.ArrayList<>();
        LinearLayout row = null;
        for (int i = 0; i < items.size(); i++) {
            if (i % 2 == 0) {
                row = new LinearLayout(this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                rows.add(row);
            }
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
            lp.rightMargin = Ui.dp(this, 9);
            row.addView(tile(items.get(i)), lp);
        }
        if (row != null && items.size() % 2 == 1) {
            row.addView(new View(this), new LinearLayout.LayoutParams(0,
                    ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        }

        for (int r = 0; r < rows.size(); r++) {
            if (r > 0) {
                grid.addView(new View(this), new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(this, 10)));
            }
            grid.addView(rows.get(r), new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        }
    }

    /** One card: coloured glyph chip, a quiet arrow, the word, the promise. */
    private View tile(final Catalog.Item it) {
        boolean installed = Catalog.available(this, it, prefs);
        int accent = accentFor(it.key);

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(Ui.box(0xF5FFFFFF,
                it.always ? 0xFF7FCCB4 : 0xFFE2EFE9, 24f, this));
        int p = Ui.dp(this, 12);
        card.setPadding(p, p, p, p);
        card.setMinimumHeight(Ui.dp(this, 122));
        card.setClickable(true);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);

        LinearLayout chip = new LinearLayout(this);
        chip.setOrientation(LinearLayout.VERTICAL);
        chip.setGravity(Gravity.CENTER);
        chip.setBackground(Ui.chip(installed ? accent : 0x66C8E2D8, 15f, this));
        chip.addView(Ui.icon(this, it.icon, 22f,
                installed ? glyphOn(it.key) : Ui.MUTED));
        top.addView(chip, new LinearLayout.LayoutParams(
                Ui.dp(this, 42), Ui.dp(this, 42)));
        top.addView(new View(this), new LinearLayout.LayoutParams(0, 1, 1f));

        if (installed) {
            LinearLayout arrow = new LinearLayout(this);
            arrow.setOrientation(LinearLayout.VERTICAL);
            arrow.setGravity(Gravity.CENTER);
            arrow.setBackground(Ui.chip(0x0D173B4D, 14f, this));
            arrow.addView(Ui.icon(this, R.drawable.ic_arrow, 13f, Ui.PETROL));
            top.addView(arrow, new LinearLayout.LayoutParams(
                    Ui.dp(this, 28), Ui.dp(this, 28)));
        }
        card.addView(top, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT));
        // icon at the top, words at the bottom: the card breathes like the mockup
        card.addView(new View(this), new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        TextView label = Ui.text(this, it.label, 16f,
                installed ? Ui.PETROL : Ui.MUTED, true);
        label.setPadding(0, Ui.dp(this, 6), 0, 0);
        card.addView(label);

        String subText = installed ? it.sub : "Ikke her";
        TextView sub = Ui.text(this, subText, 11f,
                it.always ? Ui.TEAL : Ui.MUTED, it.always);
        if (it.always) {
            sub.setLetterSpacing(0.04f);
        }
        sub.setPadding(0, Ui.dp(this, 1), 0, 0);
        card.addView(sub);

        card.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (!Catalog.launch(HomeActivity.this, it, prefs)) {
                    Toast.makeText(HomeActivity.this,
                            it.label + " er ikke tilgjengelig her", Toast.LENGTH_SHORT).show();
                }
            }
        });
        secret(card);
        return card;
    }

    /** The one promise, in a white pill. The lock on the right is the parent door. */
    /**
     * A visible door to the parent area. The child may open it, but only the
     * PIN gets past it, and the lockout makes guessing useless.
     */
    private View parentsButton() {
        LinearLayout b = new LinearLayout(this);
        b.setOrientation(LinearLayout.HORIZONTAL);
        b.setGravity(Gravity.CENTER_VERTICAL);
        b.setBackground(Ui.pill(0xFFFFF1DE, 0xEEFFD9AB, this));
        int p = Ui.dp(this, 8);
        b.setPadding(p + Ui.dp(this, 6), p, p + Ui.dp(this, 6), p);
        b.setClickable(true);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = Ui.dp(this, 10);
        b.setLayoutParams(lp);

        LinearLayout chip = new LinearLayout(this);
        chip.setOrientation(LinearLayout.VERTICAL);
        chip.setGravity(Gravity.CENTER);
        chip.setBackground(Ui.chip(0xFFFFD9AB, 13f, this));
        chip.addView(Ui.icon(this, R.drawable.ic_heart, 18f, 0xFF8A5A1F));
        b.addView(chip, new LinearLayout.LayoutParams(
                Ui.dp(this, 34), Ui.dp(this, 34)));

        LinearLayout words = new LinearLayout(this);
        words.setOrientation(LinearLayout.VERTICAL);
        words.setPadding(Ui.dp(this, 11), 0, 0, 0);
        words.addView(Ui.text(this, "Mamma & Pappa", 14f, 0xFF6B4A16, true));
        words.addView(Ui.text(this, "Ett trykk ringer hjem", 9.5f, 0xFF9A7A46, false));
        b.addView(words, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        b.addView(Ui.icon(this, R.drawable.ic_lock, 14f, 0xFF8A5A1F));
        b.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String num = prefs.parentNumber();
                if (num.length() < 3) {
                    android.widget.Toast.makeText(HomeActivity.this,
                            "Sett nummeret i foreldremenyen f\u00f8rst",
                            android.widget.Toast.LENGTH_LONG).show();
                    askPin();
                    return;
                }
                boolean canCall = checkSelfPermission(
                        android.Manifest.permission.CALL_PHONE)
                        == android.content.pm.PackageManager.PERMISSION_GRANTED;
                Intent call = new Intent(canCall ? Intent.ACTION_CALL : Intent.ACTION_DIAL,
                        android.net.Uri.parse("tel:" + num));
                try {
                    startActivity(call);
                } catch (Throwable t) {
                    askPin();
                }
            }
        });
        secret(b);
        return b;
    }

    private View footer() {
        LinearLayout pill = new LinearLayout(this);
        pill.setOrientation(LinearLayout.HORIZONTAL);
        pill.setGravity(Gravity.CENTER_VERTICAL);
        pill.setBackground(Ui.pill(0xF2FFFFFF, 0xFFE7F0EB, this));
        int ph = Ui.dp(this, 13), pv = Ui.dp(this, 8);
        pill.setPadding(ph, pv, ph, pv);

        pill.addView(Ui.icon(this, R.drawable.ic_shield, 14f, Ui.TEAL));

        View dot = new View(this);
        dot.setBackground(Ui.pill(Ui.PEACH, 0, this));
        LinearLayout.LayoutParams dotLp = new LinearLayout.LayoutParams(
                Ui.dp(this, 5), Ui.dp(this, 5));
        dotLp.leftMargin = Ui.dp(this, 7);
        pill.addView(dot, dotLp);

        TextView hint = Ui.text(this, "Telefonen virker alltid.", 11f, Ui.BODY, false);
        LinearLayout.LayoutParams hintLp = new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        hintLp.leftMargin = Ui.dp(this, 7);
        pill.addView(hint, hintLp);

        View door = Ui.icon(this, R.drawable.ic_lock, 14f, 0x66173B4D);
        pill.addView(door);

        secret(pill);
        secret(hint);
        door.setOnLongClickListener(new View.OnLongClickListener() {
            @Override
            public boolean onLongClick(View v) {
                askPin();
                return true;
            }
        });
        return pill;
    }

    /** Long press anywhere quiet is the door. Invisible to a child, obvious to a parent. */
    private void secret(View v) {
        v.setOnLongClickListener(new View.OnLongClickListener() {
            @Override
            public boolean onLongClick(View x) {
                askPin();
                return true;
            }
        });
    }

    private void updateClock() {
        if (clock != null) {
            clock.setText(new SimpleDateFormat("HH:mm", new Locale("nb", "NO"))
                    .format(new Date()));
        }
    }

    private void updateStatus() {
        if (status == null) {
            return;
        }
        String s;
        if (Kiosk.isDeviceOwner(this)) {
            s = Kiosk.isLocked(this) ? "L\u00c5ST" : "VENTER";
        } else if (Kiosk.isAdminActive(this)) {
            s = "ADMIN";
        } else {
            s = "IKKE L\u00c5ST";
        }
        status.setText(s);
        status.setTextColor(Kiosk.isDeviceOwner(this) ? Ui.TEAL : Ui.MUTED);
    }

    private void askPin() {
        PinDialog d = new PinDialog(this, prefs, new PinDialog.Listener() {
            @Override
            public void onPin(String pin) {
                Kiosk.openDoor();
                startActivity(new Intent(HomeActivity.this, ParentActivity.class));
            }
        });
        d.show();
    }
}
