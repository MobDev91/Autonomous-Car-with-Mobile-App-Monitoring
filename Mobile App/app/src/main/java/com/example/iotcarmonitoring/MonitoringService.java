package com.example.iotcarmonitoring;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import androidx.core.app.NotificationCompat;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

public class MonitoringService extends Service {

    private static final String CHANNEL_ID = "monitoring_service_channel";
    private static final int NOTIFICATION_ID = 1001;
    private static final long UPDATE_INTERVAL = 30000; // 30 seconds for background monitoring

    private CarDataManager dataManager;
    private Handler handler;
    private Runnable monitoringRunnable;
    private boolean isMonitoring = false;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        dataManager = new CarDataManager(this);
        handler = new Handler(Looper.getMainLooper());
        setupMonitoringRunnable();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startForeground(NOTIFICATION_ID, createNotification());
        startMonitoring();
        return START_STICKY; // Service will be restarted if killed
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null; // This is a started service
    }

    @Override
    public void onDestroy() {
        stopMonitoring();
        if (dataManager != null) {
            dataManager.cleanup();
        }
        super.onDestroy();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "IoT Car Monitoring Service",
                    NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Background monitoring of IoT car status");
            channel.setShowBadge(false);

            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(channel);
        }
    }

    private Notification createNotification() {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this, 0, notificationIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        return new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("IoT Car Monitor")
                .setContentText("Monitoring vehicle status...")
                .setSmallIcon(R.drawable.ic_car_notification)
                .setContentIntent(pendingIntent)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();
    }

    private void setupMonitoringRunnable() {
        monitoringRunnable = new Runnable() {
            @Override
            public void run() {
                if (isMonitoring) {
                    performBackgroundMonitoring();
                    handler.postDelayed(this, UPDATE_INTERVAL);
                }
            }
        };
    }

    private void startMonitoring() {
        if (!isMonitoring) {
            isMonitoring = true;
            handler.post(monitoringRunnable);
        }
    }

    private void stopMonitoring() {
        isMonitoring = false;
        if (handler != null && monitoringRunnable != null) {
            handler.removeCallbacks(monitoringRunnable);
        }
    }

    private void performBackgroundMonitoring() {
        // Perform lightweight monitoring in background
        new Thread(() -> {
            try {
                // Check critical status only
                CarStatus status = dataManager.getCurrentStatus();

                // Check for critical alerts
                checkCriticalAlerts(status);

                // Update notification with current status
                updateNotification(status);

                // Broadcast status update
                Intent intent = new Intent("BACKGROUND_STATUS_UPDATE");
                intent.putExtra("battery_level", status.getBatteryLevel());
                intent.putExtra("motor_status", status.getMotorStatus());
                intent.putExtra("temperature", status.getSystemTemperature());
                LocalBroadcastManager.getInstance(this).sendBroadcast(intent);

            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }

    private void checkCriticalAlerts(CarStatus status) {
        // Only check for critical alerts in background to save battery

        // Critical battery level (below 10%)
        if (status.getBatteryLevel() <= 10 && status.getBatteryLevel() > 0) {
            sendCriticalAlert("Critical Battery",
                    "Battery level critically low: " + status.getBatteryLevel() + "%");
        }

        // Critical temperature (above 70°C)
        if (status.getSystemTemperature() >= 70.0f) {
            sendCriticalAlert("Critical Temperature",
                    String.format("System overheating: %.1f°C", status.getSystemTemperature()));
        }

        // Motor error
        if ("Error".equals(status.getMotorStatus())) {
            sendCriticalAlert("Motor Error", "Critical motor system failure detected");
        }
    }

    private void sendCriticalAlert(String title, String message) {
        Intent intent = new Intent("CRITICAL_ALERT");
        intent.putExtra("title", title);
        intent.putExtra("message", message);
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent);

        // Also show high-priority notification
        showCriticalNotification(title, message);
    }

    private void showCriticalNotification(String title, String message) {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this, 0, notificationIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification alertNotification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle(title)
                .setContentText(message)
                .setSmallIcon(R.drawable.ic_warning)
                .setContentIntent(pendingIntent)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setDefaults(NotificationCompat.DEFAULT_ALL)
                .build();

        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        manager.notify((int) System.currentTimeMillis(), alertNotification);
    }

    private void updateNotification(CarStatus status) {
        String statusText = String.format("Battery: %d%% | Temp: %.1f°C | Motor: %s",
                status.getBatteryLevel(),
                status.getSystemTemperature(),
                status.getMotorStatus());

        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this, 0, notificationIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification updatedNotification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("IoT Car Monitor")
                .setContentText(statusText)
                .setSmallIcon(R.drawable.ic_car_notification)
                .setContentIntent(pendingIntent)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();

        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        manager.notify(NOTIFICATION_ID, updatedNotification);
    }
}