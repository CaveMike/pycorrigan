package com.mikecorrigan.android.c2dm;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.apache.http.Header;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.CookieStore;
import org.apache.http.client.methods.HttpEntityEnclosingRequestBase;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.client.methods.HttpRequestBase;
import org.apache.http.client.params.ClientPNames;
import org.apache.http.client.params.HttpClientParams;
import org.apache.http.client.protocol.ClientContext;
import org.apache.http.cookie.Cookie;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.BasicCookieStore;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.params.BasicHttpParams;
import org.apache.http.params.HttpParams;
import org.apache.http.protocol.BasicHttpContext;
import org.json.JSONException;
import org.json.JSONObject;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.accounts.AccountManagerCallback;
import android.accounts.AccountManagerFuture;
import android.app.AlarmManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Binder;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.os.Message;
import android.os.PowerManager;
import android.provider.Settings.Secure;
import android.util.Log;

public class Registrar extends Service {
	static final String TAG = Registrar.class.getSimpleName();

	public interface Listener {
		public void onRegistrationNotification(String accountName,
				String state, String substate);

		public void onLaunchIntent(Intent intent);

		public void onMessage(Context context, Intent intent);
	}

	// PREFERENCES
	private static final String SHARED_PREFS = Registrar.class.getSimpleName()
			.toUpperCase(Locale.ENGLISH) + "_PREFS";

	// Key for account name in shared preferences.
	private static final String ACCOUNT_NAME = "accountName";

	// Key for auth cookie name in shared preferences.
	private static final String AUTH_COOKIE = "authCookie";

	// Key for device registration id in shared preferences.
	private static final String DEVICE_REGISTRATION_ID = "regId";

	private static final String C2DM_BACKOFF = "backoff";
	private static final long DEFAULT_BACKOFF = 30000;
	private static final long BACKOFF_MULTIPLIER = 2;
	private static final long MAX_BACKOFF = 600000;

	private static final String LAST_CHANGE = "lastChange";

	private static final String REGISTRATION_STATE = "state";
	public static final String REGISTRATION_STATE_ERROR = "ERROR";
	public static final String REGISTRATION_STATE_INVALID = "INVALID";
	public static final String REGISTRATION_STATE_REGISTERING = "REGISTERING";
	public static final String REGISTRATION_STATE_REGISTERED = "REGISTERED";
	public static final String REGISTRATION_STATE_UNREGISTERING = "UNREGISTERING";
	public static final String REGISTRATION_STATE_UNREGISTERED = "UNREGISTERED";

	private static final String REGISTRATION_SUBSTATE = "subState";
	public static final String REGISTRATION_SUBSTATE_NONE = "NONE";

	// REGISTRATION_STATE_REGISTERING
	public static final String REGISTRATION_SUBSTATE_PROMPTING_USER = "PROMPTING_USER";
	public static final String REGISTRATION_SUBSTATE_INVALIDATED_AUTH_TOKEN = "INVALIDATED_AUTH_TOKEN";
	public static final String REGISTRATION_SUBSTATE_HAVE_AUTH_TOKEN = "HAVE_AUTH_TOKEN";
	public static final String REGISTRATION_SUBSTATE_HAVE_AUTH_COOKIE = "HAVE_AUTH_COOKIE";
	public static final String REGISTRATION_SUBSTATE_HAVE_REG_ID = "HAVE_REG_ID";

	// REGISTRATION_STATE_ERROR
	public static final String REGISTRATION_SUBSTATE_ERROR_C2DM_NOT_FOUND = "ERROR_C2DM_NOT_FOUND";
	public static final String REGISTRATION_SUBSTATE_ERROR_REGISTER = "ERROR_REGISTER";
	public static final String REGISTRATION_SUBSTATE_ERROR_REG_ID = "ERROR_REG_ID";
	public static final String REGISTRATION_SUBSTATE_ERROR_AUTH_COOKIE = "ERROR_AUTH_COOKIE";
	public static final String REGISTRATION_SUBSTATE_ERROR_AUTH_TOKEN = "ERROR_AUTH_TOKEN";
	public static final String REGISTRATION_SUBSTATE_ERROR_UNREGISTER = "ERROR_UNREGISTER";

	private static final int EVENT_INITIALIZE = 0;
	private static final int EVENT_UNINITIALIZE = 1;
	private static final int EVENT_REGISTER = 2;
	private static final int EVENT_REREGISTER = 3;
	private static final int EVENT_UNREGISTER = 4;
	private static final int EVENT_C2DM_REGISTRATION_RESPONSE = 5;
	private static final int EVENT_C2DM_MESSAGE = 6;
	private static final int EVENT_C2DM_RETRY_REGISTRATION = 7;
	private static final int EVENT_APP_ENGINE_REGISTER = 8;
	private static final int EVENT_APP_ENGINE_UNREGISTER = 9;
	private static final int EVENT_APP_ENGINE_SEND_REQUEST = 11;
	private static final int EVENT_APP_ENGINE_SEND_RESPONSE = 12;

	//
	private static final String ACCOUNT_TYPE = "com.google";

	// Cookie name for authorization.
	private static final String AUTH_COOKIE_NAME = "SACSID";

	private final String getBaseUrl() {
		return "https://" + mAppName + ".appspot.com";
	}

	// C2DM Request intents and extras.
	private static final String GSF_PACKAGE = "com.google.android.gsf";

	private static final String REQUEST_UNREGISTRATION_INTENT = "com.google.android.c2dm.intent.UNREGISTER";
	private static final String REQUEST_REGISTRATION_INTENT = "com.google.android.c2dm.intent.REGISTER";

	private static final String EXTRA_APPLICATION_PENDING_INTENT = "app";
	private static final String EXTRA_SENDER = "sender";

	// C2DM Response intents and extras.
	private static final String C2DM_INTENT_REGISTRATION = "com.google.android.c2dm.intent.REGISTRATION";

	public static final String EXTRA_REGISTRATION_ID = "registration_id";

	// Indicates an unregister response. Otherwise it is a register response.
	public static final String EXTRA_UNREGISTERED = "unregistered";

	// Error codes for the registration intent.
	public static final String EXTRA_ERROR = "error";
	public static final String ERR_SERVICE_NOT_AVAILABLE = "SERVICE_NOT_AVAILABLE";
	public static final String ERR_ACCOUNT_MISSING = "ACCOUNT_MISSING";
	public static final String ERR_AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED";
	public static final String ERR_TOO_MANY_REGISTRATIONS = "TOO_MANY_REGISTRATIONS";
	public static final String ERR_INVALID_PARAMETERS = "INVALID_PARAMETERS";
	public static final String ERR_INVALID_SENDER = "INVALID_SENDER";
	public static final String ERR_PHONE_REGISTRATION_ERROR = "PHONE_REGISTRATION_ERROR";

	private static final String C2DM_INTENT_RECEIVE = "com.google.android.c2dm.intent.RECEIVE";

	// Internal intent to trigger registration re-tries.
	private static final String C2DM_INTENT_RETRY = "com.google.android.c2dm.intent.RETRY";

	// Android C2DM device type.
	private static final String C2DM_DEVICE_TYPE = "ac2dm";

	// STATE
	private final IBinder mBinder = new _Binder();

	private Context mContext;
	private Handler mHandler;
	private HandlerThread mHandlerThread;

	private String mAppName;
	private String mSenderId;

	private Listener mListener = null;

	private final String mAccountType = ACCOUNT_TYPE;
	private String mAccountName;

	private boolean mNeedInvalidate;
	private String mAuthToken;

	private Cookie mAuthCookie;

	private String mRegId;

	private String mState = REGISTRATION_STATE_INVALID;
	private String mSubState = REGISTRATION_SUBSTATE_NONE;

	private long mBackoffTime = DEFAULT_BACKOFF;
	private long mLastChange = 0;

	private static final String WAKELOCK_KEY = "REG_SVC";
	private static PowerManager.WakeLock mWakeLock;

	public static Registrar getService(IBinder binder) {
		Log.v(TAG, "getService: binder=" + binder);
		return ((Registrar._Binder) binder).getService();
	}

	private class _Binder extends Binder {
		private Registrar getService() {
			Log.v(TAG, "getService");
			return Registrar.this;
		}
	}

	@Override
	public int onStartCommand(Intent intent, int flags, int startId) {
		Log.v(TAG, "onStartCommand: intent=" + intent + ", flags=" + flags
				+ ", startId=" + startId);

		c2dmHandleIntent(intent);

		return Registrar.START_NOT_STICKY;
	}

	@Override
	public IBinder onBind(Intent intent) {
		Log.v(TAG, "onBind: intent=" + intent);
		return mBinder;
	}

	@Override
	public void onCreate() {
		Log.v(TAG, "onCreate: ");
		super.onCreate();

		mHandlerThread = new HandlerThread(TAG + "Thread");
		mHandlerThread.start();
		mHandler = new _Handler(mHandlerThread.getLooper());
	}

	@Override
	public void onDestroy() {
		Log.v(TAG, "onDestroy: ");
		super.onDestroy();

		mHandlerThread.quit();

		mHandlerThread = null;
		mHandler = null;
	}

	// THREADING: Called in the application's context.
	public synchronized void initialize(Context context, String appName,
			String senderId, Listener listener) {
		Log.v(TAG, "create: appName=" + appName + ", senderId=" + senderId
				+ ", listener=" + listener);

		// Validate parameters.
		if (context == null) {
			Log.e(TAG, "Create failed, invalid context.");
			return;
		}

		if (appName == null || appName.length() == 0) {
			Log.e(TAG, "Create failed, invalid app name.");
			return;
		}

		if (senderId == null || senderId.length() == 0) {
			Log.e(TAG, "Create failed, invalid sender id.");
			return;
		}

		// This is the only place that these variables can be set.
		// After this point, they are read-only.
		// Use synchronized to prevent multiple simultaneous calls.
		mContext = context;
		mAppName = appName;
		mSenderId = senderId;

		mHandler.sendMessage(mHandler.obtainMessage(EVENT_INITIALIZE, listener));
	}

	public void uninitialize() {
		Log.v(TAG, "uninitialize");
		mHandler.sendEmptyMessage(EVENT_UNINITIALIZE);
	}

	// THREADING: Called in the application's context.
	public void register(final String accountName) {
		Log.v(TAG, "register");

		if (accountName == null || accountName.length() == 0) {
			Log.e(TAG, "Invalid account name.");
			return;
		}

		mHandler.sendMessage(mHandler
				.obtainMessage(EVENT_REGISTER, accountName));
	}

	// THREADING: Called in the application's context.
	public void reregister() {
		Log.v(TAG, "reregister");
		mHandler.sendEmptyMessage(EVENT_REREGISTER);
	}

	// THREADING: Called in the application's context.
	public void unregister() {
		Log.v(TAG, "unregister");
		mHandler.sendEmptyMessage(EVENT_UNREGISTER);
	}

	// THREADING: Called in the application's context.
	public void clear() {
		unregister();

		// TODO: This is a bug. Unregister is async and takes a while.
		// TODO: Move this to the event handler.

		clearPreferences();

		mAccountName = null;
		mNeedInvalidate = true;
		mAuthToken = null;
		mAuthCookie = null;
		mRegId = null;
		mState = REGISTRATION_STATE_REGISTERING;
		mSubState = REGISTRATION_SUBSTATE_NONE;
	}

	// THREADING: Called in the application's context.
	// It is possible for mHandlerThread to modify mAccountName at
	// the same time, but that is ok. That is the nature of
	// asynchronous communications.
	public String getAccountName() {
		return mAccountName;
	}

	// THREADING: Called in the application's context.
	// It is possible for mHandlerThread to modify mState at
	// the same time, but that is ok. That is the nature of
	// asynchronous communications.
	public boolean isRegistered() {
		return mState.equals(REGISTRATION_STATE_REGISTERED);
	}

	// TODO: Add threading info
	public void sendMessage(String message, List<String> recipients) {
		Log.v(TAG, "appEngineSendMessage: message=" + message + ", recipients="
				+ recipients);

		if (message == null || message.length() == 0 || recipients == null
				|| recipients.size() == 0) {
			Log.e(TAG, "sendMessage: Invalid parameter.");
		}

		// TODO: Implement.
	}

	// TODO: Add threading info
	public void sendRequest(String url, String body) {
		Log.e(TAG, "sendRequest:");

		// TODO: Implement.
	}

	private class _Handler extends Handler {
		public _Handler(Looper looper) {
			super(looper);
			Log.d(TAG, "_Handler: looper=" + looper);
		}

		@Override
		public void handleMessage(Message msg) {
			Log.d(TAG, "handleMessage: msg=" + msg);
			switch (msg.what) {
			// TODO: Enforce the registration state-machine.
			case EVENT_INITIALIZE: {
				Listener listener = (Listener) msg.obj;
				handleInitialize(listener);
				break;
			}
			case EVENT_UNINITIALIZE: {
				// TODO: Implement
				break;
			}
			case EVENT_REGISTER: {
				String accountName = (String) msg.obj;
				handleRegister(accountName);
				break;
			}
			case EVENT_REREGISTER: {
				requestAuthToken();
				break;
			}
			case EVENT_UNREGISTER: {
				handleUnregister();
				break;
			}
			case EVENT_C2DM_REGISTRATION_RESPONSE: {
				Intent intent = (Intent) msg.obj;
				c2dmHandleRegistrationResponse(mContext, intent);
				break;
			}
			case EVENT_C2DM_MESSAGE: {
				Intent intent = (Intent) msg.obj;
				notifyMessage(mContext, intent);
				break;
			}
			case EVENT_C2DM_RETRY_REGISTRATION: {
				// Intent intent = (Intent) msg.obj;
				c2dmRegister(mContext, mSenderId);
				break;
			}
			case EVENT_APP_ENGINE_REGISTER: {
				appEngineRegister();
				break;
			}
			case EVENT_APP_ENGINE_UNREGISTER: {
				appEngineUnregister();
				break;
			}
			case EVENT_APP_ENGINE_SEND_REQUEST: {
				appEngineDevicePublish((String)msg.obj);
				break;
			}
			case EVENT_APP_ENGINE_SEND_RESPONSE: {
				// TODO: Implement
				break;
			}
			default: {
				Log.e(TAG, "Unknown message, " + msg);
			}
			}
		}
	}

	private void handleInitialize(Listener listener) {
		if (listener == null) {
			Log.e(TAG, "Initialization failed, invalid listener.");
			return;
		}

		// Ensure that this is the first call to create().
		if (!mState.equals(REGISTRATION_STATE_INVALID)) {
			Log.e(TAG, "Create failed, already initialized.");
			return;
		}

		mListener = listener;
		readPreferences();
	}

	private void handleRegister(String accountName) {
		if (isRegistered()) {
			Log.i(TAG, "Registered, ignoring register.");
			return;
		}

		mAccountName = accountName;
		mNeedInvalidate = true;
		mAuthToken = null;
		mAuthCookie = null;
		mRegId = null;
		mState = REGISTRATION_STATE_REGISTERING;
		mSubState = REGISTRATION_SUBSTATE_NONE;
		writePreferences();

		requestAuthToken();
	}

	private void handleUnregister() {
		if (!isRegistered()) {
			Log.i(TAG, "Not registered, ignoring unregister.");
			return;
		}

		c2dmUnregister(mContext);
	}

	// THREADING: Called in the context of mHandlerThread only.
	private void notifyLaunchIntent(Intent intent) {
		Log.v(TAG, "notifyLaunchIntent: intent=" + intent);

		if (mListener != null) {
			mListener.onLaunchIntent(intent);
		}
	}

	// THREADING: Called in the context of mHandlerThread only.
	private void notifyMessage(Context context, Intent intent) {
		Log.v(TAG, "notifyMessage: context=" + context + ", intent=" + intent);

		if (mListener != null) {
			mListener.onMessage(context, intent);
		}
	}

	// THREADING: Called in the context of mHandlerThread only.
	private void notifyListeners() {
		Log.v(TAG, "notifyListeners: accountName=" + mAccountName + ", mState="
				+ mState + ", mSubState=" + mSubState);

		if (mListener != null) {
			mListener.onRegistrationNotification(mAccountName, mState,
					mSubState);
		}
	}

	// THREADING: Called in the context of mHandlerThread only.
	private void setStateAndNotify(String state, String substate) {
		mState = state;
		mSubState = substate;
		writePreferences();

		notifyListeners();
	}

	// THREADING: Called in the context of mHandlerThread only.
	private void readPreferences() {
		Log.v(TAG, "readPreferences: name=" + SHARED_PREFS);

		SharedPreferences prefs = mContext.getSharedPreferences(SHARED_PREFS,
				Context.MODE_PRIVATE);
		mAccountName = prefs.getString(ACCOUNT_NAME, null);
		// FIXME: mAuthCookie = prefs.getString(AUTH_COOKIE, null);
		mRegId = prefs.getString(DEVICE_REGISTRATION_ID, null);
		mState = prefs
				.getString(REGISTRATION_STATE, REGISTRATION_STATE_INVALID);
		mSubState = prefs.getString(REGISTRATION_SUBSTATE,
				REGISTRATION_SUBSTATE_NONE);
		mBackoffTime = prefs.getLong(C2DM_BACKOFF, DEFAULT_BACKOFF);
		mLastChange = prefs.getLong(LAST_CHANGE, 0);

		Log.d(TAG, ACCOUNT_NAME + "=" + mAccountName);
		Log.d(TAG, AUTH_COOKIE + "=" + mAuthCookie);
		Log.d(TAG, DEVICE_REGISTRATION_ID + "=" + mRegId);
		Log.d(TAG, REGISTRATION_STATE + "=" + mState);
		Log.d(TAG, REGISTRATION_SUBSTATE + "=" + mSubState);
		Log.d(TAG, C2DM_BACKOFF + "=" + mBackoffTime);
		Log.d(TAG, LAST_CHANGE + "=" + mLastChange);
	}

	// THREADING: Called in the context of mHandlerThread only.
	private void writePreferences() {
		Log.v(TAG, "writePreferences: name=" + SHARED_PREFS);

		SharedPreferences prefs = mContext.getSharedPreferences(SHARED_PREFS,
				Context.MODE_PRIVATE);
		SharedPreferences.Editor editor = prefs.edit();
		editor.putString(ACCOUNT_NAME, mAccountName);
		// FIXME: editor.putString(AUTH_COOKIE, mAuthCookie);
		editor.putString(DEVICE_REGISTRATION_ID, mRegId);
		editor.putString(REGISTRATION_STATE, mState);
		editor.putString(REGISTRATION_SUBSTATE, mSubState);
		editor.putLong(C2DM_BACKOFF, mBackoffTime);
		editor.putLong(LAST_CHANGE, mLastChange);
		editor.commit();

		Log.d(TAG, ACCOUNT_NAME + "=" + mAccountName);
		Log.d(TAG, AUTH_COOKIE + "=" + mAuthCookie);
		Log.d(TAG, DEVICE_REGISTRATION_ID + "=" + mRegId);
		Log.d(TAG, REGISTRATION_STATE + "=" + mState);
		Log.d(TAG, REGISTRATION_SUBSTATE + "=" + mSubState);
		Log.d(TAG, C2DM_BACKOFF + "=" + mBackoffTime);
		Log.d(TAG, LAST_CHANGE + "=" + mLastChange);
	}

	// THREADING: Called in the context of mHandlerThread only.
	private void clearPreferences() {
		Log.v(TAG, "clearPreferences: name=" + SHARED_PREFS);

		SharedPreferences prefs = mContext.getSharedPreferences(SHARED_PREFS,
				Context.MODE_PRIVATE);
		SharedPreferences.Editor editor = prefs.edit();
		editor.remove(ACCOUNT_NAME);
		editor.remove(AUTH_COOKIE);
		editor.remove(DEVICE_REGISTRATION_ID);
		editor.remove(REGISTRATION_STATE);
		editor.remove(REGISTRATION_SUBSTATE);
		editor.commit();
	}

	// Returns a list of account names of the specified type. If no appropriate
	// accounts are
	// registered on the device, a zero-length list is returned.
	public static List<String> getAccounts(Context context) {
		Log.v(TAG, "getAccountsByType: accountType=" + ACCOUNT_TYPE);

		final AccountManager mgr = AccountManager.get(context);
		ArrayList<String> result = new ArrayList<String>();
		final Account[] accounts = mgr.getAccounts();
		for (final Account account : accounts) {
			Log.v(TAG, "accountName=" + account.name);
			if (account.type.equals(ACCOUNT_TYPE)) {
				result.add(account.name);
			}
		}

		return result;
	}

	private Account getAccount() {
		final AccountManager mgr = AccountManager.get(mContext);
		final Account[] accounts = mgr.getAccountsByType(mAccountType);
		for (final Account account : accounts) {
			if (account.name.equals(mAccountName)) {
				return account;
			}
		}

		return null;
	}

	private void requestAuthToken() {
		Log.v(TAG, "requestAuthToken");

		final AccountManager mgr = AccountManager.get(mContext);
		final Account account = getAccount();
		if (account == null) {
			Log.e(TAG, "Failed to find account: accountType=" + mAccountType
					+ ", accountName=" + mAccountName);
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_AUTH_TOKEN);
			return;
		}

		mgr.getAuthToken(account, "ah", false, new AuthTokenCallback(),
				mHandler);
	}

	@SuppressWarnings("unchecked")
	private class AuthTokenCallback implements AccountManagerCallback<Bundle> {
		@Override
		public void run(AccountManagerFuture<Bundle> future) {
			Log.i(TAG, "AuthTokenCallback");
			handleAuthToken(future);
		}
	}

	private void handleAuthToken(AccountManagerFuture<Bundle>... tokens) {
		Log.v(TAG, "handleAuthToken");

		try {
			Bundle result = tokens[0].getResult();

			Intent intent = (Intent) result.get(AccountManager.KEY_INTENT);
			if (intent != null) {
				Log.i(TAG, "Launch activity before getting authToken: intent="
						+ intent);

				setStateAndNotify(REGISTRATION_STATE_REGISTERING,
						REGISTRATION_SUBSTATE_PROMPTING_USER);

				intent.setFlags(intent.getFlags()
						& ~Intent.FLAG_ACTIVITY_NEW_TASK);
				notifyLaunchIntent(intent);
				return;
			}

			String authToken = result.getString(AccountManager.KEY_AUTHTOKEN);
			if (mNeedInvalidate) {
				mNeedInvalidate = false;

				Log.i(TAG, "Invalidating token and starting over.");

				// Invalidate auth token.
				AccountManager mgr = AccountManager.get(mContext);
				mgr.invalidateAuthToken(mAccountType, authToken);

				setStateAndNotify(REGISTRATION_STATE_REGISTERING,
						REGISTRATION_SUBSTATE_INVALIDATED_AUTH_TOKEN);

				// Initiate the request again.
				requestAuthToken();
				return;
			} else {
				Log.i(TAG, "Received authToken=" + authToken);
				mAuthToken = authToken;
				setStateAndNotify(REGISTRATION_STATE_REGISTERING,
						REGISTRATION_SUBSTATE_HAVE_AUTH_TOKEN);

				// Move on to the next step, request auth cookie.
				requestAuthCookie();
				return;
			}
		} catch (Exception e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
		}

		setStateAndNotify(REGISTRATION_STATE_ERROR,
				REGISTRATION_SUBSTATE_ERROR_AUTH_TOKEN);
		return;
	}

	private void requestAuthCookie() {
		DefaultHttpClient httpClient = new DefaultHttpClient();
		try {
			String continueURL = getBaseUrl();
			URI uri = new URI(getBaseUrl() + "/_ah/login?continue="
					+ URLEncoder.encode(continueURL, "UTF-8") + "&auth="
					+ mAuthToken);
			HttpGet method = new HttpGet(uri);

			final HttpParams getParams = new BasicHttpParams();
			HttpClientParams.setRedirecting(getParams, false);
			method.setParams(getParams);

			HttpResponse res = httpClient.execute(method);
			Header[] headers = res.getHeaders("Set-Cookie");
			int statusCode = res.getStatusLine().getStatusCode();
			Log.v(TAG, "statusCode=" + statusCode);
			if (statusCode != 302 || headers.length == 0) {
				Log.e(TAG, "Failed to get authCookie: statusCode=" + statusCode);
				setStateAndNotify(REGISTRATION_STATE_ERROR,
						REGISTRATION_SUBSTATE_ERROR_AUTH_COOKIE);
				return;
			}

			for (Cookie cookie : httpClient.getCookieStore().getCookies()) {
				Log.v(TAG, "cookie=" + cookie.getName());
				if (AUTH_COOKIE_NAME.equals(cookie.getName())) {
					Log.i(TAG, "Received authCookie=" + cookie);
					mAuthCookie = cookie;
					setStateAndNotify(REGISTRATION_STATE_REGISTERING,
							REGISTRATION_SUBSTATE_HAVE_AUTH_COOKIE);

					// Move on to the next step, register to C2DM.
					c2dmRegister(mContext, mSenderId);
					return;
				}
			}
		} catch (IOException e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
		} catch (URISyntaxException e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
		} finally {
			httpClient.getParams().setBooleanParameter(
					ClientPNames.HANDLE_REDIRECTS, true);
		}

		setStateAndNotify(REGISTRATION_STATE_ERROR,
				REGISTRATION_SUBSTATE_ERROR_AUTH_COOKIE);
		return;
	}

	private void c2dmRegister(Context context, String senderId) {
		Log.d(TAG, "c2dmRegister: context=" + context + ", senderId="
				+ senderId);

		Intent intent = new Intent(REQUEST_REGISTRATION_INTENT);
		intent.setPackage(GSF_PACKAGE);
		intent.putExtra(EXTRA_APPLICATION_PENDING_INTENT,
				PendingIntent.getBroadcast(context, 0, new Intent(), 0));
		intent.putExtra(EXTRA_SENDER, senderId);
		ComponentName name = context.startService(intent);
		if (name == null) {
			// Service not found.
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_C2DM_NOT_FOUND);
		}
	}

	private void c2dmUnregister(Context context) {
		Log.d(TAG, "c2dmUnregister: context=" + context);

		Intent intent = new Intent(REQUEST_UNREGISTRATION_INTENT);
		intent.setPackage(GSF_PACKAGE);
		intent.putExtra(EXTRA_APPLICATION_PENDING_INTENT,
				PendingIntent.getBroadcast(context, 0, new Intent(), 0));
		ComponentName name = context.startService(intent);
		if (name == null) {
			// Service not found.
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_C2DM_NOT_FOUND);
		}
	}

	public static void c2dmOnReceive(Context context, Intent intent) {
		Log.d(TAG, "c2dmOnReceive: context=" + context + ", intent=" + intent);

		if (mWakeLock == null) {
			// This is called from a BroadcastReceiver, there is no init.
			PowerManager pm = (PowerManager) context
					.getSystemService(Context.POWER_SERVICE);
			mWakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,
					WAKELOCK_KEY);
		}
		mWakeLock.acquire();

		intent.setClass(context, Registrar.class);
		context.startService(intent);
	}

	private void c2dmHandleIntent(Intent intent) {
		Log.d(TAG, "c2dmHandleIntent: intent=" + intent);

		try {
			if (intent.getAction().equals(C2DM_INTENT_REGISTRATION)) {
				mHandler.sendMessage(mHandler.obtainMessage(
						EVENT_C2DM_REGISTRATION_RESPONSE, intent));
			} else if (intent.getAction().equals(C2DM_INTENT_RECEIVE)) {
				mHandler.sendMessage(mHandler.obtainMessage(EVENT_C2DM_MESSAGE,
						intent));
			} else if (intent.getAction().equals(C2DM_INTENT_RETRY)) {
				mHandler.sendMessage(mHandler.obtainMessage(
						EVENT_C2DM_RETRY_REGISTRATION, intent));
			}
		} finally {
			// Release the power lock, so device can go back to sleep.
			// The lock is reference counted by default, so multiple
			// messages are ok.

			// If the onMessage() needs to spawn a thread or do something else,
			// it should use it's own lock.
			mWakeLock.release();
		}
	}

	private void c2dmHandleRegistrationResponse(final Context context,
			Intent intent) {
		Log.d(TAG, "c2dmHandleRegistrationResponse: context=" + context
				+ ", intent=" + intent);

		final String registrationId = intent
				.getStringExtra(EXTRA_REGISTRATION_ID);
		String error = intent.getStringExtra(EXTRA_ERROR);
		String unregistered = intent.getStringExtra(EXTRA_UNREGISTERED);

		Log.d(TAG, "handleRegistration: registrationId = " + registrationId
				+ ", error = " + error + ", unregistered = " + unregistered);

		mLastChange = System.currentTimeMillis();

		if (unregistered != null) {
			// Unregistered
			mRegId = null;
			setStateAndNotify(REGISTRATION_STATE_UNREGISTERING,
					REGISTRATION_SUBSTATE_NONE);

			mHandler.sendEmptyMessage(EVENT_APP_ENGINE_UNREGISTER);
		} else if (error != null) {
			// Registration failed.
			Log.e(TAG, "Registration error " + error);

			mRegId = null;
			setStateAndNotify(REGISTRATION_STATE_ERROR, error);

			if ("SERVICE_NOT_AVAILABLE".equals(error)) {
				// For this error, try again later.
				Log.d(TAG, "Scheduling registration retry, backoff = "
						+ mBackoffTime);
				Intent retryIntent = new Intent(C2DM_INTENT_RETRY);
				PendingIntent retryPIntent = PendingIntent
						.getBroadcast(context, 0 /* requestCode */, retryIntent,
								0 /* flags */);

				AlarmManager am = (AlarmManager) context
						.getSystemService(Context.ALARM_SERVICE);
				am.set(AlarmManager.ELAPSED_REALTIME, mBackoffTime,
						retryPIntent);

				// Next retry should wait longer.
				mBackoffTime *= BACKOFF_MULTIPLIER;
				if (mBackoffTime > MAX_BACKOFF) {
					mBackoffTime = MAX_BACKOFF;
				}

				// Save the backoff time.
				writePreferences();
			}
		} else {
			mRegId = registrationId;
			setStateAndNotify(REGISTRATION_STATE_REGISTERING,
					REGISTRATION_SUBSTATE_HAVE_REG_ID);

			mHandler.sendEmptyMessage(EVENT_APP_ENGINE_REGISTER);
		}
	}

	private String appEngineRead(HttpRequestBase request) {
		Log.v(TAG, "appEngineRead");

		CookieStore mCookieStore = new BasicCookieStore();
		mCookieStore.addCookie(mAuthCookie);

		DefaultHttpClient httpClient = new DefaultHttpClient();
		BasicHttpContext mHttpContext = new BasicHttpContext();
		mHttpContext.setAttribute(ClientContext.COOKIE_STORE, mCookieStore);

		try {
			final HttpParams getParams = new BasicHttpParams();
			HttpClientParams.setRedirecting(getParams, false);
			request.setParams(getParams);

			request.setHeader("Accept", "application/json");

			HttpResponse response = httpClient.execute(request, mHttpContext);

			HttpEntity entity = response.getEntity();
			if (entity == null) {
				return null;
			}

			Log.d(TAG, "Status=" + response.getStatusLine());
			if (response.getStatusLine().getStatusCode() != 200) {
				return null;
			}

			InputStream is = entity.getContent();
			BufferedReader reader = new BufferedReader(new InputStreamReader(
					is, "utf-8"), 8);
			StringBuilder sb = new StringBuilder();
			String line = null;
			while ((line = reader.readLine()) != null) {
				sb.append(line + "\n");
			}
			is.close();

			return sb.toString();
		} catch (IOException e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
		} finally {
			httpClient.getParams().setBooleanParameter(
					ClientPNames.HANDLE_REDIRECTS, true);
		}

		return null;
	}

	private int appEngineWrite(HttpEntityEnclosingRequestBase request,
			HttpEntity entity) {
		Log.v(TAG, "appEngineWrite");

		CookieStore mCookieStore = new BasicCookieStore();
		mCookieStore.addCookie(mAuthCookie);

		DefaultHttpClient httpClient = new DefaultHttpClient();
		BasicHttpContext mHttpContext = new BasicHttpContext();
		mHttpContext.setAttribute(ClientContext.COOKIE_STORE, mCookieStore);

		try {
			final HttpParams getParams = new BasicHttpParams();
			HttpClientParams.setRedirecting(getParams, false);
			request.setParams(getParams);

			request.setHeader("Content-Type", "application/json");
			request.setHeader("Accept", "application/json");
			request.setEntity(entity);

			HttpResponse response = httpClient.execute(request, mHttpContext);
			Log.d(TAG, "Status=" + response.getStatusLine());
			return response.getStatusLine().getStatusCode();
		} catch (IOException e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
		} finally {
			httpClient.getParams().setBooleanParameter(
					ClientPNames.HANDLE_REDIRECTS, true);
		}

		return -1;
	}

	private void appEngineRegister() {
		Log.v(TAG, "registerAppEngine");

		String deviceId = Secure.getString(mContext.getContentResolver(),
				Secure.ANDROID_ID);
		Log.i(TAG, "deviceId=" + deviceId);

		URI uri;
		try {
			uri = new URI(getBaseUrl() + "/device/" + deviceId + "/");
		} catch (URISyntaxException e) {
			Log.w(TAG, "Registration failure: URI failed=" + e);
			mRegId = null;
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_REGISTER);
			return;
		}

		StringEntity entity;
		try {
			JSONObject j = new JSONObject();
			j.put("name", mAppName);
			j.put("reg_id", mRegId);
			j.put("dev_id", deviceId);
			j.put("type", C2DM_DEVICE_TYPE);
			entity = new StringEntity(j.toString());
		} catch (UnsupportedEncodingException e) {
			Log.w(TAG, "Registration failure: URI failed=" + e);
			mRegId = null;
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_REGISTER);
			return;
		} catch (JSONException e) {
			Log.w(TAG, "Registration failure: URI failed=" + e);
			mRegId = null;
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_REGISTER);
			return;
		}

		int statusCode = appEngineWrite(new HttpPut(uri), entity);
		if (statusCode == 200) {
			Log.v(TAG, "statusCode=" + statusCode);
			Log.v(TAG, "RegistrationReceiver.onSuccess:");
			setStateAndNotify(REGISTRATION_STATE_REGISTERED,
					REGISTRATION_SUBSTATE_NONE);
		} else {
			Log.w(TAG, "Registration failure: message=" + statusCode);
			mRegId = null;
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_REGISTER);
			return;
		}
	}

	private void appEngineUnregister() {
		Log.v(TAG, "unregisterAppEngine");

		String deviceId = Secure.getString(mContext.getContentResolver(),
				Secure.ANDROID_ID);
		Log.i(TAG, "deviceId=" + deviceId);

		URI uri;
		try {
			uri = new URI(getBaseUrl() + "/device/" + deviceId + "/");
		} catch (URISyntaxException e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
			// TODO: handle error
			return;
		}

		StringEntity entity;
		try {
			JSONObject j = new JSONObject();
			j.put("name", mAppName);
			j.put("reg_id", "");
			j.put("dev_id", deviceId);
			j.put("type", C2DM_DEVICE_TYPE);
			entity = new StringEntity(j.toString());
		} catch (UnsupportedEncodingException e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
			// TODO: handle error
			return;
		} catch (JSONException e) {
			Log.e(TAG, "Exception " + e);
			Log.e(TAG, Log.getStackTraceString(e));
			// TODO: handle error
			return;
		}

		int statusCode = appEngineWrite(new HttpPut(uri), entity);
		if (statusCode == 200) {
			Log.v(TAG, "Unregistration success: statusCode=" + statusCode);
			setStateAndNotify(REGISTRATION_STATE_UNREGISTERED,
					REGISTRATION_SUBSTATE_NONE);
		} else {
			Log.w(TAG, "Unregistration failure: message=" + statusCode);
			setStateAndNotify(REGISTRATION_STATE_ERROR,
					REGISTRATION_SUBSTATE_ERROR_UNREGISTER);
		}

		mRegId = null;
	}

	private void appEngineDevicePublish(final String message) {
		Log.v(TAG, "appEngineDevicePublish");

		String deviceId = Secure.getString(mContext.getContentResolver(),
				Secure.ANDROID_ID);
		Log.i(TAG, "deviceId=" + deviceId);

		URI uri;
		try {
			uri = new URI(getBaseUrl() + "/device/" + deviceId + "/publish/");
		} catch (URISyntaxException e) {
			Log.w(TAG, "failure: URI failed=" + e);
			return;
		}
		Log.d(TAG, "url=" + getBaseUrl() + "/device/" + deviceId + "/publish/");

		StringEntity entity;
		try {
			JSONObject j = new JSONObject();
			j.put("dev_id", deviceId);
			j.put("message", message);
			entity = new StringEntity(j.toString());
		} catch (UnsupportedEncodingException e) {
			Log.w(TAG, "failure: URI failed=" + e);
			return;
		} catch (JSONException e) {
			Log.w(TAG, "failure: URI failed=" + e);
			return;
		}

		int statusCode = appEngineWrite(new HttpPut(uri), entity);
		if (statusCode == 200) {
			Log.v(TAG, "statusCode=" + statusCode);
		} else {
			Log.w(TAG, "failure: message=" + statusCode);
			return;
		}
	}

	public void publishDevice(final String message) {
		Log.v(TAG, "publishDevice");
		mHandler.sendMessage(mHandler.obtainMessage(
				EVENT_APP_ENGINE_SEND_REQUEST, message));
	}

	@Override
	public String toString() {
		return "name=" + mAppName + ", accountType=" + mAccountType
				+ ", accountName=" + mAccountName + ", authToken=" + mAuthToken
				+ ", authCookie=" + mAuthCookie + ", regId=" + mRegId
				+ ", state=" + mState + ", substate=" + mSubState
				+ ", backoff=" + mBackoffTime + ", lastChange=" + mLastChange;
	}
}
