package no.safestart.qadialer;

import android.app.Activity;
import android.os.Bundle;

/** Stand-in messaging app for the QA harness (AOSP default images have none). */
public class SmsActivity extends Activity {

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        String data = getIntent() != null && getIntent().getData() != null
                ? getIntent().getDataString() : "(uten mottaker)";
        setContentView(DialActivity.ui(this, "QA SMS", getIntent().getAction() + "\n" + data));
    }
}
