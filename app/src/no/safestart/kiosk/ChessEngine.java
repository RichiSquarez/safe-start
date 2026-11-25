package no.safestart.kiosk;

import java.util.Random;

/**
 * Plain-Java chess rules plus a small alpha-beta bot.
 *
 * <p>No Android imports, no external libraries, no API newer than Java 8 so the
 * same file compiles both for the app (d8, min-api 23) and for a plain JVM unit
 * test.
 *
 * <p>Board indexing is "reading order": index 0 is a8 (top-left as seen by the
 * player, who is White), index 7 is h8, index 56 is a1, index 63 is h1. Row is
 * {@code index >> 3} (0 = rank 8) and column is {@code index & 7} (0 = file a).
 *
 * <p>Piece encoding: the low three bits are the piece type and bit 3 is the
 * colour, so a white queen is {@link #QUEEN} (5) and a black queen is
 * {@code QUEEN | 8} (13). Use {@link #typeOf(int)} and {@link #colorOf(int)}.
 *
 * <p>Deliberately skipped, all noted here so nobody hunts for them later:
 * <ul>
 *   <li>Under-promotion. Every pawn reaching the last rank becomes a queen, for
 *       the bot and for the human. The UI therefore needs no promotion dialog.</li>
 *   <li>Draw claims and the seventy-five move rule. The 50-move rule is applied
 *       automatically at 100 half-moves, repetition is automatic at the third
 *       occurrence, and bare kings / a lone minor piece count as a draw.</li>
 *   <li>No transposition table and no quiescence beyond two extra capture plies.
 *       The node and wall-clock budgets below are what keep it responsive.</li>
 * </ul>
 */
public final class ChessEngine {

    // ------------------------------------------------------------------ api

    /** Empty square. */
    public static final int EMPTY = 0;
    public static final int PAWN = 1;
    public static final int KNIGHT = 2;
    public static final int BISHOP = 3;
    public static final int ROOK = 4;
    public static final int QUEEN = 5;
    public static final int KING = 6;

    /** Colour of White, and the side the human plays. */
    public static final int WHITE = 0;
    /** Colour of Black, and the side the bot plays. */
    public static final int BLACK = 1;

    /** The game continues; the side to move has at least one legal move. */
    public static final int STATUS_PLAYING = 0;
    /** The side to move is mated. {@link #winner()} says who delivered it. */
    public static final int STATUS_CHECKMATE = 1;
    /** The side to move has no legal move but is not in check. */
    public static final int STATUS_STALEMATE = 2;
    /** Automatic draw: 50-move rule, threefold repetition, or no mating material. */
    public static final int STATUS_DRAW = 3;

    private static final int COLOR_BIT = 8;

    // ------------------------------------------------------------- position

    /** 64 squares, see the class comment for the indexing. */
    private final int[] board = new int[64];

    /** {@link #WHITE} or {@link #BLACK}: the side to move. */
    private int turn;

    /** Castling rights bits, see {@link #WK} .. {@link #BQ}. */
    private int castling;

    /** En-passant target square, or -1. */
    private int ep;

    /** Half-moves since the last capture or pawn move, for the 50-move rule. */
    private int halfmove;

    private final int[] kingSq = new int[2];

    // ---------------------------------------------------------- undo stack

    private static final int MAX_PLY = 1024;

    private final int[] unMove = new int[MAX_PLY];
    private final int[] unPiece = new int[MAX_PLY];
    private final int[] unCaptured = new int[MAX_PLY];
    private final int[] unCapSq = new int[MAX_PLY];
    private final int[] unCastling = new int[MAX_PLY];
    private final int[] unEp = new int[MAX_PLY];
    private final int[] unHalf = new int[MAX_PLY];
    private final long[] unKey = new long[MAX_PLY];
    private final long[] posKey = new long[MAX_PLY + 1];
    private int histLen;

    /** Zobrist key of the current position; also the repetition key. */
    private long key;

    /** Scratch buffer for pseudo-legal moves; never used re-entrantly. */
    private final int[] scratch = new int[256];

    private int lastFrom = -1;
    private int lastTo = -1;

    // --------------------------------------------------------- castling ids

    private static final int WK = 1;
    private static final int WQ = 2;
    private static final int BK = 4;
    private static final int BQ = 8;

    /** Rights that survive a move from / to this square. */
    private static final int[] CASTLE_MASK = new int[64];

    // ------------------------------------------------------------- geometry

    private static final int[] KNIGHT_DR = {-2, -2, -1, -1, 1, 1, 2, 2};
    private static final int[] KNIGHT_DC = {-1, 1, -2, 2, -2, 2, -1, 1};
    private static final int[] KING_DR = {-1, -1, -1, 0, 0, 1, 1, 1};
    private static final int[] KING_DC = {-1, 0, 1, -1, 1, -1, 0, 1};
    private static final int[] ROOK_DR = {-1, 1, 0, 0};
    private static final int[] ROOK_DC = {0, 0, -1, 1};
    private static final int[] BISHOP_DR = {-1, -1, 1, 1};
    private static final int[] BISHOP_DC = {-1, 1, -1, 1};

    // ---------------------------------------------------------- evaluation

    private static final int[] VALUE = {0, 100, 320, 330, 500, 900, 0};

    /*
     * Piece-square tables, written in board order (first row = rank 8) from
     * White's point of view. Black simply reads the mirrored square, 63 - i.
     */
    private static final int[] PST_PAWN = {
             0,   0,   0,   0,   0,   0,   0,   0,
            60,  60,  60,  60,  60,  60,  60,  60,
            18,  20,  22,  26,  26,  22,  20,  18,
             8,   9,  14,  20,  20,  14,   9,   8,
             3,   5,   9,  16,  16,   9,   5,   3,
             0,   1,   3,   8,   8,   3,   1,   0,
             2,   2,   2,   0,   0,   2,   2,   2,
             0,   0,   0,   0,   0,   0,   0,   0
    };

    private static final int[] PST_KNIGHT = {
           -50, -35, -25, -20, -20, -25, -35, -50,
           -35, -15,   0,   5,   5,   0, -15, -35,
           -25,   5,  12,  18,  18,  12,   5, -25,
           -20,   5,  18,  24,  24,  18,   5, -20,
           -20,   5,  18,  24,  24,  18,   5, -20,
           -25,   5,  12,  18,  18,  12,   5, -25,
           -35, -15,   0,   0,   0,   0, -15, -35,
           -50, -35, -25, -20, -20, -25, -35, -50
    };

    private static final int[] PST_BISHOP = {
           -20, -10, -10, -10, -10, -10, -10, -20,
           -10,   5,   0,   0,   0,   0,   5, -10,
           -10,  10,  12,  12,  12,  12,  10, -10,
           -10,   0,  12,  14,  14,  12,   0, -10,
           -10,   5,   8,  14,  14,   8,   5, -10,
           -10,   0,  10,  12,  12,  10,   0, -10,
           -10,   0,   0,   0,   0,   0,   0, -10,
           -20, -10, -10, -10, -10, -10, -10, -20
    };

    private static final int[] PST_ROOK = {
             0,   0,   0,   5,   5,   0,   0,   0,
             8,  12,  12,  12,  12,  12,  12,   8,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
            -5,   0,   0,   0,   0,   0,   0,  -5,
             0,   0,   0,   5,   5,   0,   0,   0
    };

    private static final int[] PST_QUEEN = {
           -20, -10, -10,  -5,  -5, -10, -10, -20,
           -10,   0,   5,   0,   0,   0,   0, -10,
           -10,   5,   5,   5,   5,   5,   0, -10,
            -5,   0,   5,   5,   5,   5,   0,  -5,
             0,   0,   5,   5,   5,   5,   0,  -5,
           -10,   0,   5,   5,   5,   5,   0, -10,
           -10,   0,   0,   0,   0,   0,   0, -10,
           -20, -10, -10,  -5,  -5, -10, -10, -20
    };

    private static final int[] PST_KING_MID = {
           -30, -40, -40, -50, -50, -40, -40, -30,
           -30, -40, -40, -50, -50, -40, -40, -30,
           -30, -40, -40, -50, -50, -40, -40, -30,
           -30, -40, -40, -50, -50, -40, -40, -30,
           -20, -30, -30, -40, -40, -30, -30, -20,
           -10, -20, -20, -20, -20, -20, -20, -10,
            20,  20,   0,   0,   0,   0,  20,  20,
            20,  30,  10,   0,   0,  10,  30,  20
    };

    private static final int[] PST_KING_END = {
           -50, -40, -30, -20, -20, -30, -40, -50,
           -30, -20, -10,   0,   0, -10, -20, -30,
           -30, -10,  20,  30,  30,  20, -10, -30,
           -30, -10,  30,  40,  40,  30, -10, -30,
           -30, -10,  30,  40,  40,  30, -10, -30,
           -30, -10,  20,  30,  30,  20, -10, -30,
           -30, -30,   0,   0,   0,   0, -30, -30,
           -50, -30, -30, -30, -30, -30, -30, -50
    };

    /** Indexed by piece type; the king entry is unused (see {@link #evaluate()}). */
    private static final int[][] PST = {
            null, PST_PAWN, PST_KNIGHT, PST_BISHOP, PST_ROOK, PST_QUEEN, PST_KING_MID
    };

    // --------------------------------------------------------------- search

    private static final int INF = 1000000;
    private static final int MATE = 100000;

    private final Random random = new Random();

    private int nodes;
    private int nodeBudget;
    private long deadline;
    private long noiseSeed;
    private boolean aborted;

    /** Per-ply move buffers, so the search does not allocate per node. */
    private final int[][] searchMoves = new int[16][256];
    private final int[][] searchScores = new int[16][256];

    private static final SearchAbort ABORT = new SearchAbort();

    /** Thrown once inside {@link #botMove} when the budget runs out. */
    private static final class SearchAbort extends RuntimeException {
        SearchAbort() {
            super("search budget exhausted", null, false, false);
        }
    }

    // Zobrist tables. A fixed seed keeps a game reproducible per session.
    private static final int[][] Z_PIECE = new int[16][64];
    private static final int[] Z_CASTLE = new int[16];
    private static final int[] Z_EP = new int[65];
    private static int Z_SIDE;

    static {
        for (int i = 0; i < 64; i++) {
            CASTLE_MASK[i] = 15;
        }
        CASTLE_MASK[60] = 15 & ~(WK | WQ); // e1
        CASTLE_MASK[63] = 15 & ~WK;        // h1
        CASTLE_MASK[56] = 15 & ~WQ;        // a1
        CASTLE_MASK[4] = 15 & ~(BK | BQ);  // e8
        CASTLE_MASK[7] = 15 & ~BK;         // h8
        CASTLE_MASK[0] = 15 & ~BQ;         // a8

        Random z = new Random(0x5AFE57A27L);
        for (int p = 0; p < 16; p++) {
            for (int s = 0; s < 64; s++) {
                Z_PIECE[p][s] = z.nextInt();
            }
        }
        for (int c = 0; c < 16; c++) {
            Z_CASTLE[c] = z.nextInt();
        }
        for (int s = 0; s < 65; s++) {
            Z_EP[s] = z.nextInt();
        }
        Z_SIDE = z.nextInt();
    }

    // ------------------------------------------------------------ lifecycle

    /** A new engine in the standard start position, White to move. */
    public ChessEngine() {
        reset();
    }

    /** Puts the standard start position back on the board. */
    public void reset() {
        for (int i = 0; i < 64; i++) {
            board[i] = EMPTY;
        }
        putRow(0, BLACK);
        for (int c = 0; c < 8; c++) {
            board[8 + c] = PAWN | COLOR_BIT;
            board[48 + c] = PAWN;
        }
        putRow(7, WHITE);

        kingSq[WHITE] = 60;
        kingSq[BLACK] = 4;
        turn = WHITE;
        castling = WK | WQ | BK | BQ;
        ep = -1;
        halfmove = 0;
        histLen = 0;
        key = computeKey();
        posKey[0] = key;
        lastFrom = -1;
        lastTo = -1;
    }

    private void putRow(int row, int color) {
        int base = color == WHITE ? 0 : COLOR_BIT;
        int i = row * 8;
        board[i] = ROOK | base;
        board[i + 1] = KNIGHT | base;
        board[i + 2] = BISHOP | base;
        board[i + 3] = QUEEN | base;
        board[i + 4] = KING | base;
        board[i + 5] = BISHOP | base;
        board[i + 6] = KNIGHT | base;
        board[i + 7] = ROOK | base;
    }

    // ---------------------------------------------------------- inspection

    /** Piece on square {@code i} (0..63), {@link #EMPTY} when the square is bare. */
    public int pieceAt(int i) {
        if (i < 0 || i > 63) {
            return EMPTY;
        }
        return board[i];
    }

    /** {@link #WHITE}, {@link #BLACK}, or -1 for an empty square. */
    public int sideAt(int i) {
        int p = pieceAt(i);
        return p == EMPTY ? -1 : colorOf(p);
    }

    /** The side to move. */
    public int turn() {
        return turn;
    }

    /** True when the side to move is in check. */
    public boolean inCheck() {
        return inCheck(turn);
    }

    /** Square of {@code color}'s king, for the UI if it ever wants it. */
    public int kingSquare(int color) {
        return kingSq[color == WHITE ? WHITE : BLACK];
    }

    /** The square the last {@link #move(int, int)} came from, or -1. */
    public int lastFrom() {
        return lastFrom;
    }

    /** The square the last {@link #move(int, int)} went to, or -1. */
    public int lastTo() {
        return lastTo;
    }

    /** {@link #STATUS_PLAYING}, {@link #STATUS_CHECKMATE}, {@link #STATUS_STALEMATE} or {@link #STATUS_DRAW}. */
    public int status() {
        int[] all = new int[256];
        int n = generateLegalMoves(turn, all);
        if (n == 0) {
            return inCheck(turn) ? STATUS_CHECKMATE : STATUS_STALEMATE;
        }
        if (halfmove >= 100) {
            return STATUS_DRAW;
        }
        if (insufficientMaterial()) {
            return STATUS_DRAW;
        }
        if (repetitionCount() >= 3) {
            return STATUS_DRAW;
        }
        return STATUS_PLAYING;
    }

    /** {@link #WHITE} or {@link #BLACK} after a checkmate, otherwise -1. */
    public int winner() {
        return status() == STATUS_CHECKMATE ? 1 - turn : -1;
    }

    // -------------------------------------------------------------- moving

    /**
     * Destinations reachable from {@code from} that are fully legal, i.e. they
     * do not leave the mover's own king in check. Empty when the square holds
     * no piece of the side to move.
     */
    public int[] legalMoves(int from) {
        int[] out = new int[0];
        if (from < 0 || from > 63) {
            return out;
        }
        int[] all = new int[256];
        int n = generateLegalMoves(turn, all);
        int count = 0;
        for (int i = 0; i < n; i++) {
            if ((all[i] & 63) == from) {
                count++;
            }
        }
        if (count == 0) {
            return out;
        }
        int[] result = new int[count];
        int c = 0;
        for (int i = 0; i < n; i++) {
            if ((all[i] & 63) == from) {
                result[c++] = (all[i] >> 6) & 63;
            }
        }
        return result;
    }

    /** True when from -> to is legal for the side to move right now. */
    public boolean isLegal(int from, int to) {
        return encodeLegal(from, to) != 0;
    }

    /**
     * Plays a legal move for the side to move. Returns false (and changes
     * nothing) when the move is not legal. A pawn reaching the last rank is
     * always promoted to a queen.
     */
    public boolean move(int from, int to) {
        int mv = encodeLegal(from, to);
        if (mv == 0) {
            return false;
        }
        makeMove(mv);
        lastFrom = from;
        lastTo = to;
        return true;
    }

    /** 0 when the move is illegal, otherwise the encoded move. */
    private int encodeLegal(int from, int to) {
        if (from < 0 || from > 63 || to < 0 || to > 63) {
            return 0;
        }
        int[] all = new int[256];
        int n = generateLegalMoves(turn, all);
        int want = from | (to << 6);
        for (int i = 0; i < n; i++) {
            if (all[i] == want) {
                return want;
            }
        }
        return 0;
    }

    // ---------------------------------------------------------------- bot

    /**
     * Best move for the side to move, or null when the game is over.
     *
     * <p>This is synchronous and may take up to about a second, so call it from
     * a background thread and hand the result back with {@code View.post}.
     * Level 1 ("Lett") is depth 2, level 2 ("Middels") depth 3, level 3
     * ("Vanskelig") depth 4, each with capture quiescence and a node/clock
     * budget that aborts the search rather than freeze the caller.
     *
     * @return a two element array {from, to}, or null when there is no move
     */
    public int[] botMove(int level) {
        return botMove(level, botTimeBudget(level));
    }

    /** Millisecond budget used by {@link #botMove(int)}. */
    public static long botTimeBudget(int level) {
        if (level >= 3) {
            return 900L;
        }
        return level == 2 ? 600L : 400L;
    }

    /**
     * Same as {@link #botMove(int)} but with an explicit wall-clock budget in
     * milliseconds. The search stops at whichever comes first, this budget or
     * the node budget, and keeps the best move of the last fully completed
     * depth.
     */
    public int[] botMove(int level, long maxMillis) {
        if (status() != STATUS_PLAYING) {
            return null;
        }
        int maxDepth = level >= 3 ? 4 : (level == 2 ? 3 : 2);
        nodeBudget = level >= 3 ? 150000 : (level == 2 ? 100000 : 40000);
        if (maxMillis <= 0L) {
            maxMillis = botTimeBudget(level);
        }

        int[] root = new int[256];
        int n = generateLegalMoves(turn, root);
        if (n == 0) {
            return null;
        }
        if (n == 1) {
            return pair(root[0]);
        }

        // The search mutates the position, so keep a snapshot to restore in
        // the finally block; an abort unwinds from an arbitrary depth.
        int[] snapBoard = board.clone();
        int snapTurn = turn;
        int snapCastling = castling;
        int snapEp = ep;
        int snapHalf = halfmove;
        int snapHist = histLen;
        int snapWk = kingSq[0];
        int snapBk = kingSq[1];
        long snapKey = key;

        nodes = 0;
        aborted = false;
        noiseSeed = random.nextLong();
        deadline = System.nanoTime() + maxMillis * 1000000L;

        int[] order = new int[n];
        for (int i = 0; i < n; i++) {
            // Random jitter only breaks ties, it never promotes a bad capture
            // above a good one, but it does vary the opening move.
            order[i] = moveOrderScore(root[i]) + random.nextInt(24);
        }

        int[] doneMoves = null;
        int[] doneScores = null;
        boolean[] doneExact = null;
        int doneBest = -1;

        try {
            for (int depth = 1; depth <= maxDepth; depth++) {
                int alpha = -INF;
                int iterationBest = -1;
                int[] scores = new int[n];
                boolean[] exact = new boolean[n];
                boolean complete = true;
                try {
                    for (int i = 0; i < n; i++) {
                        pickNext(root, order, i, n);
                        int mv = root[i];
                        int mover = turn;
                        makeMove(mv);
                        if (inCheck(mover)) {
                            unmakeMove();
                            scores[i] = -INF;
                            continue;
                        }
                        int sc;
                        try {
                            sc = -negamax(depth - 1, -INF, -alpha, 1);
                        } finally {
                            unmakeMove();
                        }
                        scores[i] = sc;
                        if (sc > alpha) {
                            alpha = sc;
                            exact[i] = true;
                            iterationBest = i;
                        } else if (iterationBest < 0) {
                            iterationBest = i;
                        }
                    }
                } catch (SearchAbort a) {
                    complete = false;
                }
                if (!complete) {
                    break;
                }
                if (iterationBest >= 0) {
                    doneMoves = root.clone();
                    doneScores = scores;
                    doneExact = exact;
                    doneBest = iterationBest;
                    for (int i = 0; i < n; i++) {
                        order[i] = scores[i];
                    }
                    if (scores[doneBest] > MATE - 1000) {
                        break; // mate found, no deeper search needed
                    }
                }
            }
        } finally {
            System.arraycopy(snapBoard, 0, board, 0, 64);
            turn = snapTurn;
            castling = snapCastling;
            ep = snapEp;
            halfmove = snapHalf;
            histLen = snapHist;
            kingSq[0] = snapWk;
            kingSq[1] = snapBk;
            key = snapKey;
            aborted = false;
        }

        if (doneMoves == null || doneBest < 0) {
            return pair(root[0]);
        }

        int chosen = doneBest;
        int bestScore = doneScores[doneBest];
        if (bestScore < MATE - 1000) {
            // Among moves whose score is exact and within a small band, pick
            // one at random. Two searches rarely play the identical game.
            int count = 0;
            int total = doneScores.length;
            int[] band = new int[total];
            for (int i = 0; i < total; i++) {
                if (doneExact[i] && doneScores[i] >= bestScore - 12) {
                    band[count++] = i;
                }
            }
            if (count > 1) {
                chosen = band[random.nextInt(count)];
            }
        }

        int mv = doneMoves[chosen];
        if (!isLegalMove(mv)) {
            int[] all = new int[256];
            int m = generateLegalMoves(turn, all);
            return m > 0 ? pair(all[0]) : null;
        }
        return pair(mv);
    }

    private static int[] pair(int mv) {
        return new int[]{mv & 63, (mv >> 6) & 63};
    }

    private boolean isLegalMove(int mv) {
        int[] all = new int[256];
        int n = generateLegalMoves(turn, all);
        for (int i = 0; i < n; i++) {
            if (all[i] == mv) {
                return true;
            }
        }
        return false;
    }

    // ------------------------------------------------------------- search

    private int negamax(int depth, int alpha, int beta, int ply) {
        tick();
        if (depth <= 0) {
            return quiesce(alpha, beta, ply, 0);
        }
        if (ply >= 15) {
            return evaluate();
        }
        int side = turn;
        int[] moves = searchMoves[ply];
        int[] scores = searchScores[ply];
        int n = generatePseudo(side, moves);
        for (int i = 0; i < n; i++) {
            scores[i] = moveOrderScore(moves[i]);
        }

        int best = -INF;
        int legal = 0;
        for (int i = 0; i < n; i++) {
            pickNext(moves, scores, i, n);
            int mv = moves[i];
            makeMove(mv);
            if (inCheck(side)) {
                unmakeMove();
                continue;
            }
            legal++;
            int sc = -negamax(depth - 1, -beta, -alpha, ply + 1);
            unmakeMove();
            if (sc > best) {
                best = sc;
            }
            if (sc > alpha) {
                alpha = sc;
            }
            if (alpha >= beta) {
                return beta;
            }
        }
        if (legal == 0) {
            return inCheck(side) ? -MATE + ply : 0;
        }
        return best;
    }

    /** Capture-only search, two extra plies at most. */
    private int quiesce(int alpha, int beta, int ply, int qdepth) {
        tick();
        int side = turn;
        int stand = evaluate();
        if (stand >= beta) {
            return beta;
        }
        if (stand > alpha) {
            alpha = stand;
        }
        if (qdepth >= 2 || ply >= 15) {
            return alpha;
        }

        int[] moves = searchMoves[ply];
        int[] scores = searchScores[ply];
        int n = generatePseudo(side, moves);
        int c = 0;
        for (int i = 0; i < n; i++) {
            int mv = moves[i];
            int from = mv & 63;
            int to = (mv >> 6) & 63;
            int p = board[from];
            int type = typeOf(p);
            boolean promotion = type == PAWN && (rowOf(to) == 0 || rowOf(to) == 7);
            boolean epCapture = type == PAWN && to == ep && board[to] == EMPTY
                    && colOf(from) != colOf(to);
            if (board[to] != EMPTY || promotion || epCapture) {
                moves[c] = mv;
                scores[c] = moveOrderScore(mv);
                c++;
            }
        }
        n = c;

        int best = stand;
        for (int i = 0; i < n; i++) {
            pickNext(moves, scores, i, n);
            int mv = moves[i];
            makeMove(mv);
            if (inCheck(side)) {
                unmakeMove();
                continue;
            }
            int sc = -quiesce(-beta, -alpha, ply + 1, qdepth + 1);
            unmakeMove();
            if (sc > best) {
                best = sc;
            }
            if (sc > alpha) {
                alpha = sc;
            }
            if (alpha >= beta) {
                return beta;
            }
        }
        return best;
    }

    private void tick() {
        if (aborted) {
            throw ABORT;
        }
        nodes++;
        if (nodes > nodeBudget) {
            aborted = true;
            throw ABORT;
        }
        if ((nodes & 1023) == 0 && System.nanoTime() - deadline >= 0L) {
            aborted = true;
            throw ABORT;
        }
    }

    /** Swaps the best remaining move of [start, end) to {@code start}. */
    private static void pickNext(int[] moves, int[] scores, int start, int end) {
        int best = start;
        for (int i = start + 1; i < end; i++) {
            if (scores[i] > scores[best]) {
                best = i;
            }
        }
        if (best != start) {
            int m = moves[best];
            moves[best] = moves[start];
            moves[start] = m;
            int s = scores[best];
            scores[best] = scores[start];
            scores[start] = s;
        }
    }

    /** Cheap ordering key: captures first (MVV-LVA), promotions next. */
    private int moveOrderScore(int mv) {
        int from = mv & 63;
        int to = (mv >> 6) & 63;
        int victim = board[to];
        int score = 0;
        if (victim != EMPTY) {
            score = 100 * VALUE[typeOf(victim)] - VALUE[typeOf(board[from])];
        }
        int type = typeOf(board[from]);
        if (type == PAWN && (rowOf(to) == 0 || rowOf(to) == 7)) {
            score += 800;
        }
        return score;
    }

    // ---------------------------------------------------------- evaluation

    private int evaluate() {
        int nonPawn = 0;
        int whiteBishops = 0;
        int blackBishops = 0;
        for (int i = 0; i < 64; i++) {
            int p = board[i];
            if (p == EMPTY) {
                continue;
            }
            int type = typeOf(p);
            if (type != PAWN && type != KING) {
                nonPawn += VALUE[type];
            }
            if (type == BISHOP) {
                if (colorOf(p) == WHITE) {
                    whiteBishops++;
                } else {
                    blackBishops++;
                }
            }
        }
        boolean endgame = nonPawn <= 1400;

        int score = 0;
        for (int i = 0; i < 64; i++) {
            int p = board[i];
            if (p == EMPTY) {
                continue;
            }
            int type = typeOf(p);
            int color = colorOf(p);
            int idx = color == WHITE ? i : 63 - i;
            int value = VALUE[type];
            int pst = type == KING
                    ? (endgame ? PST_KING_END[idx] : PST_KING_MID[idx])
                    : PST[type][idx];
            score += color == WHITE ? value + pst : -(value + pst);
        }
        if (whiteBishops >= 2) {
            score += 18;
        }
        if (blackBishops >= 2) {
            score -= 18;
        }
        score += positionNoise();
        return turn == WHITE ? score : -score;
    }

    /**
     * A small position-dependent wobble, stable for one search but different
     * for the next one so the bot does not replay an identical game.
     */
    private int positionNoise() {
        long x = key * 0x9E3779B97F4A7C15L + noiseSeed;
        x ^= x >>> 33;
        x *= 0xFF51AFD7ED558CCDL;
        x ^= x >>> 33;
        return (int) (x & 15L) - 8;
    }

    // ------------------------------------------------------ move generation

    /** Encodes a move as {@code from | (to << 6)}. */
    private static int add(int[] moves, int n, int from, int to) {
        if (n < moves.length) {
            moves[n] = from | (to << 6);
            return n + 1;
        }
        return n;
    }

    /** Legal moves for {@code color}, filtered through make/unmake. */
    private int generateLegalMoves(int color, int[] out) {
        int n = generatePseudo(color, scratch);
        int c = 0;
        for (int i = 0; i < n; i++) {
            int mv = scratch[i];
            makeMove(mv);
            boolean ok = !inCheck(color);
            unmakeMove();
            if (ok) {
                out[c++] = mv;
            }
        }
        return c;
    }

    private int generatePseudo(int color, int[] moves) {
        int n = 0;
        for (int sq = 0; sq < 64; sq++) {
            int p = board[sq];
            if (p == EMPTY || colorOf(p) != color) {
                continue;
            }
            int type = typeOf(p);
            int row = sq >> 3;
            int col = sq & 7;

            if (type == PAWN) {
                int dir = color == WHITE ? -1 : 1;
                int startRow = color == WHITE ? 6 : 1;
                int r1 = row + dir;
                if (r1 >= 0 && r1 < 8) {
                    int one = r1 * 8 + col;
                    if (board[one] == EMPTY) {
                        n = add(moves, n, sq, one);
                        if (row == startRow) {
                            int two = (row + 2 * dir) * 8 + col;
                            if (board[two] == EMPTY) {
                                n = add(moves, n, sq, two);
                            }
                        }
                    }
                    for (int dc = -1; dc <= 1; dc += 2) {
                        int c1 = col + dc;
                        if (c1 < 0 || c1 > 7) {
                            continue;
                        }
                        int to = r1 * 8 + c1;
                        int q = board[to];
                        if (q != EMPTY && colorOf(q) != color) {
                            n = add(moves, n, sq, to);
                        } else if (q == EMPTY && to == ep) {
                            n = add(moves, n, sq, to);
                        }
                    }
                }
            } else if (type == KNIGHT) {
                for (int k = 0; k < 8; k++) {
                    int r = row + KNIGHT_DR[k];
                    int c = col + KNIGHT_DC[k];
                    if (r < 0 || r > 7 || c < 0 || c > 7) {
                        continue;
                    }
                    int to = r * 8 + c;
                    int q = board[to];
                    if (q == EMPTY || colorOf(q) != color) {
                        n = add(moves, n, sq, to);
                    }
                }
            } else if (type == KING) {
                for (int k = 0; k < 8; k++) {
                    int r = row + KING_DR[k];
                    int c = col + KING_DC[k];
                    if (r < 0 || r > 7 || c < 0 || c > 7) {
                        continue;
                    }
                    int to = r * 8 + c;
                    int q = board[to];
                    if (q == EMPTY || colorOf(q) != color) {
                        n = add(moves, n, sq, to);
                    }
                }
            } else {
                boolean diagonal = type == BISHOP || type == QUEEN;
                boolean straight = type == ROOK || type == QUEEN;
                if (diagonal) {
                    for (int k = 0; k < 4; k++) {
                        n = slide(moves, n, sq, BISHOP_DR[k], BISHOP_DC[k], color);
                    }
                }
                if (straight) {
                    for (int k = 0; k < 4; k++) {
                        n = slide(moves, n, sq, ROOK_DR[k], ROOK_DC[k], color);
                    }
                }
            }
        }

        // Castling: rights intact, king and rook at home, path empty, and the
        // king may not start in, pass through, or land on an attacked square.
        int enemy = 1 - color;
        if (color == WHITE) {
            boolean kingHome = board[60] == KING;
            if ((castling & WK) != 0 && kingHome && board[63] == ROOK
                    && board[61] == EMPTY && board[62] == EMPTY
                    && !attacked(60, enemy) && !attacked(61, enemy) && !attacked(62, enemy)) {
                n = add(moves, n, 60, 62);
            }
            if ((castling & WQ) != 0 && kingHome && board[56] == ROOK
                    && board[57] == EMPTY && board[58] == EMPTY && board[59] == EMPTY
                    && !attacked(60, enemy) && !attacked(59, enemy) && !attacked(58, enemy)) {
                n = add(moves, n, 60, 58);
            }
        } else {
            int blackKing = KING | COLOR_BIT;
            int blackRook = ROOK | COLOR_BIT;
            boolean kingHome = board[4] == blackKing;
            if ((castling & BK) != 0 && kingHome && board[7] == blackRook
                    && board[5] == EMPTY && board[6] == EMPTY
                    && !attacked(4, enemy) && !attacked(5, enemy) && !attacked(6, enemy)) {
                n = add(moves, n, 4, 6);
            }
            if ((castling & BQ) != 0 && kingHome && board[0] == blackRook
                    && board[1] == EMPTY && board[2] == EMPTY && board[3] == EMPTY
                    && !attacked(4, enemy) && !attacked(3, enemy) && !attacked(2, enemy)) {
                n = add(moves, n, 4, 2);
            }
        }
        return n;
    }

    private int slide(int[] moves, int n, int sq, int dr, int dc, int color) {
        int row = sq >> 3;
        int col = sq & 7;
        int r = row + dr;
        int c = col + dc;
        while (r >= 0 && r < 8 && c >= 0 && c < 8) {
            int to = r * 8 + c;
            int q = board[to];
            if (q == EMPTY) {
                n = add(moves, n, sq, to);
            } else {
                if (colorOf(q) != color) {
                    n = add(moves, n, sq, to);
                }
                return n;
            }
            r += dr;
            c += dc;
        }
        return n;
    }

    /** True when {@code sq} is attacked by any piece of {@code byColor}. */
    private boolean attacked(int sq, int byColor) {
        int row = sq >> 3;
        int col = sq & 7;

        // Pawns. A white pawn attacks upwards, so it must sit one row below.
        int pawnRow = row + (byColor == WHITE ? 1 : -1);
        if (pawnRow >= 0 && pawnRow < 8) {
            int want = PAWN | (byColor == WHITE ? 0 : COLOR_BIT);
            for (int dc = -1; dc <= 1; dc += 2) {
                int pc = col + dc;
                if (pc < 0 || pc > 7) {
                    continue;
                }
                if (board[pawnRow * 8 + pc] == want) {
                    return true;
                }
            }
        }

        // Knights.
        int wantKnight = KNIGHT | (byColor == WHITE ? 0 : COLOR_BIT);
        for (int k = 0; k < 8; k++) {
            int r = row + KNIGHT_DR[k];
            int c = col + KNIGHT_DC[k];
            if (r < 0 || r > 7 || c < 0 || c > 7) {
                continue;
            }
            if (board[r * 8 + c] == wantKnight) {
                return true;
            }
        }

        // King.
        int wantKing = KING | (byColor == WHITE ? 0 : COLOR_BIT);
        for (int k = 0; k < 8; k++) {
            int r = row + KING_DR[k];
            int c = col + KING_DC[k];
            if (r < 0 || r > 7 || c < 0 || c > 7) {
                continue;
            }
            if (board[r * 8 + c] == wantKing) {
                return true;
            }
        }

        // Sliding pieces.
        int base = byColor == WHITE ? 0 : COLOR_BIT;
        int rook = ROOK | base;
        int bishop = BISHOP | base;
        int queen = QUEEN | base;
        for (int k = 0; k < 4; k++) {
            int r = row + ROOK_DR[k];
            int c = col + ROOK_DC[k];
            while (r >= 0 && r < 8 && c >= 0 && c < 8) {
                int q = board[r * 8 + c];
                if (q != EMPTY) {
                    if (q == rook || q == queen) {
                        return true;
                    }
                    break;
                }
                r += ROOK_DR[k];
                c += ROOK_DC[k];
            }
        }
        for (int k = 0; k < 4; k++) {
            int r = row + BISHOP_DR[k];
            int c = col + BISHOP_DC[k];
            while (r >= 0 && r < 8 && c >= 0 && c < 8) {
                int q = board[r * 8 + c];
                if (q != EMPTY) {
                    if (q == bishop || q == queen) {
                        return true;
                    }
                    break;
                }
                r += BISHOP_DR[k];
                c += BISHOP_DC[k];
            }
        }
        return false;
    }

    private boolean inCheck(int color) {
        return attacked(kingSq[color == WHITE ? WHITE : BLACK], 1 - color);
    }

    // -------------------------------------------------- make / unmake move

    private void makeMove(int mv) {
        int from = mv & 63;
        int to = (mv >> 6) & 63;
        int p = board[from];
        int color = colorOf(p);
        int type = typeOf(p);

        int captured = board[to];
        int capSq = to;
        if (type == PAWN && to == ep && captured == EMPTY && colOf(from) != colOf(to)) {
            capSq = color == WHITE ? to + 8 : to - 8;
            captured = board[capSq];
            board[capSq] = EMPTY;
        }

        int prevCastling = castling;
        int prevEp = ep;
        int prevHalf = halfmove;
        long prevKey = key;

        long k = key;
        board[from] = EMPTY;
        k ^= Z_PIECE[p][from];

        int placed = p;
        if (type == PAWN && (rowOf(to) == 0 || rowOf(to) == 7)) {
            placed = QUEEN | color * COLOR_BIT;
        }
        board[to] = placed;
        k ^= Z_PIECE[placed][to];
        if (captured != EMPTY) {
            k ^= Z_PIECE[captured][capSq];
        }

        if (type == KING) {
            kingSq[color] = to;
            if (to - from == 2 || from - to == 2) {
                int rFrom;
                int rTo;
                if (to - from == 2) {
                    rFrom = from + 3;
                    rTo = from + 1;
                } else {
                    rFrom = from - 4;
                    rTo = from - 1;
                }
                int rook = board[rFrom];
                board[rTo] = rook;
                board[rFrom] = EMPTY;
                k ^= Z_PIECE[rook][rFrom] ^ Z_PIECE[rook][rTo];
            }
        }

        castling &= CASTLE_MASK[from] & CASTLE_MASK[to];

        ep = -1;
        if (type == PAWN && (to - from == 16 || from - to == 16)) {
            ep = (from + to) >> 1;
        }

        if (type == PAWN || captured != EMPTY) {
            halfmove = 0;
        } else {
            halfmove++;
        }

        k ^= Z_SIDE;
        k ^= Z_CASTLE[prevCastling] ^ Z_CASTLE[castling];
        k ^= Z_EP[prevEp < 0 ? 64 : prevEp] ^ Z_EP[ep < 0 ? 64 : ep];
        key = k;
        turn = 1 - turn;

        unMove[histLen] = mv;
        unPiece[histLen] = p;
        unCaptured[histLen] = captured;
        unCapSq[histLen] = capSq;
        unCastling[histLen] = prevCastling;
        unEp[histLen] = prevEp;
        unHalf[histLen] = prevHalf;
        unKey[histLen] = prevKey;

        if (histLen < MAX_PLY - 1) {
            histLen++;
            posKey[histLen] = key;
        }
    }

    private void unmakeMove() {
        if (histLen <= 0) {
            return;
        }
        histLen--;
        int mv = unMove[histLen];
        int from = mv & 63;
        int to = (mv >> 6) & 63;
        int p = unPiece[histLen];
        int captured = unCaptured[histLen];
        int capSq = unCapSq[histLen];

        board[to] = EMPTY;
        board[from] = p;
        if (captured != EMPTY) {
            board[capSq] = captured;
        }

        int color = colorOf(p);
        if (typeOf(p) == KING) {
            kingSq[color] = from;
            if (to - from == 2 || from - to == 2) {
                if (to - from == 2) {
                    board[from + 3] = board[from + 1];
                    board[from + 1] = EMPTY;
                } else {
                    board[from - 4] = board[from - 1];
                    board[from - 1] = EMPTY;
                }
            }
        }

        castling = unCastling[histLen];
        ep = unEp[histLen];
        halfmove = unHalf[histLen];
        key = unKey[histLen];
        turn = 1 - turn;
    }

    // -------------------------------------------------------------- draws

    /**
     * Counts how often the current position has occurred, including now. Only
     * reversible moves are scanned, which is what the repetition rule allows.
     */
    private int repetitionCount() {
        int count = 1;
        int stop = histLen - halfmove;
        if (stop < 0) {
            stop = 0;
        }
        for (int i = histLen - 2; i >= stop; i -= 2) {
            if (posKey[i] == key) {
                count++;
            }
        }
        return count;
    }

    /** Bare kings, or a single minor piece, cannot force a mate. */
    private boolean insufficientMaterial() {
        int minors = 0;
        for (int i = 0; i < 64; i++) {
            int p = board[i];
            if (p == EMPTY) {
                continue;
            }
            int type = typeOf(p);
            if (type == PAWN || type == ROOK || type == QUEEN) {
                return false;
            }
            if (type == KNIGHT || type == BISHOP) {
                minors++;
            }
        }
        return minors <= 1;
    }

    // ------------------------------------------------------------- helpers

    private long computeKey() {
        long k = 0L;
        for (int i = 0; i < 64; i++) {
            int p = board[i];
            if (p != EMPTY) {
                k ^= Z_PIECE[p][i];
            }
        }
        k ^= Z_CASTLE[castling];
        k ^= Z_EP[ep < 0 ? 64 : ep];
        if (turn == BLACK) {
            k ^= Z_SIDE;
        }
        return k;
    }

    /** Piece type 1..6, or 0 for an empty square. */
    public static int typeOf(int piece) {
        return piece & 7;
    }

    /** {@link #WHITE} or {@link #BLACK}. Meaningless for an empty square. */
    public static int colorOf(int piece) {
        return (piece >> 3) & 1;
    }

    /** Row 0 (rank 8) to row 7 (rank 1). */
    public static int rowOf(int sq) {
        return sq >> 3;
    }

    /** Column 0 (file a) to column 7 (file h). */
    public static int colOf(int sq) {
        return sq & 7;
    }

    /** "e4" style name of a square, handy in logs. */
    public static String squareName(int sq) {
        if (sq < 0 || sq > 63) {
            return "??";
        }
        return new String(new char[]{(char) ('a' + (sq & 7)), (char) ('8' - (sq >> 3))});
    }
}
