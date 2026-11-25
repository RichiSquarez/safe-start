package no.safestart.kiosk;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.util.Log;

import android.os.UserManager;
import java.util.LinkedHashSet;
import java.util.Set;

/**
 * Kiosk wiring. Everything that actually blocks the child needs Device Owner;
 * without it we fall back to being the HOME app plus screen pinning.
 */
final class Kiosk {
    private static final String TAG = "Safestart";

    private Kiosk() {}

    static DevicePolicyManager dpm(Context c) {
        return (DevicePolicyManager) c.getSystemService(Context.DEVICE_POLICY_SERVICE);
    }

    static ComponentName admin(Context c) {
        return new ComponentName(c, AdminReceiver.class);
    }

    static boolean isDeviceOwner(Context c) {
        DevicePolicyManager d = dpm(c);
        return d != null && d.isDeviceOwnerApp(c.getPackageName());
    }

    static boolean isAdminActive(Context c) {
        DevicePolicyManager d = dpm(c);
        return d != null && d.isAdminActive(admin(c));
    }

    static boolean isLocked(Context c) {
        try {
            ActivityManager am = (ActivityManager) c.getSystemService(Context.ACTIVITY_SERVICE);
            return am != null && am.getLockTaskModeState() != ActivityManager.LOCK_TASK_MODE_NONE;
        } catch (Throwable t) {
            return false;
        }
    }

    /** Packages the child is allowed to reach while the screen is pinned. */
    static Set<String> allowlist(Context c, Prefs p) {
        Set<String> pkgs = new LinkedHashSet<>();
        pkgs.add(c.getPackageName());
        for (Catalog.Item it : Catalog.ALL) {
            if (!it.always && !p.isAllowed(it.key)) {
                continue;
            }
            String pkg = Catalog.resolvePackage(c, it, p);
            if (pkg != null) {
                pkgs.add(pkg);
            }
        }
        return pkgs;
    }

    /** Push the allowlist to the system and pin the screen. Only meaningful as Device Owner. */
    static void lock(Context c, Prefs p) {
        if (!isDeviceOwner(c)) {
            Log.i(TAG, "not device owner: falling back to plain screen pinning");
            return;
        }
        DevicePolicyManager d = dpm(c);
        Set<String> pkgs = allowlist(c, p);
        Log.i(TAG, "allowlist (" + pkgs.size() + "): " + pkgs);
        try {
            d.setLockTaskPackages(admin(c), pkgs.toArray(new String[0]));
        } catch (SecurityException e) {
            Log.w(TAG, "setLockTaskPackages denied", e);
        }
        // From API 28 the power menu ("global actions") is on by default inside
        // lock task, which hands the child Shut down / Restart / Emergency call.
        // From API 34 this policy and the allowlist above are applied together,
        // so a failure here can also drop the allowlist - keep them adjacent.
        if (android.os.Build.VERSION.SDK_INT >= 28) {
            try {
                d.setLockTaskFeatures(admin(c), DevicePolicyManager.LOCK_TASK_FEATURE_NONE);
            } catch (Throwable t) {
                Log.w(TAG, "setLockTaskFeatures not available", t);
            }
        }
        try {
            String[] applied = d.getLockTaskPackages(admin(c));
            Log.i(TAG, "applied allowlist: " + java.util.Arrays.toString(applied));
        } catch (Throwable t) {
            Log.w(TAG, "getLockTaskPackages not available", t);
        }
        try {
            if (!d.setStatusBarDisabled(admin(c), true)) {
                Log.w(TAG, "setStatusBarDisabled refused (status bar stays while unlocked)");
            }
        } catch (Throwable t) {
            Log.w(TAG, "setStatusBarDisabled not available", t);
        }
        try {
            if (!d.setKeyguardDisabled(admin(c), true)) {
                // A PIN/pattern/password is set, so the system keeps the keyguard
                // and the kiosk will not come back by itself after a reboot.
                Log.w(TAG, "keyguard not disabled: a screen lock is set");
                if (android.os.Build.VERSION.SDK_INT >= 24) {
                    d.setPasswordQuality(admin(c),
                            DevicePolicyManager.PASSWORD_QUALITY_UNSPECIFIED);
                }
            }
        } catch (Throwable t) {
            Log.w(TAG, "setKeyguardDisabled not available", t);
        }
        // Device Owner can grant the runtime permission permanently; the parent
        // screen cannot always do it, and API 30+ may auto-reset it.
        try {
            d.setPermissionGrantState(admin(c), c.getPackageName(),
                    android.Manifest.permission.CALL_PHONE,
                    DevicePolicyManager.PERMISSION_GRANT_STATE_GRANTED);
        } catch (Throwable t) {
            Log.w(TAG, "setPermissionGrantState not available", t);
        }
        // Safe mode would boot the system launcher with Safestart disabled, and
        // a factory reset would hand the child a plain phone again.
        try {
            d.addUserRestriction(admin(c), UserManager.DISALLOW_SAFE_BOOT);
            d.addUserRestriction(admin(c), UserManager.DISALLOW_FACTORY_RESET);
        } catch (Throwable t) {
            Log.w(TAG, "user restriction not available", t);
        }
        // Without a persistent preferred home the "choose a launcher" dialog can
        // appear before the kiosk takes over.
        try {
            IntentFilter home = new IntentFilter(Intent.ACTION_MAIN);
            home.addCategory(Intent.CATEGORY_HOME);
            home.addCategory(Intent.CATEGORY_DEFAULT);
            d.addPersistentPreferredActivity(admin(c), home,
                    new ComponentName(c, HomeActivity.class));
        } catch (Throwable t) {
            Log.w(TAG, "addPersistentPreferredActivity not available", t);
        }
    }

    /** Start lock task on this activity, if it is not already running. */
    static void enter(Activity a, Prefs p) {
        // Apply the policy every time, even when the task is already locked:
        // an earlier build (or a lost lock task) leaves the allowlist empty and
        // the restrictions unset, and this is the only place that repairs it.
        if (isDeviceOwner(a)) {
            lock(a, p);
        }
        if (isLocked(a)) {
            return;
        }
        try {
            a.startLockTask();
        } catch (Throwable t) {
            Log.w(TAG, "startLockTask failed", t);
        }
    }

    /** Parent escape hatch: leave lock task and give the phone back. */
    static void unlock(Activity a) {
        try {
            if (isLocked(a)) {
                a.stopLockTask();
            }
        } catch (Throwable t) {
            Log.w(TAG, "stopLockTask failed", t);
        }
        if (isDeviceOwner(a)) {
            try {
                dpm(a).setStatusBarDisabled(admin(a), false);
            } catch (Throwable ignored) {
            }
        }
    }

    private static long doorUntil = 0L;

    /** Called right after a correct PIN. ParentActivity refuses to open without this. */
    static void openDoor() {
        doorUntil = System.currentTimeMillis() + 5000L;
    }

    /** One-shot: true only once, within five seconds of a correct PIN. */
    static boolean doorOpen() {
        boolean ok = System.currentTimeMillis() <= doorUntil;
        doorUntil = 0L;
        return ok;
    }

    static String statusLine(Context c) {
        if (isDeviceOwner(c)) {
            return "Device Owner: aktiv \u2014 telefonen er l\u00e5st til Safestart";
        }
        if (isAdminActive(c)) {
            return "Device Admin: aktiv, men ikke Device Owner";
        }
        return "Ikke l\u00e5st: Safestart er bare hjemmeskjermen";
    }
}
