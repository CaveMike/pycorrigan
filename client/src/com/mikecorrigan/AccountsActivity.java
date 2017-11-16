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

import java.util.List;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;

import com.mikecorrigan.android.c2dm.Registrar;

public class AccountsActivity extends Activity {
    private static final String TAG = AccountsActivity.class.getSimpleName();

    private final Context mContext = this;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.connect);
        setConnectScreenContent();
    }

    private void setConnectScreenContent() {
        List<String> accounts = Registrar.getAccounts(mContext);

        if (accounts.size() == 0) {
            // Show a dialog and invoke the "Add Account" activity if requested
            AlertDialog.Builder builder = new AlertDialog.Builder(mContext);
            builder.setMessage(R.string.needs_account);
            builder.setPositiveButton(R.string.add_account, new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    startActivity(new Intent(Settings.ACTION_ADD_ACCOUNT)); // TODO:
                                                                            // Get
                                                                            // activity
                                                                            // result?
                }
            });
            builder.setNegativeButton(R.string.skip, new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    setResult(RESULT_CANCELED);
                    finish();
                }
            });
            builder.setIcon(android.R.drawable.stat_sys_warning);
            builder.setTitle(R.string.attention);
            builder.show();
        } else {
            final ListView listView = (ListView) findViewById(R.id.select_account);
            listView.setAdapter(new ArrayAdapter<String>(mContext, R.layout.account, accounts));
            listView.setChoiceMode(ListView.CHOICE_MODE_SINGLE);
            listView.setItemChecked(0, true);

            final Button connectButton = (Button) findViewById(R.id.connect);
            connectButton.setOnClickListener(new OnClickListener() {
                @Override
                public void onClick(View v) {
                    int pos = listView.getCheckedItemPosition();
                    TextView account = (TextView) listView.getChildAt(pos);

                    Log.d(TAG, "accountName=" + account.getText());

                    Intent resultIntent = new Intent();
                    resultIntent.putExtra("accountName", (String) account.getText());
                    setResult(Activity.RESULT_OK, resultIntent);
                    finish();
                }
            });
        }
    }
}
