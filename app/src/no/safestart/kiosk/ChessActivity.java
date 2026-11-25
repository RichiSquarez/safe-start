package no.safestart.kiosk;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Sjakk mot en bot. Brettet tegnes med enkle geometriske brikker slik at
 * appen ikke er avhengig av sjakksymboler i systemfonten. Alt holder seg
 * innenfor samme palett som resten av appen.
 */
public class ChessActivity extends Activity {

    private final Handler ui = new Handler(Looper.getMainLooper());
    private ChessEngine engine;
    private BoardView board;
    private TextView statusView;
    private TextView levelView;
    private int level = 1;
    private boolean thinking;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        engine = new ChessEngine();
        engine.reset();
        setContentView(buildUi());
        refresh();
    }

    @Override
    protected void onResume() {
        super.onResume();
        Ui.immersive(this);
    }

    @Override
    public void onBackPressed() {
        finish();
    }

    // ------------------------------------------------------------------ ui

    private View buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Ui.PAPER);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(20), dp(18), dp(20), dp(10));

        LinearLayout titles = new LinearLayout(this);
        titles.setOrientation(LinearLayout.VERTICAL);
        TextView eyebrow = Ui.eyebrow(this, "SAFESTART");
        TextView title = new TextView(this);
        title.setText("Sjakk");
        title.setTextSize(24f);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Ui.PETROL);
        titles.addView(eyebrow);
        titles.addView(title);
        header.addView(titles, new LinearLayout.LayoutParams(0,
                LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        TextView back = new TextView(this);
        back.setText("Tilbake");
        back.setTextSize(12f);
        back.setTypeface(Typeface.DEFAULT_BOLD);
        back.setTextColor(Ui.PETROL);
        back.setGravity(Gravity.CENTER);
        back.setPadding(dp(14), dp(9), dp(14), dp(9));
        back.setBackground(Ui.pill(0xF2FFFFFF, Ui.RULE, this));
        back.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                finish();
            }
        });
        header.addView(back);
        root.addView(header);

        statusView = new TextView(this);
        statusView.setTextSize(13f);
        statusView.setTextColor(Ui.BODY);
        statusView.setPadding(dp(20), 0, dp(20), dp(12));
        root.addView(statusView);

        FrameLayout stage = new FrameLayout(this);
        stage.setPadding(dp(16), 0, dp(16), dp(8));
        board = new BoardView(this);
        stage.addView(board, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT, Gravity.CENTER));
        root.addView(stage, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout footer = new LinearLayout(this);
        footer.setOrientation(LinearLayout.HORIZONTAL);
        footer.setGravity(Gravity.CENTER_VERTICAL);
        footer.setPadding(dp(20), dp(4), dp(20), dp(18));

        levelView = new TextView(this);
        levelView.setTextSize(12f);
        levelView.setTypeface(Typeface.DEFAULT_BOLD);
        levelView.setTextColor(Ui.PETROL);
        levelView.setGravity(Gravity.CENTER);
        levelView.setPadding(dp(16), dp(11), dp(16), dp(11));
        levelView.setBackground(Ui.pill(0xF2FFFFFF, Ui.RULE, this));
        levelView.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                level = level >= 3 ? 1 : level + 1;
                refresh();
            }
        });
        footer.addView(levelView);

        View gap = new View(this);
        footer.addView(gap, new LinearLayout.LayoutParams(0, 1, 1f));

        TextView again = new TextView(this);
        again.setText("Ny runde");
        again.setTextSize(12f);
        again.setTypeface(Typeface.DEFAULT_BOLD);
        again.setTextColor(Ui.WHITE);
        again.setGravity(Gravity.CENTER);
        again.setPadding(dp(18), dp(11), dp(18), dp(11));
        again.setBackground(Ui.pill(Ui.TEAL, Ui.TEAL, this));
        again.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                engine.reset();
                thinking = false;
                board.setSelected(-1);
                refresh();
            }
        });
        footer.addView(again);
        root.addView(footer);

        return root;
    }

    private void refresh() {
        levelView.setText("Niv\u00e5 " + level + " \u00b7 " + levelName(level));
        statusView.setText(statusText());
        board.invalidate();
    }

    private static String levelName(int l) {
        if (l >= 3) {
            return "vanskelig";
        }
        return l == 2 ? "middels" : "lett";
    }

    private String statusText() {
        int st = engine.status();
        if (st == ChessEngine.STATUS_CHECKMATE) {
            return engine.winner() == ChessEngine.WHITE
                    ? "Sjakkmatt \u2013 du vant. Bra spilt."
                    : "Sjakkmatt \u2013 boten vant. Pr\u00f8v igjen.";
        }
        if (st == ChessEngine.STATUS_STALEMATE) {
            return "Patt \u2013 ingen lovlige trekk. Uavgjort.";
        }
        if (st == ChessEngine.STATUS_DRAW) {
            return "Uavgjort.";
        }
        if (thinking) {
            return "Boten tenker \u2026";
        }
        if (engine.inCheck()) {
            return "Sjakk! Du m\u00e5 flytte kongen.";
        }
        return "Din tur. Du spiller hvitt.";
    }

    // --------------------------------------------------------------- moves

    private void onSquare(int sq) {
        if (thinking || engine.status() != ChessEngine.STATUS_PLAYING) {
            return;
        }
        if (engine.turn() != ChessEngine.WHITE) {
            return;
        }
        int sel = board.getSelected();
        if (sel < 0) {
            if (isOurs(sq)) {
                board.setSelected(sq);
            }
            return;
        }
        if (sq == sel) {
            board.setSelected(-1);
            return;
        }
        if (engine.isLegal(sel, sq)) {
            int from = sel;
            board.setSelected(-1);
            engine.move(from, sq);
            refresh();
            if (engine.status() == ChessEngine.STATUS_PLAYING) {
                botTurn();
            }
        } else if (isOurs(sq)) {
            board.setSelected(sq);
        } else {
            board.setSelected(-1);
        }
    }

    private boolean isOurs(int sq) {
        int p = engine.pieceAt(sq);
        return p != ChessEngine.EMPTY && ChessEngine.colorOf(p) == ChessEngine.WHITE;
    }

    private void botTurn() {
        thinking = true;
        refresh();
        final int lvl = level;
        Thread t = new Thread(new Runnable() {
            @Override
            public void run() {
                int[] mv = null;
                try {
                    mv = engine.botMove(lvl);
                } catch (Throwable ignored) {
                    mv = null;
                }
                final int[] play = mv;
                ui.post(new Runnable() {
                    @Override
                    public void run() {
                        thinking = false;
                        if (play != null) {
                            engine.move(play[0], play[1]);
                        }
                        refresh();
                    }
                });
            }
        }, "sjakk-bot");
        t.setDaemon(true);
        t.start();
    }

    private int dp(float v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    // ----------------------------------------------------------- the board

    private final class BoardView extends View {

        private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint glyph = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path acc = new Path();
        private final Path tmp = new Path();
        private int selected = -1;
        private float pad;
        private float cell;

        BoardView(Context c) {
            super(c);
            stroke.setStyle(Paint.Style.STROKE);
            glyph.setStyle(Paint.Style.FILL);
        }

        void setSelected(int sq) {
            selected = sq;
            invalidate();
        }

        int getSelected() {
            return selected;
        }

        @Override
        protected void onMeasure(int wSpec, int hSpec) {
            int w = MeasureSpec.getSize(wSpec);
            int h = MeasureSpec.getSize(hSpec);
            int size = Math.min(w, h);
            if (size <= 0) {
                size = Math.min(getResources().getDisplayMetrics().widthPixels, 900);
            }
            setMeasuredDimension(size, size);
        }

        @Override
        protected void onDraw(Canvas c) {
            int s = getWidth();
            pad = s * 0.022f;
            cell = (s - pad * 2f) / 8f;

            fill.setColor(Ui.WHITE);
            c.drawRoundRect(new RectF(0, 0, s, s), s * 0.05f, s * 0.05f, fill);

            // squares
            for (int sq = 0; sq < 64; sq++) {
                int row = ChessEngine.rowOf(sq);
                int col = ChessEngine.colOf(sq);
                boolean dark = ((row + col) & 1) == 1;
                fill.setColor(dark ? Ui.MINT2 : 0xFFF6FBF8);
                c.drawRect(pad + col * cell, pad + row * cell,
                        pad + (col + 1) * cell, pad + (row + 1) * cell, fill);
            }

            // last move + selection tints
            tint(c, engine.lastFrom(), 0x24116B65);
            tint(c, engine.lastTo(), 0x24116B65);
            tint(c, selected, 0x55FFD19A);

            // legal targets for the selected piece
            if (selected >= 0) {
                int[] moves;
                try {
                    moves = engine.legalMoves(selected);
                } catch (Throwable t) {
                    moves = new int[0];
                }
                for (int i = 0; i < moves.length; i++) {
                    int to = moves[i] >>> 6;
                    float cx = pad + ChessEngine.colOf(to) * cell + cell / 2f;
                    float cy = pad + ChessEngine.rowOf(to) * cell + cell / 2f;
                    if (engine.pieceAt(to) == ChessEngine.EMPTY) {
                        fill.setColor(0x66116B65);
                        c.drawCircle(cx, cy, cell * 0.115f, fill);
                    } else {
                        stroke.setColor(0x99116B65);
                        stroke.setStrokeWidth(Math.max(2f, cell * 0.055f));
                        c.drawCircle(cx, cy, cell * 0.40f, stroke);
                    }
                }
            }

            // pieces
            for (int sq = 0; sq < 64; sq++) {
                int p = engine.pieceAt(sq);
                if (p == ChessEngine.EMPTY) {
                    continue;
                }
                int row = ChessEngine.rowOf(sq);
                int col = ChessEngine.colOf(sq);
                float left = pad + col * cell;
                float top = pad + row * cell;
                drawPiece(c, p, left, top);
            }
        }

        private void tint(Canvas c, int sq, int color) {
            if (sq < 0 || sq > 63) {
                return;
            }
            fill.setColor(color);
            c.drawRect(pad + ChessEngine.colOf(sq) * cell,
                    pad + ChessEngine.rowOf(sq) * cell,
                    pad + (ChessEngine.colOf(sq) + 1) * cell,
                    pad + (ChessEngine.rowOf(sq) + 1) * cell, fill);
        }

        private void drawPiece(Canvas c, int piece, float left, float top) {
            int type = ChessEngine.typeOf(piece);
            boolean white = ChessEngine.colorOf(piece) == ChessEngine.WHITE;
            float s = cell * 0.94f;
            float ox = left + (cell - s) / 2f;
            float oy = top + (cell - s) / 2f;

            acc.reset();
            boolean first = true;
            switch (type) {
                case ChessEngine.PAWN:
                    first = add(circle(ox + .50f * s, oy + .30f * s, .135f * s), first);
                    first = add(poly(ox + .365f * s, oy + .72f * s,
                            ox + .635f * s, oy + .72f * s,
                            ox + .560f * s, oy + .44f * s,
                            ox + .440f * s, oy + .44f * s), first);
                    add(rrect(ox + .275f * s, oy + .72f * s,
                            ox + .725f * s, oy + .83f * s, .05f * s), first);
                    break;
                case ChessEngine.ROOK:
                    first = add(rrect(ox + .340f * s, oy + .32f * s,
                            ox + .660f * s, oy + .73f * s, .035f * s), first);
                    first = add(rrect(ox + .300f * s, oy + .225f * s,
                            ox + .410f * s, oy + .350f * s, .02f * s), first);
                    first = add(rrect(ox + .445f * s, oy + .225f * s,
                            ox + .555f * s, oy + .350f * s, .02f * s), first);
                    first = add(rrect(ox + .590f * s, oy + .225f * s,
                            ox + .700f * s, oy + .350f * s, .02f * s), first);
                    add(rrect(ox + .270f * s, oy + .73f * s,
                            ox + .730f * s, oy + .84f * s, .05f * s), first);
                    break;
                case ChessEngine.KNIGHT:
                    first = add(poly(ox + .225f * s, oy + .420f * s,
                            ox + .340f * s, oy + .265f * s,
                            ox + .480f * s, oy + .220f * s,
                            ox + .560f * s, oy + .120f * s,
                            ox + .615f * s, oy + .260f * s,
                            ox + .740f * s, oy + .460f * s,
                            ox + .760f * s, oy + .720f * s,
                            ox + .400f * s, oy + .720f * s,
                            ox + .455f * s, oy + .560f * s,
                            ox + .300f * s, oy + .500f * s), first);
                    add(rrect(ox + .285f * s, oy + .73f * s,
                            ox + .715f * s, oy + .84f * s, .05f * s), first);
                    break;
                case ChessEngine.BISHOP:
                    first = add(circle(ox + .500f * s, oy + .200f * s, .036f * s), first);
                    first = add(circle(ox + .500f * s, oy + .350f * s, .115f * s), first);
                    first = add(poly(ox + .395f * s, oy + .430f * s,
                            ox + .605f * s, oy + .430f * s,
                            ox + .565f * s, oy + .720f * s,
                            ox + .435f * s, oy + .720f * s), first);
                    add(rrect(ox + .285f * s, oy + .72f * s,
                            ox + .715f * s, oy + .83f * s, .05f * s), first);
                    break;
                case ChessEngine.QUEEN:
                    first = add(poly(ox + .295f * s, oy + .620f * s,
                            ox + .230f * s, oy + .310f * s,
                            ox + .370f * s, oy + .450f * s,
                            ox + .500f * s, oy + .255f * s,
                            ox + .630f * s, oy + .450f * s,
                            ox + .770f * s, oy + .310f * s,
                            ox + .705f * s, oy + .620f * s), first);
                    first = add(poly(ox + .330f * s, oy + .600f * s,
                            ox + .670f * s, oy + .600f * s,
                            ox + .620f * s, oy + .720f * s,
                            ox + .380f * s, oy + .720f * s), first);
                    add(rrect(ox + .270f * s, oy + .72f * s,
                            ox + .730f * s, oy + .84f * s, .05f * s), first);
                    break;
                default: // KING
                    first = add(rrect(ox + .462f * s, oy + .170f * s,
                            ox + .538f * s, oy + .400f * s, .012f * s), first);
                    first = add(rrect(ox + .375f * s, oy + .250f * s,
                            ox + .625f * s, oy + .322f * s, .012f * s), first);
                    first = add(poly(ox + .360f * s, oy + .400f * s,
                            ox + .640f * s, oy + .400f * s,
                            ox + .600f * s, oy + .720f * s,
                            ox + .400f * s, oy + .720f * s), first);
                    add(rrect(ox + .270f * s, oy + .72f * s,
                            ox + .730f * s, oy + .84f * s, .05f * s), first);
                    break;
            }

            if (acc.isEmpty()) {
                return;
            }
            if (white) {
                fill.setColor(Ui.WHITE);
                c.drawPath(acc, fill);
                stroke.setColor(Ui.PETROL);
                stroke.setStrokeWidth(Math.max(1.5f, cell * 0.045f));
                c.drawPath(acc, stroke);
            } else {
                fill.setColor(Ui.PETROL);
                c.drawPath(acc, fill);
            }
        }

        private boolean add(Path p, boolean first) {
            if (p == null) {
                return first;
            }
            if (first) {
                acc.set(p);
                return false;
            }
            tmp.set(p);
            if (!acc.op(tmp, Path.Op.UNION)) {
                acc.addPath(tmp);
            }
            return false;
        }

        private Path circle(float cx, float cy, float r) {
            Path p = new Path();
            p.addCircle(cx, cy, r, Path.Direction.CW);
            return p;
        }

        private Path rrect(float l, float t, float r, float b, float rad) {
            Path p = new Path();
            p.addRoundRect(new RectF(l, t, r, b), rad, rad, Path.Direction.CW);
            return p;
        }

        private Path poly(float... xy) {
            Path p = new Path();
            p.moveTo(xy[0], xy[1]);
            for (int i = 2; i + 1 < xy.length; i += 2) {
                p.lineTo(xy[i], xy[i + 1]);
            }
            p.close();
            return p;
        }

        @Override
        public boolean onTouchEvent(MotionEvent e) {
            if (e.getAction() != MotionEvent.ACTION_DOWN) {
                return true;
            }
            if (cell <= 0f) {
                return true;
            }
            int col = (int) ((e.getX() - pad) / cell);
            int row = (int) ((e.getY() - pad) / cell);
            if (col < 0 || col > 7 || row < 0 || row > 7) {
                return true;
            }
            onSquare(row * 8 + col);
            return true;
        }
    }
}
