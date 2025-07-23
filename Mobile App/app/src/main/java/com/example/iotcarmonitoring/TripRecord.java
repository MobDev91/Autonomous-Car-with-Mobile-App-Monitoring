package com.example.iotcarmonitoring;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class TripRecord {

    private long id;
    private long timestamp;
    private double distance; // in kilometers
    private long duration; // in seconds
    private double averageSpeed; // in km/h
    private int batteryConsumed; // percentage consumed
    private String startLocation;
    private String endLocation;

    // Constructor for basic trip record
    public TripRecord(long endTimestamp, double distance, long duration, double averageSpeed, int batteryConsumed) {
        this.timestamp = endTimestamp; // This represents trip END time
        this.distance = distance;
        this.duration = duration;
        this.averageSpeed = averageSpeed;
        this.batteryConsumed = batteryConsumed;
        this.startLocation = "Unknown";
        this.endLocation = "Unknown";
    }

    // Full constructor
    public TripRecord(long id, long timestamp, double distance, long duration,
                      double averageSpeed, int batteryConsumed, String startLocation, String endLocation) {
        this.id = id;
        this.timestamp = timestamp;
        this.distance = distance;
        this.duration = duration;
        this.averageSpeed = averageSpeed;
        this.batteryConsumed = batteryConsumed;
        this.startLocation = startLocation != null ? startLocation : "Unknown";
        this.endLocation = endLocation != null ? endLocation : "Unknown";
    }

    // Getters
    public long getId() {
        return id;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public double getDistance() {
        return distance;
    }

    public long getDuration() {
        return duration;
    }

    public double getAverageSpeed() {
        return averageSpeed;
    }

    public int getBatteryConsumed() {
        return batteryConsumed;
    }

    public String getStartLocation() {
        return startLocation;
    }

    public String getEndLocation() {
        return endLocation;
    }

    // Setters
    public void setId(long id) {
        this.id = id;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    public void setDistance(double distance) {
        this.distance = Math.max(0, distance);
    }

    public void setDuration(long duration) {
        this.duration = Math.max(0, duration);
    }

    public void setAverageSpeed(double averageSpeed) {
        this.averageSpeed = Math.max(0, averageSpeed);
    }

    public void setBatteryConsumed(int batteryConsumed) {
        this.batteryConsumed = Math.max(0, Math.min(100, batteryConsumed));
    }

    public void setStartLocation(String startLocation) {
        this.startLocation = startLocation != null ? startLocation : "Unknown";
    }

    public void setEndLocation(String endLocation) {
        this.endLocation = endLocation != null ? endLocation : "Unknown";
    }

    // Utility methods
    public String getFormattedDate() {
        SimpleDateFormat sdf = new SimpleDateFormat("MMM dd, yyyy", Locale.getDefault());
        return sdf.format(new Date(timestamp));
    }

    public String getFormattedTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm", Locale.getDefault());
        return sdf.format(new Date(timestamp));
    }

    public String getFormattedDateTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("MMM dd, yyyy HH:mm", Locale.getDefault());
        return sdf.format(new Date(timestamp));
    }

    public String getFormattedStartTime() {
        long startTime = timestamp - (duration * 1000); // Calculate start time
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm", Locale.getDefault());
        return sdf.format(new Date(startTime));
    }

    public String getFormattedEndTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm", Locale.getDefault());
        return sdf.format(new Date(timestamp));
    }

    public String getFormattedTimeRange() {
        return getFormattedStartTime() + " - " + getFormattedEndTime();
    }

    public String getFormattedDistance() {
        if (distance < 1.0) {
            return String.format(Locale.getDefault(), "%.0f m", distance * 1000);
        } else {
            return String.format(Locale.getDefault(), "%.2f km", distance);
        }
    }

    public String getFormattedDuration() {
        long hours = duration / 3600;
        long minutes = (duration % 3600) / 60;
        long seconds = duration % 60;

        if (hours > 0) {
            return String.format(Locale.getDefault(), "%dh %dm", hours, minutes);
        } else if (minutes > 0) {
            return String.format(Locale.getDefault(), "%dm %ds", minutes, seconds);
        } else {
            return String.format(Locale.getDefault(), "%ds", seconds);
        }
    }

    public String getFormattedAverageSpeed() {
        return String.format(Locale.getDefault(), "%.1f km/h", averageSpeed);
    }

    public String getEfficiencyRating() {
        // Calculate efficiency based on battery consumption per kilometer
        if (distance <= 0) return "N/A";

        double consumptionPerKm = batteryConsumed / distance;
        if (consumptionPerKm <= 8) {
            return "🟢 Excellent";
        } else if (consumptionPerKm <= 12) {
            return "🟡 Good";
        } else if (consumptionPerKm <= 18) {
            return "🟠 Fair";
        } else {
            return "🔴 Poor";
        }
    }

    public boolean isLongTrip() {
        return distance > 0.8 || duration > 1800; // More than 800m or 30 minutes
    }

    public boolean isHighSpeedTrip() {
        return averageSpeed > 8.0; // More than 8 km/h average (reasonable for small autonomous car)
    }

    public boolean isEfficientTrip() {
        return distance > 0 && (batteryConsumed / distance) <= 12; // Less than 12% per km
    }

    @Override
    public String toString() {
        return "TripRecord{" +
                "id=" + id +
                ", timestamp=" + timestamp +
                ", distance=" + distance +
                ", duration=" + duration +
                ", averageSpeed=" + averageSpeed +
                ", batteryConsumed=" + batteryConsumed +
                ", startLocation='" + startLocation + '\'' +
                ", endLocation='" + endLocation + '\'' +
                '}';
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;

        TripRecord that = (TripRecord) obj;
        return id == that.id && timestamp == that.timestamp;
    }

    @Override
    public int hashCode() {
        return Long.hashCode(id) + Long.hashCode(timestamp);
    }
}