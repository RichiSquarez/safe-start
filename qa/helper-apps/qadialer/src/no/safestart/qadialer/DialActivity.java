package no.safestart.qadialer;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Stand-in dialer used by the QA harness only.
 *
 * The AOSP "default" emulator images ship without a Phone app, so
 * Catalog.resolvePackage() finds nothing for ACTION_DIAL and the Ring tile can
 * never be opened. This activity gives the harness a deterministic target: it
 * is a separate, third-party package, which is exactly the case package
 * visibility filters out on Android 11+ unless <queries> is declared.
 */
public class DialActivity extends Activity {

    static LinearLayout ui(Activity a, String headline, String detail) {
        LinearLayout root = new LinearLayout(a);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.parseColor("#F7FAF8"));

        TextView h = new TextView(a);
        h.setText(headline);
        h.setTextSize(30f);
        h.setTextColor(Color.parseColor("#173B4D"));
        h.setGravity(Gravity.CENTER);
        root.addView(h);

        TextView d = new TextView(a);
        d.setText(detail);
        d.setTextSize(14f);
        d.setTextColor(Color.parseColor("#49636B"));
        d.setGravity(Gravity.CENTER);
        root.addView(d);
        return root;
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        String data = getIntent() != null && getIntent().getData() != null
                ? getIntent().getDataString() : "(uten nummer)";
        setContentView(ui(this, "QA DIALER", getIntent().getAction() + "\n" + data));
    }
}
