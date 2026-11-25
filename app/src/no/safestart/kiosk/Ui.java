package no.safestart.kiosk;

import android.content.Context;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.util.TypedValue;
import android.widget.TextView;

/** Small design helpers so the test build uses the real Safestart palette. */
final class Ui {
    static final int PETROL = 0xFF173B4D;
    static final int TEAL = 0xFF116B65;
    static final int PAPER = 0xFFF7FAF8;
    static final int MINT = 0xFFDDF1E9;
    static final int MINT2 = 0xFFC8E2D8;
    static final int PEACH = 0xFFFFD19A;
    static final int BODY = 0xFF49636B;
    static final int MUTED = 0xFF6E8586;
    static final int RULE = 0xFFD9E8E3;
    static final int WHITE = 0xFFFFFFFF;

    private Ui() {}

    static int dp(Context c, float v) {
        return Math.round(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v,
                c.getResources().getDisplayMetrics()));
    }

    static GradientDrawable box(int fill, int stroke, float radiusDp, Context c) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(dp(c, radiusDp));
        if (stroke != 0) {
            g.setStroke(Math.max(1, dp(c, 1)), stroke);
        }
        return g;
    }

    /** Full-bleed kiosk look: no status bar, no navigation bar, no peeking. */
    static void immersive(android.app.Activity a) {
        android.view.View d = a.getWindow().getDecorView();
        d.setSystemUiVisibility(android.view.View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | android.view.View.SYSTEM_UI_FLAG_FULLSCREEN
                | android.view.View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | android.view.View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | android.view.View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | android.view.View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
    }

    /** Fully rounded shape, for clocks, status pills and the footer. */
    static GradientDrawable pill(int fill, int stroke, Context c) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(999f);
        if (stroke != 0) {
            g.setStroke(Math.max(1, dp(c, 1)), stroke);
        }
        return g;
    }

    /** A round chip that holds one glyph, used for tile icons. */
    static GradientDrawable chip(int fill, float radiusDp, Context c) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(dp(c, radiusDp));
        return g;
    }

    static TextView text(Context c, String t, float sp, int color, boolean bold) {
        TextView v = new TextView(c);
        v.setText(t);
        v.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        v.setTextColor(color);
        v.setLineSpacing(dp(c, 2), 1f);
        if (bold) {
            v.setTypeface(Typeface.DEFAULT_BOLD);
        }
        return v;
    }

    static TextView eyebrow(Context c, String t) {
        TextView v = text(c, t.toUpperCase(java.util.Locale.ROOT), 10f, TEAL, true);
        v.setLetterSpacing(0.16f);
        return v;
    }

    /** A flat glyph from res/drawable-xxhdpi, tinted in one colour. */
    static android.widget.ImageView icon(Context c, int res, float sizeDp, int tint) {
        android.widget.ImageView v = new android.widget.ImageView(c);
        v.setImageResource(res);
        v.setScaleType(android.widget.ImageView.ScaleType.FIT_CENTER);
        v.setColorFilter(tint);
        LinearLayoutParams(v, sizeDp, c);
        return v;
    }

    private static void LinearLayoutParams(android.widget.ImageView v, float sizeDp, Context c) {
        android.widget.LinearLayout.LayoutParams lp = new android.widget.LinearLayout.LayoutParams(
                dp(c, sizeDp), dp(c, sizeDp));
        v.setLayoutParams(lp);
    }
}
