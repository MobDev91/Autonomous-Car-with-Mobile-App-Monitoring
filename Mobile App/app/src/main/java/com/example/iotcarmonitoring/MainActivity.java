package com.example.iotcarmonitoring;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;
import androidx.core.app.NotificationCompat;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private static final String CHANNEL_ID = "iot_car_notifications";

    // UI Components
    private TextView batteryPercentage;
    private ProgressBar batteryProgressBar;
    private ImageView batteryIcon;
    private TextView batteryHealthText;

    private TextView motorStatusText;
    private ImageView motorStatusIcon;

    private TextView temperatureText;
    private ImageView temperatureIcon;

    private RecyclerView tripHistoryRecyclerView;
    private TripHistoryAdapter tripAdapter;

    private CardView refreshButton;

    // Data components
    private CarDataManager dataManager;
    private List<TripRecord> tripHistory;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initializeUI();
        setupNotificationChannel();
        setupDataManager();
        setupTripHistory();
        setupBroadcastReceiver();

        // Initial data load
        refreshData();
    }

    private void initializeUI() {
        // Battery components
        batteryPercentage = findViewById(R.id.battery_percentage);
        batteryProgressBar = findViewById(R.id.battery_progress);
        batteryIcon = findViewById(R.id.battery_icon);
        batteryHealthText = findViewById(R.id.battery_health);

        // Motor components
        motorStatusText = findViewById(R.id.motor_status_text);
        motorStatusIcon = findViewById(R.id.motor_status_icon);

        // Temperature components
        temperatureText = findViewById(R.id.temperature_text);
        temperatureIcon = findViewById(R.id.temperature_icon);

        // Trip history
        tripHistoryRecyclerView = findViewById(R.id.trip_history_recycler);

        // Refresh button
        refreshButton = findViewById(R.id.refresh_button);
        refreshButton.setOnClickListener(v -> refreshData());
    }

    private void setupNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            CharSequence name = "IoT Car Monitoring";
            String description = "Notifications for car status alerts";
            int importance = NotificationManager.IMPORTANCE_HIGH;
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, name, importance);
            channel.setDescription(description);

            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            notificationManager.createNotificationChannel(channel);
        }
    }

    private void setupDataManager() {
        dataManager = new CarDataManager(this);
    }

    private void setupTripHistory() {
        tripHistory = new ArrayList<>();
        tripAdapter = new TripHistoryAdapter(tripHistory);
        tripHistoryRecyclerView.setLayoutManager(new LinearLayoutManager(this));
        tripHistoryRecyclerView.setAdapter(tripAdapter);
    }

    private void setupBroadcastReceiver() {
        BroadcastReceiver dataReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                String action = intent.getAction();
                if ("CAR_DATA_UPDATE".equals(action)) {
                    updateUI();
                } else if ("CAR_ALERT".equals(action)) {
                    String alertType = intent.getStringExtra("alert_type");
                    String message = intent.getStringExtra("message");
                    showNotification(alertType, message);
                }
            }
        };

        IntentFilter filter = new IntentFilter();
        filter.addAction("CAR_DATA_UPDATE");
        filter.addAction("CAR_ALERT");
        LocalBroadcastManager.getInstance(this).registerReceiver(dataReceiver, filter);
    }

    private void refreshData() {
        dataManager.refreshData();
        updateUI();
        loadTripHistory();
    }

    private void updateUI() {
        CarStatus status = dataManager.getCurrentStatus();

        // Update battery info
        updateBatteryDisplay(status.getBatteryLevel(), status.getBatteryHealth());

        // Update motor status
        updateMotorDisplay(status.getMotorStatus());

        // Update temperature
        updateTemperatureDisplay(status.getSystemTemperature());
    }

    private void updateBatteryDisplay(int batteryLevel, String batteryHealth) {
        batteryPercentage.setText(batteryLevel + "%");
        batteryProgressBar.setProgress(batteryLevel);
        batteryHealthText.setText("Health: " + batteryHealth);

        // Update battery icon based on level
        if (batteryLevel > 75) {
            batteryIcon.setImageResource(R.drawable.ic_battery_full);
            batteryIcon.setColorFilter(getResources().getColor(R.color.battery_good));
        } else if (batteryLevel > 25) {
            batteryIcon.setImageResource(R.drawable.ic_battery_half);
            batteryIcon.setColorFilter(getResources().getColor(R.color.battery_medium));
        } else {
            batteryIcon.setImageResource(R.drawable.ic_battery_low);
            batteryIcon.setColorFilter(getResources().getColor(R.color.battery_low));
        }
    }

    private void updateMotorDisplay(String motorStatus) {
        motorStatusText.setText(motorStatus);

        if ("Running".equals(motorStatus)) {
            motorStatusIcon.setImageResource(R.drawable.ic_motor_running);
            motorStatusIcon.setColorFilter(getResources().getColor(R.color.status_good));
        } else if ("Stopped".equals(motorStatus)) {
            motorStatusIcon.setImageResource(R.drawable.ic_motor_stopped);
            motorStatusIcon.setColorFilter(getResources().getColor(R.color.status_neutral));
        } else {
            motorStatusIcon.setImageResource(R.drawable.ic_motor_error);
            motorStatusIcon.setColorFilter(getResources().getColor(R.color.status_error));
        }
    }

    private void updateTemperatureDisplay(float temperature) {
        temperatureText.setText(String.format("%.1f°C", temperature));

        if (temperature > 60) {
            temperatureIcon.setColorFilter(getResources().getColor(R.color.temp_hot));
        } else if (temperature > 40) {
            temperatureIcon.setColorFilter(getResources().getColor(R.color.temp_warm));
        } else {
            temperatureIcon.setColorFilter(getResources().getColor(R.color.temp_normal));
        }
    }

    private void loadTripHistory() {
        List<TripRecord> trips = dataManager.getTripHistory();
        tripHistory.clear();
        tripHistory.addAll(trips);
        tripAdapter.notifyDataSetChanged();
    }

    private void showNotification(String alertType, String message) {
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_car_notification)
                .setContentTitle("IoT Car Alert: " + alertType)
                .setContentText(message)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true);

        NotificationManager notificationManager =
                (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        notificationManager.notify((int) System.currentTimeMillis(), builder.build());

        // Also show toast for immediate feedback
        Toast.makeText(this, alertType + ": " + message, Toast.LENGTH_LONG).show();
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshData();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (dataManager != null) {
            dataManager.cleanup();
        }
    }
}