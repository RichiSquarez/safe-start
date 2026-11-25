package no.safestart.kiosk;

import android.content.Context;
import android.content.SharedPreferences;

import java.security.MessageDigest;

/** Everything the parent can change lives here. The PIN is stored as a salted SHA-256. */
final class Prefs {
    static final String KEY_PHONE = "phone";
    static final String KEY_SMS = "sms";
    static final String KEY_CAMERA = "camera";
    static final String KEY_MAPS = "maps";
    static final String KEY_SKYSS = "skyss";
    static final String KEY_CHESS = "chess";
    static final String KEY_PARENT_NUMBER = "parent_number";

    static final String DEFAULT_PIN = "1234";

    private static final String FILE = "safestart";
    private final SharedPreferences sp;

    Prefs(Context c) {
        sp = c.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }

    /** Telefon is always true: it is the one thing we promise. */
    boolean isAllowed(String key) {
        if (KEY_PHONE.equals(key)) {
            return true;
        }
        return sp.getBoolean("allow_" + key, true);
    }

    void setAllowed(String key, boolean value) {
        if (KEY_PHONE.equals(key)) {
            return;
        }
        sp.edit().putBoolean("allow_" + key, value).apply();
    }

    /**
     * True while the parent has unlocked the phone from the parent screen.
     *
     * Lock task mode belongs to the task that started it (HomeActivity), so
     * "Laas opp telefonen" cannot end it from ParentActivity. Instead it raises
     * this flag and closes itself; HomeActivity.onResume then leaves lock task
     * mode instead of re-entering it. Locking again lowers the flag.
     */
    boolean isUnlocked() {
        return sp.getBoolean("unlocked", false);
    }

    void setUnlocked(boolean value) {
        sp.edit().putBoolean("unlocked", value).apply();
    }

    boolean checkPin(String pin) {
        return pin != null && hash(pin).equals(sp.getString("pin_hash", hash(DEFAULT_PIN)));
    }

    /** How many digits the stored PIN has, so the dialog knows when to judge. */
    int pinLength() {
        return sp.getInt("pin_len", DEFAULT_PIN.length());
    }

    /** The number behind the «Mamma & Pappa» button, empty until a parent sets it. */
    String parentNumber() {
        return sp.getString(KEY_PARENT_NUMBER, "").replace(" ", "");
    }

    void setParentNumber(String number) {
        sp.edit().putString(KEY_PARENT_NUMBER, number == null ? "" : number.trim()).apply();
    }

    void setPin(String pin) {
        sp.edit().putString("pin_hash", hash(pin)).putInt("pin_len", pin.length()).apply();
    }

    int fails() {
        return sp.getInt("fails", 0);
    }

    long lockedUntil() {
        return sp.getLong("locked_until", 0L);
    }

    long registerFail() {
        int f = fails() + 1;
        SharedPreferences.Editor e = sp.edit().putInt("fails", f);
        if (f >= 5) {
            e.putLong("locked_until", System.currentTimeMillis() + 30000L).putInt("fails", 0);
        }
        e.apply();
        return lockedUntil();
    }

    void clearFails() {
        sp.edit().putInt("fails", 0).putLong("locked_until", 0L).apply();
    }

    String skyssPackage() {
        return sp.getString("skyss_pkg", "");
    }

    private static String hash(String pin) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest(("safestart:" + pin).getBytes("UTF-8"));
            StringBuilder sb = new StringBuilder(d.length * 2);
            for (byte b : d) {
                sb.append(Character.forDigit((b >> 4) & 0xF, 16));
                sb.append(Character.forDigit(b & 0xF, 16));
            }
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }
}
