package no.safestart.kiosk;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Re-applies the kiosk policy after the phone has been restarted or the app has
 * been replaced. The Device Owner policies survive a reboot, but the lock task
 * itself does not, and a phone that comes back without it is a normal phone.
 *
 * Only DevicePolicyManager calls belong here - starting activities from a
 * receiver is restricted from API 29 and is not needed, because the persistent
 * preferred home activity already makes the system launch the kiosk.
 */
public final class BootReceiver extends BroadcastReceiver {
    private static final String TAG = "Safestart";

    public static final String ACTION_LOCKED_BOOT =
            "android.intent.action.LOCKED_BOOT_COMPLETED";

    @Override
    public void onReceive(Context c, Intent intent) {
        String action = intent == null ? "" : String.valueOf(intent.getAction());
        Log.i(TAG, "boot receiver: " + action);
        if (ACTION_LOCKED_BOOT.equals(action)) {
            // Before the user is unlocked the credential-encrypted prefs are not
            // readable, so the stored allowlist is unavailable. Nothing to do.
            return;
        }
        try {
            Kiosk.lock(c, new Prefs(c));
        } catch (Throwable t) {
            Log.w(TAG, "boot lock failed", t);
        }
    }
}
