/*******************************************************************************
 * Copyright 2011 Google Inc. All Rights Reserved.
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * which accompanies this distribution, and is available at
 * http://www.eclipse.org/legal/epl-v10.html
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *******************************************************************************/

package com.mikecorrigan;

import java.util.ArrayList;
import java.util.List;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.util.Log;
import android.view.Menu;
import android.view.MenuInflater;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.Toast;

import com.mikecorrigan.android.c2dm.Registrar;

public class CorriganActivity extends Activity implements Registrar.Listener {
    private static final String TAG = CorriganActivity.class.getSimpleName();

    private static final String SENDER_ID = "462893092392";

    private Registrar registrar;
    private Button button;

    private ServiceConnection mConnection = new ServiceConnection() {
        @Override
        public void onServiceConnected(ComponentName className, IBinder binder) {
            Log.v(TAG, "onServiceConnected");

            registrar = Registrar.getService(binder);
            registrar.initialize(CorriganActivity.this, "pycorrigan", SENDER_ID,
                    CorriganActivity.this);
        }

        @Override
        public void onServiceDisconnected(ComponentName className) {
            Log.v(TAG, "onServiceDisconnected");
            registrar = null;
        }
    };

    // INTENTS
    public static final int LAUNCH_AUTH_INTENT = 0;
    public static final int LAUNCH_ACCOUNT_ACTIVITY = 1;

    @Override
    public void onRegistrationNotification(String accountName, String state, String substate) {
        Log.v(TAG, "onRegistrationNotification: accountName=" + accountName + ", state=" + state
                + ", substate=" + substate);

        // TODO: DEBUG: Remove later
        if (Registrar.REGISTRATION_STATE_REGISTERED.equals(state)) {
            List<String> recipients = new ArrayList<String>();
            recipients.add(accountName);
            registrar.sendMessage("Registration complete", recipients);
        }
    }

    @Override
    public void onLaunchIntent(Intent intent) {
        this.startActivityForResult(intent, LAUNCH_AUTH_INTENT);
    }

    @Override
    public void onMessage(Context context, Intent intent) {
        Log.d(TAG,
                "onMessage: from=" + intent.getStringExtra("from") + ", sender="
                        + intent.getStringExtra("sender") + ", message="
                        + intent.getStringExtra("message"));
        Toast.makeText(CorriganActivity.this, intent.getStringExtra("message"), Toast.LENGTH_SHORT)
                .show();
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        Log.i(TAG, "onCreate");
        super.onCreate(savedInstanceState);

        Intent intent = new Intent(this, Registrar.class);
        bindService(intent, mConnection,
                Context.BIND_AUTO_CREATE);

        setScreenContent(R.layout.activity_main);

        Button button = (Button)findViewById(R.id.say_hello);
        if (button != null) {
            button.setOnClickListener(new OnClickListener() {
				@Override
				public void onClick(View v) {
					registrar.publishDevice("hello from myself");
				}});
        }
    }

    @Override
    public void onResume() {
        super.onResume();

        if (registrar != null) {
            if (!registrar.isRegistered()) {
                final String accountName = registrar.getAccountName();
                if (accountName == null) {
                    Intent intent = new Intent(this, AccountsActivity.class);
                    startActivityForResult(intent, LAUNCH_ACCOUNT_ACTIVITY);
                } else {
                    registrar.reregister();
                }
            }
        }
    }

    /**
     * Shuts down the activity.
     */
    @Override
    public void onDestroy() {
        super.onDestroy();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent intent) {
        Log.d(TAG, "onActivityResult: requestCode=" + requestCode + ", resultCode=" + resultCode
                + ", intent=" + intent);
        if (requestCode == LAUNCH_ACCOUNT_ACTIVITY) {
            if (resultCode == RESULT_OK) {
                final String accountName = intent.getStringExtra("accountName");
                Log.d(TAG, "accountName=" + accountName);
                registrar.register(accountName);
            } else {
                finish();
            }
        }
        else if (requestCode == LAUNCH_AUTH_INTENT) {
            if (resultCode == RESULT_OK) {
                registrar.reregister();
            } else {
                Log.e(TAG, "Auth intent failed: requestCode=" + requestCode + ", resultCode="
                        + resultCode + ", intent=" + intent);
                finish();
            }
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        MenuInflater inflater = getMenuInflater();
        inflater.inflate(R.menu.main_menu, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        Log.v(TAG, "onOptionsItemSelected: item=" + item);

        final String title = item.getTitle().toString();
        Log.v(TAG, "onOptionsItemSelected: title=" + title);
        if (title.equals(getString(R.string.accounts))) {
            startActivityForResult(new Intent(this, AccountsActivity.class),
                    LAUNCH_ACCOUNT_ACTIVITY);
            return true;
        } else if (title.equals(getString(R.string.unregister))) {
            registrar.unregister();
            return true;
        } else if (title.equals(getString(R.string.reregister))) {
            registrar.reregister();
            return true;
        } else if (title.equals(getString(R.string.clear))) {
            registrar.clear();
            return true;
        } else {
            return super.onOptionsItemSelected(item);
        }
    }

    // Manage UI Screens

    private void setHelloWorldScreenContent() {
        setContentView(R.layout.activity_main);

        final Button sayHelloButton = (Button) findViewById(R.id.say_hello);
        sayHelloButton.setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View v) {
            }
        });
    }

    /**
     * Sets the screen content based on the screen id.
     */
    private void setScreenContent(int screenId) {
        setContentView(screenId);
        switch (screenId) {
            case R.layout.activity_main:
                setHelloWorldScreenContent();
                break;
        }
    }
}
