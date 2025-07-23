package com.example.iotcarmonitoring;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

public class NetworkChangeReceiver extends BroadcastReceiver {

    private static boolean wasConnected = false;

    @Override
    public void onReceive(Context context, Intent intent) {
        if (isNetworkConnected(context)) {
            if (!wasConnected) {
                // Network restored
                broadcastNetworkChange(context, true, "Network connection restored");
                wasConnected = true;
            }
        } else {
            if (wasConnected) {
                // Network lost
                broadcastNetworkChange(context, false, "Network connection lost");
                wasConnected = false;
            }
        }
    }

    private boolean isNetworkConnected(Context context) {
        ConnectivityManager connectivityManager =
                (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);

        if (connectivityManager != null) {
            NetworkInfo activeNetwork = connectivityManager.getActiveNetworkInfo();
            return activeNetwork != null && activeNetwork.isConnectedOrConnecting();
        }
        return false;
    }

    private void broadcastNetworkChange(Context context, boolean isConnected, String message) {
        Intent intent = new Intent("NETWORK_STATUS_CHANGE");
        intent.putExtra("is_connected", isConnected);
        intent.putExtra("message", message);
        LocalBroadcastManager.getInstance(context).sendBroadcast(intent);
    }
}