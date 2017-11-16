package com.mikecorrigan.android.c2dm;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class C2DMBroadcastReceiver extends BroadcastReceiver {
	private static final String TAG = C2DMBroadcastReceiver.class.getSimpleName();

	@Override
	public final void onReceive(Context context, Intent intent) {
		Log.d(TAG, "onReceive: context=" + context + ", intent=" + intent);

		Registrar.c2dmOnReceive(context, intent);
		setResult(Activity.RESULT_OK, null, null);
	}
}
