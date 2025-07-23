package com.example.iotcarmonitoring;

import android.content.Context;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class SimulationDataManager {

    private static final long UPDATE_INTERVAL = 2000; // 2 seconds for real-time simulation

    private Context context;
    private CarStatus currentStatus;
    private List<TripRecord> tripHistory;
    private Handler mainHandler;
    private Random random;
    private DatabaseHelper dbHelper;

    // Simulation state variables
    private boolean isRunning = false;
    private boolean isCarMoving = false;
    private long simulationStartTime;
    private float baseTemperature = 35.0f;
    private int baseBatteryLevel = 85;
    private long lastTripTime = 0;
    private int tripCounter = 0;

    // Simulation scenarios
    private SimulationScenario currentScenario = SimulationScenario.NORMAL;
    private long scenarioStartTime;

    public enum SimulationScenario {
        NORMAL,          // Normal operation
        LOW_BATTERY,     // Battery draining scenario
        OVERHEATING,     // Temperature rising scenario
        LONG_TRIP       // Extended driving scenario
    }

    public SimulationDataManager(Context context) {
        this.context = context;
        this.currentStatus = new CarStatus();
        this.tripHistory = new ArrayList<>();
        this.mainHandler = new Handler(Looper.getMainLooper());
        this.random = new Random();
        this.dbHelper = new DatabaseHelper(context);
        this.simulationStartTime = System.currentTimeMillis();

        initializeSimulationData();
        generateInitialTripHistory();
    }

    private void initializeSimulationData() {
        // Initialize with realistic starting values
        currentStatus.setBatteryLevel(baseBatteryLevel);
        currentStatus.setBatteryHealth("Good");
        currentStatus.setBatteryVoltage(12.4f);
        currentStatus.setMotorStatus("Stopped");
        currentStatus.setMotorSpeed(0);
        currentStatus.setMotorDirection("None");
        currentStatus.setSystemTemperature(baseTemperature);
        currentStatus.setAmbientTemperature(baseTemperature - 8);
        currentStatus.setConnected(true);
    }

    private void generateInitialTripHistory() {
        long currentTime = System.currentTimeMillis();

        // Generate 8 realistic trips from the past few days
        String[] startLocations = {"Home", "Garage", "Station A", "Point A", "Start Zone", "Base"};
        String[] endLocations = {"Work", "Mall", "Park", "School", "Station B", "Point B", "End Zone"};

        long lastTripEndTime = currentTime; // Start from current time and work backwards

        for (int i = 0; i < 8; i++) {
            // Generate realistic autonomous car parameters
            double distance = 0.05 + random.nextDouble() * 0.95; // 50m to 1000m (0.05-1.0 km)
            double avgSpeed = 1.5 + random.nextDouble() * 2.5; // 1.5-4.0 km/h (realistic for autonomous car)

            // Calculate duration based on distance and speed (Physics: time = distance / speed)
            long duration = Math.round(distance / avgSpeed * 3600); // Convert hours to seconds
            duration = Math.max(60, duration); // Minimum 1 minute trip

            // Trip end time (ensure no overlap with future trips)
            long tripEndTime = lastTripEndTime - (300000 + random.nextInt(1800000)); // 5-35 minutes gap between trips

            // Calculate trip start time
            long tripStartTime = tripEndTime - (duration * 1000); // Convert seconds to milliseconds

            // Calculate battery consumption (realistic for small autonomous car)
            int batteryUsed = 2 + (int)(distance * (8 + random.nextInt(5))) + (int)(duration / 600); // Extra 1% per 10 minutes
            batteryUsed = Math.max(1, Math.min(25, batteryUsed)); // Cap between 1-25%

            TripRecord trip = new TripRecord(tripEndTime, distance, duration, avgSpeed, batteryUsed);
            trip.setStartLocation(startLocations[random.nextInt(startLocations.length)]);
            trip.setEndLocation(endLocations[random.nextInt(endLocations.length)]);

            tripHistory.add(trip);

            // Update for next iteration (working backwards in time)
            lastTripEndTime = tripStartTime; // Next trip must end before this trip starts
        }

        // Sort by timestamp (newest first)
        tripHistory.sort((t1, t2) -> Long.compare(t2.getTimestamp(), t1.getTimestamp()));
    }

    public void startSimulation() {
        if (!isRunning) {
            isRunning = true;
            scheduleNextUpdate();
        }
    }

    public void stopSimulation() {
        isRunning = false;
        if (mainHandler != null) {
            mainHandler.removeCallbacksAndMessages(null);
        }
    }

    private void scheduleNextUpdate() {
        if (isRunning) {
            mainHandler.postDelayed(this::updateSimulationData, UPDATE_INTERVAL);
        }
    }

    private void updateSimulationData() {
        try {
            long currentTime = System.currentTimeMillis();
            long elapsedTime = currentTime - simulationStartTime;

            // Check if we should change scenarios
            checkScenarioChange(elapsedTime);

            // Update data based on current scenario
            updateBatterySimulation();
            updateMotorSimulation();
            updateTemperatureSimulation();

            // Occasionally add new trips
            maybeGenerateNewTrip(currentTime);

            // Check for alerts
            checkForSimulatedAlerts();

            // Broadcast update
            broadcastDataUpdate();

            // Schedule next update
            scheduleNextUpdate();

        } catch (Exception e) {
            e.printStackTrace();
            // Continue simulation even if there's an error
            scheduleNextUpdate();
        }
    }

    private void checkScenarioChange(long elapsedTime) {
        // Change scenario every 30-60 seconds
        if (elapsedTime - scenarioStartTime > 30000 + random.nextInt(30000)) {
            SimulationScenario[] scenarios = SimulationScenario.values();
            SimulationScenario newScenario = scenarios[random.nextInt(scenarios.length)];

            // Avoid repeating the same scenario immediately
            if (newScenario != currentScenario) {
                currentScenario = newScenario;
                scenarioStartTime = elapsedTime;

                // Log scenario change for debugging
                System.out.println("Simulation: Switching to " + currentScenario);
            }
        }
    }

    private void updateBatterySimulation() {
        int currentLevel = currentStatus.getBatteryLevel();
        float currentVoltage = currentStatus.getBatteryVoltage();

        switch (currentScenario) {
            case LOW_BATTERY:
                // Simulate faster battery drain
                if (currentLevel > 15) {
                    currentLevel = Math.max(15, currentLevel - (1 + random.nextInt(2)));
                    currentVoltage = Math.max(11.0f, currentVoltage - 0.05f);
                }
                currentStatus.setBatteryHealth(currentLevel < 20 ? "Poor" : "Fair");
                break;

            case LONG_TRIP:
                // Simulate steady drain during long trip
                if (isCarMoving && currentLevel > 10) {
                    currentLevel = Math.max(10, currentLevel - 1);
                    currentVoltage = Math.max(11.2f, currentVoltage - 0.02f);
                }
                break;

            default:
                // Normal battery behavior
                if (isCarMoving && currentLevel > 20) {
                    // Slow drain when moving
                    if (random.nextInt(5) == 0) { // 20% chance each update
                        currentLevel = Math.max(20, currentLevel - 1);
                        currentVoltage = Math.max(11.5f, currentVoltage - 0.01f);
                    }
                } else if (!isCarMoving && currentLevel < baseBatteryLevel) {
                    // Slight recovery when stopped (simulating charging)
                    if (random.nextInt(10) == 0) { // 10% chance each update
                        currentLevel = Math.min(baseBatteryLevel, currentLevel + 1);
                        currentVoltage = Math.min(12.4f, currentVoltage + 0.02f);
                    }
                }
                currentStatus.setBatteryHealth(currentLevel > 60 ? "Good" : currentLevel > 30 ? "Fair" : "Poor");
                break;
        }

        currentStatus.setBatteryLevel(currentLevel);
        currentStatus.setBatteryVoltage(currentVoltage);
    }

    private void updateMotorSimulation() {
        switch (currentScenario) {
            case LONG_TRIP:
                currentStatus.setMotorStatus("Running");
                currentStatus.setMotorSpeed(60 + random.nextInt(20)); // 60-80% speed
                currentStatus.setMotorDirection(getRandomDirection());
                isCarMoving = true;
                break;

            default:
                // Random start/stop behavior - only Running or Stopped
                if (random.nextInt(15) == 0) { // Reduced frequency: 6.7% chance to change state
                    if (isCarMoving) {
                        // Stop the car
                        currentStatus.setMotorStatus("Stopped");
                        currentStatus.setMotorSpeed(0);
                        currentStatus.setMotorDirection("None");
                        isCarMoving = false;
                    } else {
                        // Start the car
                        currentStatus.setMotorStatus("Running");
                        currentStatus.setMotorSpeed(30 + random.nextInt(40)); // 30-70% speed
                        currentStatus.setMotorDirection(getRandomDirection());
                        isCarMoving = true;
                    }
                }
                break;
        }
    }

    private void updateTemperatureSimulation() {
        float currentTemp = currentStatus.getSystemTemperature();

        switch (currentScenario) {
            case OVERHEATING:
                // Simulate overheating
                if (currentTemp < 75.0f) {
                    currentTemp = Math.min(75.0f, currentTemp + 1.0f + random.nextFloat());
                }
                break;

            case LONG_TRIP:
                // Higher temperature during long trips
                float longTripTargetTemp = baseTemperature + 15;
                if (currentTemp < longTripTargetTemp) {
                    currentTemp = Math.min(longTripTargetTemp, currentTemp + 0.5f);
                }
                break;

            default:
                // Normal temperature variation
                float normalTargetTemp = baseTemperature + (isCarMoving ? 10 : 0);
                if (Math.abs(currentTemp - normalTargetTemp) > 0.5f) {
                    if (currentTemp > normalTargetTemp) {
                        currentTemp = Math.max(normalTargetTemp, currentTemp - 0.3f);
                    } else {
                        currentTemp = Math.min(normalTargetTemp, currentTemp + 0.3f);
                    }
                }
                // Add small random variation
                currentTemp += (random.nextFloat() - 0.5f);
                break;
        }

        currentStatus.setSystemTemperature(currentTemp);
        currentStatus.setAmbientTemperature(currentTemp - 8 - random.nextFloat() * 2);
    }

    private void maybeGenerateNewTrip(long currentTime) {
        // Generate a new trip every 2-5 minutes during simulation
        if (currentTime - lastTripTime > (120000 + random.nextInt(180000))) {

            // Check if there's a recent trip that might still be running
            long earliestNewTripStart = currentTime;
            if (!tripHistory.isEmpty()) {
                TripRecord lastTrip = tripHistory.get(0); // Most recent trip
                long lastTripEndTime = lastTrip.getTimestamp();

                // Only generate new trip if enough time has passed since last trip ended
                if (currentTime - lastTripEndTime < 60000) { // Less than 1 minute since last trip ended
                    return; // Don't generate new trip yet
                }

                // New trip should start at least 1-5 minutes after last trip ended
                earliestNewTripStart = lastTripEndTime + 60000 + random.nextInt(240000);
            }

            // Trip end time (when this new trip will complete)
            long tripEndTime = Math.max(currentTime, earliestNewTripStart + 60000); // At least 1 minute from start

            // Generate realistic autonomous car parameters
            double distance = 0.03 + random.nextDouble() * 0.67; // 30m to 700m (0.03-0.7 km)
            double avgSpeed = 1.8 + random.nextDouble() * 2.2; // 1.8-4.0 km/h (realistic for lane detection car)

            // Calculate duration based on physics: time = distance / speed
            long duration = Math.round(distance / avgSpeed * 3600); // Convert hours to seconds
            duration = Math.max(45, duration); // Minimum 45 seconds trip

            // Calculate trip start time
            long tripStartTime = tripEndTime - (duration * 1000); // Convert to milliseconds

            // Ensure trip start time is logical (not in the future from current time)
            if (tripStartTime > currentTime) {
                tripStartTime = currentTime - duration * 1000;
                tripEndTime = currentTime;
            }

            // Realistic battery consumption for autonomous car
            int batteryUsed = 1 + (int)(distance * (10 + random.nextInt(6))) + (int)(duration / 300);
            batteryUsed = Math.max(1, Math.min(20, batteryUsed)); // Cap between 1-20%

            TripRecord newTrip = new TripRecord(tripEndTime, distance, duration, avgSpeed, batteryUsed);

            // Set realistic locations
            String[] starts = {"Parking", "Home", "Station", "Point A", "Zone 1"};
            String[] ends = {"Destination", "Target", "Point B", "Zone 2", "Finish"};
            newTrip.setStartLocation(starts[random.nextInt(starts.length)]);
            newTrip.setEndLocation(ends[random.nextInt(ends.length)]);

            tripHistory.add(0, newTrip); // Add to beginning

            // Keep only last 10 trips
            if (tripHistory.size() > 10) {
                tripHistory.remove(tripHistory.size() - 1);
            }

            lastTripTime = currentTime;
            tripCounter++;
        }
    }

    private void checkForSimulatedAlerts() {
        // Low battery alert
        if (currentStatus.getBatteryLevel() <= 20) {
            sendAlert("Low Battery",
                    "Battery level is " + currentStatus.getBatteryLevel() + "%");
        }

        // High temperature alert
        if (currentStatus.getSystemTemperature() >= 65.0f) {
            sendAlert("High Temperature",
                    String.format("System temperature is %.1f°C", currentStatus.getSystemTemperature()));
        }

        // Battery health alert
        if ("Poor".equals(currentStatus.getBatteryHealth())) {
            sendAlert("Battery Health", "Battery health is degrading");
        }
    }

    private String getRandomDirection() {
        String[] directions = {"Forward", "Left", "Right", "Backward"};
        return directions[random.nextInt(directions.length)];
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

    // Public methods for accessing simulated data
    public CarStatus getCurrentStatus() {
        return currentStatus;
    }

    public List<TripRecord> getTripHistory() {
        return new ArrayList<>(tripHistory);
    }

    public void forceScenario(SimulationScenario scenario) {
        this.currentScenario = scenario;
        this.scenarioStartTime = System.currentTimeMillis() - simulationStartTime;
    }

    public SimulationScenario getCurrentScenario() {
        return currentScenario;
    }

    public void cleanup() {
        stopSimulation();
        if (dbHelper != null) {
            dbHelper.close();
        }
    }
}