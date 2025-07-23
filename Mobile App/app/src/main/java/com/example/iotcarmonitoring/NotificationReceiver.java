package com.example.iotcarmonitoring;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class NotificationReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();

        if ("com.example.iotcarmonitoring.NOTIFICATION_ACTION".equals(action)) {
            // Handle notification actions
            String actionType = intent.getStringExtra("action_type");

            switch (actionType) {
                case "open_app":
                    openApp(context);
                    break;
                case "dismiss_alert":
                    dismissAlert(context, intent);
                    break;
                default:
                    // Default action - open app
                    openApp(context);
                    break;
            }
        }
    }

    private void openApp(Context context) {
        Intent launchIntent = new Intent(context, MainActivity.class);
        launchIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        context.startActivity(launchIntent);
    }

    private void dismissAlert(Context context, Intent intent) {
        // Handle alert dismissal logic here
        long alertId = intent.getLongExtra("alert_id", -1);
        if (alertId != -1) {
            // Mark alert as dismissed in database
            DatabaseHelper dbHelper = new DatabaseHelper(context);
            dbHelper.markAlertAsRead(alertId);
            dbHelper.close();
        }
    }
}