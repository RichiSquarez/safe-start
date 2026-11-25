package no.skyss.billett;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Stand-in for the real Skyss ticket app (QA harness only).
 *
 * The package name matches Catalog.skyssPackage()'s first candidate, so it
 * exercises the <package> entries in the app's <queries> block: on Android 11+
 * without those entries the Skyss tile stays "Ikke her" and the package never
 * reaches the lock-task allowlist.
 */
public class MainActivity extends Activity {

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.parseColor("#C2E5F1"));

        TextView h = new TextView(this);
        h.setText("QA SKYSS");
        h.setTextSize(30f);
        h.setTextColor(Color.parseColor("#173B4D"));
        h.setGravity(Gravity.CENTER);
        root.addView(h);

        TextView d = new TextView(this);
        d.setText("no.skyss.billett / MainActivity");
        d.setTextSize(13f);
        d.setTextColor(Color.parseColor("#49636B"));
        d.setGravity(Gravity.CENTER);
        root.addView(d);

        setContentView(root);
    }
}
