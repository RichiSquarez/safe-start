package no.safestart.kiosk;

import android.app.Dialog;
import android.content.Context;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Locale;

/**
 * Numeric PIN pad drawn by the app itself. We do not rely on the system keyboard,
 * because inside lock task mode the child never gets to a keyboard we control.
 */
final class PinDialog extends Dialog {
    interface Listener {
        void onPin(String pin);
    }

    private final Prefs prefs;
    private final Listener listener;
    private final StringBuilder entry = new StringBuilder();
    private TextView dots;
    private TextView error;

    PinDialog(Context c, Prefs prefs, Listener listener) {
        super(c);
        this.prefs = prefs;
        this.listener = listener;
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(getContext());
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Ui.PAPER);
        int pad = Ui.dp(getContext(), 24);
        root.setPadding(pad, pad, pad, pad);

        root.addView(Ui.eyebrow(getContext(), "Foreldre"));
        TextView title = Ui.text(getContext(), "Skriv PIN-koden", 22f, Ui.PETROL, true);
        title.setPadding(0, Ui.dp(getContext(), 6), 0, 0);
        root.addView(title);

        dots = Ui.text(getContext(), "", 30f, Ui.TEAL, true);
        dots.setGravity(Gravity.CENTER);
        dots.setLetterSpacing(0.3f);
        dots.setPadding(0, Ui.dp(getContext(), 14), 0, Ui.dp(getContext(), 4));
        root.addView(dots);

        error = Ui.text(getContext(), " ", 12f, 0xFFB3261E, false);
        error.setGravity(Gravity.CENTER);
        root.addView(error);

        int keyW = Ui.dp(getContext(), 76);
        int keyH = Ui.dp(getContext(), 56);
        String[][] keys = {{"1", "2", "3"}, {"4", "5", "6"}, {"7", "8", "9"}, {"", "0", "\u232B"}};
        for (String[] row : keys) {
            LinearLayout line = new LinearLayout(getContext());
            line.setOrientation(LinearLayout.HORIZONTAL);
            line.setGravity(Gravity.CENTER);
            for (final String k : row) {
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(keyW, keyH);
                lp.setMargins(Ui.dp(getContext(), 4), Ui.dp(getContext(), 4),
                        Ui.dp(getContext(), 4), Ui.dp(getContext(), 4));
                if (k.length() == 0) {
                    View filler = new View(getContext());
                    line.addView(filler, lp);
                    continue;
                }
                Button btn = new Button(getContext());
                btn.setText(k);
                btn.setTextSize(20f);
                btn.setAllCaps(false);
                btn.setTextColor(Ui.PETROL);
                btn.setBackground(Ui.box(Ui.WHITE, Ui.RULE, 10f, getContext()));
                btn.setPadding(0, 0, 0, 0);
                btn.setOnClickListener(new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        onKey(k);
                    }
                });
                line.addView(btn, lp);
            }
            root.addView(line);
        }

        Button cancel = new Button(getContext());
        cancel.setText("Avbryt");
        cancel.setAllCaps(false);
        cancel.setTextColor(Ui.MUTED);
        cancel.setBackgroundColor(0x00000000);
        cancel.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                dismiss();
            }
        });
        root.addView(cancel, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, Ui.dp(getContext(), 44)));

        setContentView(root);
        render();
    }

    private void onKey(String k) {
        long until = prefs.lockedUntil();
        if (until > System.currentTimeMillis()) {
            long secs = Math.max(1, (until - System.currentTimeMillis()) / 1000);
            error.setText(String.format(Locale.US, "For mange fors\u00f8k. Vent %d sek.", secs));
            return;
        }
        if ("\u232B".equals(k)) {
            if (entry.length() > 0) {
                entry.deleteCharAt(entry.length() - 1);
            }
        } else {
            boolean full = entry.length() >= prefs.pinLength();
            if (!full) {
                entry.append(k);
            }
        }
        render();
        // Judge the PIN the moment it is as long as the stored one: a wrong
        // 4-digit try has to count as a failure, otherwise a child can walk
        // through all 10 000 combinations without ever hitting the lockout.
        if (entry.length() == prefs.pinLength()) {
            if (prefs.checkPin(entry.toString())) {
                prefs.clearFails();
                dismiss();
                listener.onPin(entry.toString());
            } else {
                fail();
            }
        }
    }

    private void fail() {
        entry.setLength(0);
        long until = prefs.registerFail();
        if (until > System.currentTimeMillis()) {
            error.setText("For mange fors\u00f8k. Vent 30 sek.");
        } else {
            error.setText("Feil PIN");
        }
        render();
    }

    private void render() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < entry.length(); i++) {
            sb.append("\u2022 ");
        }
        for (int i = entry.length(); i < 4; i++) {
            sb.append("\u2013 ");
        }
        dots.setText(sb.toString().trim());
    }
}
