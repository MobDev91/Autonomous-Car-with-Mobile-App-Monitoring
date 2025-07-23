package com.example.iotcarmonitoring;

public class CarStatus {

    // Battery information
    private int batteryLevel;
    private String batteryHealth;
    private float batteryVoltage;

    // Motor information
    private String motorStatus;
    private int motorSpeed;
    private String motorDirection;

    // Temperature information
    private float systemTemperature;
    private float ambientTemperature;

    // System information
    private long lastUpdateTime;
    private boolean isConnected;

    public CarStatus() {
        // Initialize with default values
        this.batteryLevel = 0;
        this.batteryHealth = "Unknown";
        this.batteryVoltage = 0.0f;
        this.motorStatus = "Stopped";
        this.motorSpeed = 0;
        this.motorDirection = "None";
        this.systemTemperature = 0.0f;
        this.ambientTemperature = 0.0f;
        this.lastUpdateTime = System.currentTimeMillis();
        this.isConnected = false;
    }

    // Battery getters and setters
    public int getBatteryLevel() {
        return batteryLevel;
    }

    public void setBatteryLevel(int batteryLevel) {
        this.batteryLevel = Math.max(0, Math.min(100, batteryLevel)); // Clamp between 0-100
        updateTimestamp();
    }

    public String getBatteryHealth() {
        return batteryHealth;
    }

    public void setBatteryHealth(String batteryHealth) {
        this.batteryHealth = batteryHealth != null ? batteryHealth : "Unknown";
        updateTimestamp();
    }

    public float getBatteryVoltage() {
        return batteryVoltage;
    }

    public void setBatteryVoltage(float batteryVoltage) {
        this.batteryVoltage = Math.max(0, batteryVoltage);
        updateTimestamp();
    }

    // Motor getters and setters
    public String getMotorStatus() {
        return motorStatus;
    }

    public void setMotorStatus(String motorStatus) {
        this.motorStatus = motorStatus != null ? motorStatus : "Unknown";
        updateTimestamp();
    }

    public int getMotorSpeed() {
        return motorSpeed;
    }

    public void setMotorSpeed(int motorSpeed) {
        this.motorSpeed = Math.max(0, Math.min(100, motorSpeed)); // Clamp between 0-100
        updateTimestamp();
    }

    public String getMotorDirection() {
        return motorDirection;
    }

    public void setMotorDirection(String motorDirection) {
        this.motorDirection = motorDirection != null ? motorDirection : "None";
        updateTimestamp();
    }

    // Temperature getters and setters
    public float getSystemTemperature() {
        return systemTemperature;
    }

    public void setSystemTemperature(float systemTemperature) {
        this.systemTemperature = systemTemperature;
        updateTimestamp();
    }

    public float getAmbientTemperature() {
        return ambientTemperature;
    }

    public void setAmbientTemperature(float ambientTemperature) {
        this.ambientTemperature = ambientTemperature;
        updateTimestamp();
    }

    // System getters and setters
    public long getLastUpdateTime() {
        return lastUpdateTime;
    }

    public boolean isConnected() {
        return isConnected;
    }

    public void setConnected(boolean connected) {
        this.isConnected = connected;
        updateTimestamp();
    }

    private void updateTimestamp() {
        this.lastUpdateTime = System.currentTimeMillis();
    }

    // Utility methods
    public boolean isBatteryLow() {
        return batteryLevel <= 20;
    }

    public boolean isBatteryCritical() {
        return batteryLevel <= 10;
    }

    public boolean isTemperatureHigh() {
        return systemTemperature >= 60.0f;
    }

    public boolean isTemperatureCritical() {
        return systemTemperature >= 70.0f;
    }

    public boolean isMotorRunning() {
        return "Running".equalsIgnoreCase(motorStatus);
    }

    public boolean hasMotorError() {
        return "Error".equalsIgnoreCase(motorStatus);
    }

    public String getBatteryHealthStatus() {
        switch (batteryHealth.toLowerCase()) {
            case "excellent":
                return "🟢 Excellent";
            case "good":
                return "🟢 Good";
            case "fair":
                return "🟡 Fair";
            case "poor":
                return "🔴 Poor";
            default:
                return "❓ Unknown";
        }
    }

    public String getMotorStatusDisplay() {
        switch (motorStatus.toLowerCase()) {
            case "running":
                return "🟢 Running";
            case "stopped":
                return "🟡 Stopped";
            case "error":
                return "🔴 Error";
            case "maintenance":
                return "🟠 Maintenance";
            default:
                return "❓ Unknown";
        }
    }

    public String getTemperatureStatus() {
        if (systemTemperature >= 70.0f) {
            return "🔴 Critical";
        } else if (systemTemperature >= 60.0f) {
            return "🟠 High";
        } else if (systemTemperature >= 40.0f) {
            return "🟡 Warm";
        } else {
            return "🟢 Normal";
        }
    }

    @Override
    public String toString() {
        return "CarStatus{" +
                "batteryLevel=" + batteryLevel +
                ", batteryHealth='" + batteryHealth + '\'' +
                ", batteryVoltage=" + batteryVoltage +
                ", motorStatus='" + motorStatus + '\'' +
                ", motorSpeed=" + motorSpeed +
                ", motorDirection='" + motorDirection + '\'' +
                ", systemTemperature=" + systemTemperature +
                ", ambientTemperature=" + ambientTemperature +
                ", lastUpdateTime=" + lastUpdateTime +
                ", isConnected=" + isConnected +
                '}';
    }
}