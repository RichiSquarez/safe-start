package no.safestart.kiosk;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.provider.MediaStore;
import android.util.Log;

import java.util.ArrayList;
import java.util.List;

/** The things a child may do, and how each one is launched. */
final class Catalog {
    private static final String TAG = "Safestart";

    static final class Item {
        final String key;
        final String label;
        final String sub;
        final boolean always;
        final int icon;
        /** True for screens inside our own app (Sjakk), false for other apps. */
        final boolean internal;

        Item(String key, String label, String sub, boolean always, int icon) {
            this(key, label, sub, always, icon, false);
        }

        Item(String key, String label, String sub, boolean always, int icon, boolean internal) {
            this.key = key;
            this.label = label;
            this.sub = sub;
            this.always = always;
            this.icon = icon;
            this.internal = internal;
        }
    }

    /** Class name of our own chess screen, kept as a string so the tile compiles on its own. */
    static final String CHESS_CLASS = "no.safestart.kiosk.ChessActivity";

    static final Item PHONE = new Item(Prefs.KEY_PHONE, "Ring",
            "Alltid tilgjengelig", true, R.drawable.ic_phone);
    static final Item SMS = new Item(Prefs.KEY_SMS, "Meldinger",
            "SMS til kjente", false, R.drawable.ic_sms);
    static final Item CAMERA = new Item(Prefs.KEY_CAMERA, "Kamera",
            "Ta bilder", false, R.drawable.ic_camera);
    static final Item MAPS = new Item(Prefs.KEY_MAPS, "Kart",
            "Se hvor du er", false, R.drawable.ic_map);
    static final Item SKYSS = new Item(Prefs.KEY_SKYSS, "Skyss",
            "Bussbillett", false, R.drawable.ic_bus);
    static final Item CHESS = new Item(Prefs.KEY_CHESS, "Sjakk",
            "Mot en bot", false, R.drawable.ic_chess, true);

    static final Item[] ALL = {PHONE, SMS, CAMERA, MAPS, SKYSS, CHESS};

    private Catalog() {}

    static List<Item> visible(Context c, Prefs p) {
        List<Item> out = new ArrayList<>();
        for (Item it : ALL) {
            if (it.always || p.isAllowed(it.key)) {
                out.add(it);
            }
        }
        return out;
    }

    /** Package that actually handles this tile, or null when nothing is installed. */
    static String resolvePackage(Context c, Item it, Prefs p) {
        if (it.internal) {
            return c.getPackageName();
        }
        Intent i = intentFor(c, it, p);
        if (i == null) {
            return null;
        }
        PackageManager pm = c.getPackageManager();
        ResolveInfo ri = pm.resolveActivity(i, PackageManager.MATCH_DEFAULT_ONLY);
        return ri == null || ri.activityInfo == null ? null : ri.activityInfo.packageName;
    }

    static Intent intentFor(Context c, Item it, Prefs p) {
        if (it.internal) {
            return new Intent().setClassName(c, CHESS_CLASS);
        }
        if (it == PHONE) {
            return new Intent(Intent.ACTION_DIAL, Uri.parse("tel:"));
        }
        if (it == SMS) {
            Intent i = new Intent(Intent.ACTION_MAIN);
            i.addCategory("android.intent.category.APP_MESSAGING");
            if (c.getPackageManager().resolveActivity(i, 0) != null) {
                return i;
            }
            return new Intent(Intent.ACTION_VIEW, Uri.parse("sms:"));
        }
        if (it == CAMERA) {
            return new Intent(MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA);
        }
        if (it == MAPS) {
            return new Intent(Intent.ACTION_VIEW, Uri.parse("geo:60.3913,5.3221?q=Bergen"));
        }
        String pkg = skyssPackage(c, p);
        if (pkg == null) {
            return null;
        }
        Intent i = c.getPackageManager().getLaunchIntentForPackage(pkg);
        if (i == null) {
            i = new Intent(Intent.ACTION_MAIN);
            i.setPackage(pkg);
        }
        return i;
    }

    /** Skyss is not installed on a bare emulator, so try known ids and let the parent override. */
    static String skyssPackage(Context c, Prefs p) {
        String custom = p.skyssPackage();
        if (custom != null && custom.length() > 0 && isInstalled(c, custom)) {
            return custom;
        }
        String[] candidates = {"no.skyss.billett", "no.skyss.reise", "no.skyss", "no.skyss.tickets"};
        for (String cand : candidates) {
            if (isInstalled(c, cand)) {
                return cand;
            }
        }
        return null;
    }

    static boolean isInstalled(Context c, String pkg) {
        try {
            c.getPackageManager().getPackageInfo(pkg, 0);
            return true;
        } catch (android.content.pm.PackageManager.NameNotFoundException e) {
            // From API 30 the same exception also means "not visible to us",
            // which without a <queries> entry looks exactly like "not installed".
            android.util.Log.i("Safestart", "pakke ikke synlig eller installert: " + pkg);
            return false;
        } catch (Exception e) {
            return false;
        }
    }

    /** True when the tile can actually be opened on this phone. */
    static boolean available(Context c, Item it, Prefs p) {
        return resolvePackage(c, it, p) != null;
    }

    /** Returns true when something was actually started. */
    static boolean launch(Context c, Item it, Prefs p) {
        Intent i = intentFor(c, it, p);
        if (i == null) {
            return false;
        }
        try {
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
            return true;
        } catch (Exception e) {
            Log.w(TAG, "launch failed for " + it.key, e);
            return false;
        }
    }
}
