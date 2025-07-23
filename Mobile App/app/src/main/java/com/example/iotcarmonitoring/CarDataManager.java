package com.example.iotcarmonitoring;

import android.content.Context;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.json.JSONArray;
import org.json.JSONObject;

public class CarDataManager {

    private static final String RASPBERRY_PI_BASE_URL = "http://192.168.1.100:8080"; // Replace with your Pi's IP
    private static final long UPDATE_INTERVAL = 5000; // 5 seconds
    private static final boolean SIMULATION_MODE = true; // Set to false for real Pi connection

    private Context context;
    private CarStatus currentStatus;
    private List<TripRecord> tripHistory;
    private ExecutorService executor;
    private Handler mainHandler;
    private DatabaseHelper dbHelper;

    // Simulation components
    private SimulationDataManager simulationManager;

    // Alert thresholds
    private static final int LOW_BATTERY_THRESHOLD = 20;
    private static final float HIGH_TEMP_THRESHOLD = 65.0f;

    public CarDataManager(Context context) {
        this.context = context;
        this.currentStatus = new CarStatus();
        this.tripHistory = new ArrayList<>();
        this.executor = Executors.newFixedThreadPool(2);
        this.mainHandler = new Handler(Looper.getMainLooper());
        this.dbHelper = new DatabaseHelper(context);

        if (SIMULATION_MODE) {
            setupSimulation();
        } else {
            startPeriodicUpdates();
        }
    }

    private void setupSimulation() {
        simulationManager = new SimulationDataManager(context);
        simulationManager.startSimulation();
    }

    public void refreshData() {
        if (SIMULATION_MODE) {
            // Get data from simulation
            currentStatus = simulationManager.getCurrentStatus();
            tripHistory = simulationManager.getTripHistory();

            mainHandler.post(() -> {
                broadcastDataUpdate();
                // Note: Alerts are handled by SimulationDataManager
            });
        } else {
            // Real Pi communication
            executor.execute(() -> {
                fetchBatteryStatus();
                fetchMotorStatus();
                fetchSystemTemperature();
                fetchTripHistory();

                mainHandler.post(() -> {
                    broadcastDataUpdate();
                    checkForAlerts();
                });
            });
        }
    }

    private void startPeriodicUpdates() {
        mainHandler.post(new Runnable() {
            @Override
            public void run() {
                refreshData();
                mainHandler.postDelayed(this, UPDATE_INTERVAL);
            }
        });
    }

    private void fetchBatteryStatus() {
        try {
            String response = makeHttpRequest("/api/battery");
            if (response != null) {
                JSONObject json = new JSONObject(response);
                int level = json.getInt("level");
                String health = json.getString("health");
                float voltage = (float) json.getDouble("voltage");

                currentStatus.setBatteryLevel(level);
                currentStatus.setBatteryHealth(health);
                currentStatus.setBatteryVoltage(voltage);

                // Store battery data in local database
                dbHelper.insertBatteryReading(level, voltage, health);
            }
        } catch (Exception e) {
            // Fallback to simulation data for testing
            simulateBatteryData();
        }
    }

    private void fetchMotorStatus() {
        try {
            String response = makeHttpRequest("/api/motor");
            if (response != null) {
                JSONObject json = new JSONObject(response);
                String status = json.getString("status");
                int speed = json.getInt("speed");
                String direction = json.getString("direction");

                currentStatus.setMotorStatus(status);
                currentStatus.setMotorSpeed(speed);
                currentStatus.setMotorDirection(direction);
            }
        } catch (Exception e) {
            // Fallback to simulation data for testing
            simulateMotorData();
        }
    }

    private void fetchSystemTemperature() {
        try {
            String response = makeHttpRequest("/api/temperature");
            if (response != null) {
                JSONObject json = new JSONObject(response);
                float cpuTemp = (float) json.getDouble("cpu_temperature");
                float ambientTemp = (float) json.getDouble("ambient_temperature");

                currentStatus.setSystemTemperature(cpuTemp);
                currentStatus.setAmbientTemperature(ambientTemp);

                // Store temperature data
                dbHelper.insertTemperatureReading(cpuTemp, ambientTemp);
            }
        } catch (Exception e) {
            // Fallback to simulation data for testing
            simulateTemperatureData();
        }
    }

    private void fetchTripHistory() {
        try {
            String response = makeHttpRequest("/api/trips");
            if (response != null) {
                JSONArray jsonArray = new JSONArray(response);
                tripHistory.clear();

                for (int i = 0; i < jsonArray.length(); i++) {
                    JSONObject trip = jsonArray.getJSONObject(i);
                    TripRecord record = new TripRecord(
                            trip.getLong("timestamp"),
                            trip.getDouble("distance"),
                            trip.getLong("duration"),
                            trip.getDouble("avg_speed"),
                            trip.getInt("battery_consumed")
                    );
                    tripHistory.add(record);
                }
            }
        } catch (Exception e) {
            // Load from local database or simulate
            loadLocalTripHistory();
        }
    }

    private String makeHttpRequest(String endpoint) {
        try {
            URL url = new URL(RASPBERRY_PI_BASE_URL + endpoint);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(3000);
            connection.setReadTimeout(3000);

            int responseCode = connection.getResponseCode();
            if (responseCode == HttpURLConnection.HTTP_OK) {
                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(connection.getInputStream()));
                StringBuilder response = new StringBuilder();
                String line;

                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();
                return response.toString();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    private void checkForAlerts() {
        // Check battery level
        if (currentStatus.getBatteryLevel() <= LOW_BATTERY_THRESHOLD) {
            sendAlert("Low Battery",
                    "Battery level is " + currentStatus.getBatteryLevel() + "%");
        }

        // Check temperature
        if (currentStatus.getSystemTemperature() >= HIGH_TEMP_THRESHOLD) {
            sendAlert("High Temperature",
                    String.format("System temperature is %.1f°C", currentStatus.getSystemTemperature()));
        }

        // Check battery health
        if ("Poor".equals(currentStatus.getBatteryHealth())) {
            sendAlert("Battery Health", "Battery health is degrading");
        }
    }

    private void sendAlert(String alertType, String message) {
        Intent intent = new Intent("CAR_ALERT");
        intent.putExtra("alert_type", alertType);
        intent.putExtra("message", message);
        LocalBroadcastManager.getInstance(context).sendBroadcast(intent);

        // Store alert in database
        dbHelper.insertAlert(alertType, message);
    }

    private void broadcastDataUpdate() {
        Intent intent = new Intent("CAR_DATA_UPDATE");
        LocalBroadcastManager.getInstance(context).sendBroadcast(intent);
    }

    // Simulation methods for testing without Raspberry Pi
    private void simulateBatteryData() {
        int level = 45 + (int)(Math.random() * 40); // 45-85%
        currentStatus.setBatteryLevel(level);
        currentStatus.setBatteryHealth("Good");
        currentStatus.setBatteryVoltage(3.7f + (float)(Math.random() * 0.5));
    }

    private void simulateMotorData() {
        String[] statuses = {"Running", "Stopped"}; // Removed "Error"
        String status = statuses[(int)(Math.random() * statuses.length)];
        currentStatus.setMotorStatus(status);
        currentStatus.setMotorSpeed("Running".equals(status) ? 50 + (int)(Math.random() * 50) : 0);
        currentStatus.setMotorDirection("Running".equals(status) ? "Forward" : "None");
    }

    private void simulateTemperatureData() {
        float temp = 35.0f + (float)(Math.random() * 20); // 35-55°C
        currentStatus.setSystemTemperature(temp);
        currentStatus.setAmbientTemperature(temp - 10);
    }

    private void loadLocalTripHistory() {
        // Load from database or create sample data with logical calculations
        if (tripHistory.isEmpty()) {
            long currentTime = System.currentTimeMillis();

            // Create realistic trips with proper timing (working backwards from current time)

            // Trip 1: Most recent (ended 30 minutes ago)
            double distance1 = 0.4; // 400m
            double speed1 = 2.5; // 2.5 km/h
            long duration1 = Math.round(distance1 / speed1 * 3600); // 576 seconds = 9.6 minutes
            int battery1 = 2 + (int)(distance1 * 12); // 7%
            long endTime1 = currentTime - 1800000; // 30 minutes ago
            tripHistory.add(new TripRecord(endTime1, distance1, duration1, speed1, battery1));

            // Trip 2: Ended 45 minutes ago (15 minutes gap after trip 1 ended)
            double distance2 = 0.25; // 250m
            double speed2 = 3.0; // 3.0 km/h
            long duration2 = Math.round(distance2 / speed2 * 3600); // 300 seconds = 5 minutes
            int battery2 = 2 + (int)(distance2 * 10); // 4%
            long endTime2 = currentTime - 2700000; // 45 minutes ago
            tripHistory.add(new TripRecord(endTime2, distance2, duration2, speed2, battery2));

            // Trip 3: Ended 1.5 hours ago (30 minutes gap after trip 2 ended)
            double distance3 = 0.6; // 600m
            double speed3 = 2.0; // 2.0 km/h
            long duration3 = Math.round(distance3 / speed3 * 3600); // 1080 seconds = 18 minutes
            int battery3 = 3 + (int)(distance3 * 11); // 10%
            long endTime3 = currentTime - 5400000; // 1.5 hours ago
            tripHistory.add(new TripRecord(endTime3, distance3, duration3, speed3, battery3));

            // Trip 4: Ended 2.5 hours ago (1 hour gap after trip 3 ended)
            double distance4 = 0.15; // 150m
            double speed4 = 1.8; // 1.8 km/h
            long duration4 = Math.round(distance4 / speed4 * 3600); // 300 seconds = 5 minutes
            int battery4 = 1 + (int)(distance4 * 13); // 3%
            long endTime4 = currentTime - 9000000; // 2.5 hours ago
            tripHistory.add(new TripRecord(endTime4, distance4, duration4, speed4, battery4));
        }
    }

    public CarStatus getCurrentStatus() {
        if (SIMULATION_MODE && simulationManager != null) {
            return simulationManager.getCurrentStatus();
        }
        return currentStatus;
    }

    public List<TripRecord> getTripHistory() {
        if (SIMULATION_MODE && simulationManager != null) {
            return simulationManager.getTripHistory();
        }
        return new ArrayList<>(tripHistory);
    }

    // Methods to control simulation
    public void setSimulationMode(boolean enabled) {
        // Note: This method is for future use when we want to toggle between modes
        // For now, SIMULATION_MODE is a constant
    }

    public void forceSimulationScenario(String scenarioName) {
        if (SIMULATION_MODE && simulationManager != null) {
            try {
                SimulationDataManager.SimulationScenario scenario =
                        SimulationDataManager.SimulationScenario.valueOf(scenarioName.toUpperCase());
                simulationManager.forceScenario(scenario);
            } catch (IllegalArgumentException e) {
                // Invalid scenario name, ignore
            }
        }
    }

    public boolean isInSimulationMode() {
        return SIMULATION_MODE;
    }

    public void cleanup() {
        if (executor != null && !executor.isShutdown()) {
            executor.shutdown();
        }
        if (simulationManager != null) {
            simulationManager.cleanup();
        }
        if (dbHelper != null) {
            dbHelper.close();
        }
    }
}