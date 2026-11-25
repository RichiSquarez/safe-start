package no.safestart.kiosk;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.view.View;

/**
 * The home background: paper, plus a few very large, very faint blobs.
 * Kept as a plain View so the whole look is one Canvas pass and needs no assets.
 */
final class Backdrop extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private Shader[] shaders = new Shader[0];
    private float[] xs = new float[0];
    private float[] ys = new float[0];
    private float[] rs = new float[0];

    /** cx/cy are fractions of the view size, r is a fraction of the width. */
    private static final float[][] BLOBS = {
            // cx,   cy,   r
            {0.02f, 0.00f, 0.78f},
            {1.06f, 0.22f, 0.90f},
            {0.10f, 1.02f, 0.90f},
            {0.86f, 0.92f, 0.70f},
    };

    private static final int[] COLOURS = {
            0x77C8E2D8,
            0x4AA9CFC4,
            0x3DFFD19A,
            0x46DDF1E9,
    };

    Backdrop(Context c) {
        super(c);
        setWillNotDraw(false);
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        int n = BLOBS.length;
        shaders = new Shader[n];
        xs = new float[n];
        ys = new float[n];
        rs = new float[n];
        for (int i = 0; i < n; i++) {
            xs[i] = BLOBS[i][0] * w;
            ys[i] = BLOBS[i][1] * h;
            rs[i] = Math.max(1f, BLOBS[i][2] * w);
            shaders[i] = new RadialGradient(xs[i], ys[i], rs[i],
                    COLOURS[i], Color.TRANSPARENT, Shader.TileMode.CLAMP);
        }
    }

    @Override
    protected void onDraw(Canvas c) {
        c.drawColor(Ui.PAPER);
        for (int i = 0; i < shaders.length; i++) {
            paint.setShader(shaders[i]);
            c.drawCircle(xs[i], ys[i], rs[i], paint);
        }
        paint.setShader(null);
    }
}
