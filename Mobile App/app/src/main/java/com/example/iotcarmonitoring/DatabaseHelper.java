package com.example.iotcarmonitoring;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import java.util.ArrayList;
import java.util.List;

public class DatabaseHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "iot_car_monitoring.db";
    private static final int DATABASE_VERSION = 1;

    // Table names
    private static final String TABLE_TRIPS = "trips";
    private static final String TABLE_BATTERY_READINGS = "battery_readings";
    private static final String TABLE_TEMPERATURE_READINGS = "temperature_readings";
    private static final String TABLE_ALERTS = "alerts";

    // Common columns
    private static final String COLUMN_ID = "id";
    private static final String COLUMN_TIMESTAMP = "timestamp";

    // Trip table columns
    private static final String COLUMN_DISTANCE = "distance";
    private static final String COLUMN_DURATION = "duration";
    private static final String COLUMN_AVG_SPEED = "avg_speed";
    private static final String COLUMN_BATTERY_CONSUMED = "battery_consumed";
    private static final String COLUMN_START_LOCATION = "start_location";
    private static final String COLUMN_END_LOCATION = "end_location";

    // Battery readings columns
    private static final String COLUMN_BATTERY_LEVEL = "battery_level";
    private static final String COLUMN_BATTERY_VOLTAGE = "battery_voltage";
    private static final String COLUMN_BATTERY_HEALTH = "battery_health";

    // Temperature readings columns
    private static final String COLUMN_CPU_TEMP = "cpu_temperature";
    private static final String COLUMN_AMBIENT_TEMP = "ambient_temperature";

    // Alerts columns
    private static final String COLUMN_ALERT_TYPE = "alert_type";
    private static final String COLUMN_ALERT_MESSAGE = "alert_message";
    private static final String COLUMN_IS_READ = "is_read";

    public DatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        // Create trips table
        String createTripsTable = "CREATE TABLE " + TABLE_TRIPS + " (" +
                COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
                COLUMN_TIMESTAMP + " INTEGER NOT NULL, " +
                COLUMN_DISTANCE + " REAL NOT NULL, " +
                COLUMN_DURATION + " INTEGER NOT NULL, " +
                COLUMN_AVG_SPEED + " REAL NOT NULL, " +
                COLUMN_BATTERY_CONSUMED + " INTEGER NOT NULL, " +
                COLUMN_START_LOCATION + " TEXT, " +
                COLUMN_END_LOCATION + " TEXT" +
                ")";
        db.execSQL(createTripsTable);

        // Create battery readings table
        String createBatteryTable = "CREATE TABLE " + TABLE_BATTERY_READINGS + " (" +
                COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
                COLUMN_TIMESTAMP + " INTEGER NOT NULL, " +
                COLUMN_BATTERY_LEVEL + " INTEGER NOT NULL, " +
                COLUMN_BATTERY_VOLTAGE + " REAL NOT NULL, " +
                COLUMN_BATTERY_HEALTH + " TEXT NOT NULL" +
                ")";
        db.execSQL(createBatteryTable);

        // Create temperature readings table
        String createTempTable = "CREATE TABLE " + TABLE_TEMPERATURE_READINGS + " (" +
                COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
                COLUMN_TIMESTAMP + " INTEGER NOT NULL, " +
                COLUMN_CPU_TEMP + " REAL NOT NULL, " +
                COLUMN_AMBIENT_TEMP + " REAL NOT NULL" +
                ")";
        db.execSQL(createTempTable);

        // Create alerts table
        String createAlertsTable = "CREATE TABLE " + TABLE_ALERTS + " (" +
                COLUMN_ID + " INTEGER PRIMARY KEY AUTOINCREMENT, " +
                COLUMN_TIMESTAMP + " INTEGER NOT NULL, " +
                COLUMN_ALERT_TYPE + " TEXT NOT NULL, " +
                COLUMN_ALERT_MESSAGE + " TEXT NOT NULL, " +
                COLUMN_IS_READ + " INTEGER DEFAULT 0" +
                ")";
        db.execSQL(createAlertsTable);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_TRIPS);
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_BATTERY_READINGS);
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_TEMPERATURE_READINGS);
        db.execSQL("DROP TABLE IF EXISTS " + TABLE_ALERTS);
        onCreate(db);
    }

    // Trip operations
    public long insertTrip(TripRecord trip) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();

        values.put(COLUMN_TIMESTAMP, trip.getTimestamp());
        values.put(COLUMN_DISTANCE, trip.getDistance());
        values.put(COLUMN_DURATION, trip.getDuration());
        values.put(COLUMN_AVG_SPEED, trip.getAverageSpeed());
        values.put(COLUMN_BATTERY_CONSUMED, trip.getBatteryConsumed());
        values.put(COLUMN_START_LOCATION, trip.getStartLocation());
        values.put(COLUMN_END_LOCATION, trip.getEndLocation());

        long id = db.insert(TABLE_TRIPS, null, values);
        db.close();
        return id;
    }

    public List<TripRecord> getAllTrips() {
        List<TripRecord> trips = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();

        String query = "SELECT * FROM " + TABLE_TRIPS + " ORDER BY " + COLUMN_TIMESTAMP + " DESC";
        Cursor cursor = db.rawQuery(query, null);

        if (cursor.moveToFirst()) {
            do {
                TripRecord trip = new TripRecord(
                        cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID)),
                        cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_TIMESTAMP)),
                        cursor.getDouble(cursor.getColumnIndexOrThrow(COLUMN_DISTANCE)),
                        cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_DURATION)),
                        cursor.getDouble(cursor.getColumnIndexOrThrow(COLUMN_AVG_SPEED)),
                        cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_BATTERY_CONSUMED)),
                        cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_START_LOCATION)),
                        cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_END_LOCATION))
                );
                trips.add(trip);
            } while (cursor.moveToNext());
        }

        cursor.close();
        db.close();
        return trips;
    }

    // Battery reading operations
    public long insertBatteryReading(int level, float voltage, String health) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();

        values.put(COLUMN_TIMESTAMP, System.currentTimeMillis());
        values.put(COLUMN_BATTERY_LEVEL, level);
        values.put(COLUMN_BATTERY_VOLTAGE, voltage);
        values.put(COLUMN_BATTERY_HEALTH, health);

        long id = db.insert(TABLE_BATTERY_READINGS, null, values);
        db.close();
        return id;
    }

    public List<BatteryReading> getBatteryHistory(long fromTimestamp) {
        List<BatteryReading> readings = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();

        String query = "SELECT * FROM " + TABLE_BATTERY_READINGS +
                " WHERE " + COLUMN_TIMESTAMP + " >= ? ORDER BY " + COLUMN_TIMESTAMP + " ASC";
        Cursor cursor = db.rawQuery(query, new String[]{String.valueOf(fromTimestamp)});

        if (cursor.moveToFirst()) {
            do {
                BatteryReading reading = new BatteryReading(
                        cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_TIMESTAMP)),
                        cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_BATTERY_LEVEL)),
                        cursor.getFloat(cursor.getColumnIndexOrThrow(COLUMN_BATTERY_VOLTAGE)),
                        cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_BATTERY_HEALTH))
                );
                readings.add(reading);
            } while (cursor.moveToNext());
        }

        cursor.close();
        db.close();
        return readings;
    }

    // Temperature reading operations
    public long insertTemperatureReading(float cpuTemp, float ambientTemp) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();

        values.put(COLUMN_TIMESTAMP, System.currentTimeMillis());
        values.put(COLUMN_CPU_TEMP, cpuTemp);
        values.put(COLUMN_AMBIENT_TEMP, ambientTemp);

        long id = db.insert(TABLE_TEMPERATURE_READINGS, null, values);
        db.close();
        return id;
    }

    public List<TemperatureReading> getTemperatureHistory(long fromTimestamp) {
        List<TemperatureReading> readings = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();

        String query = "SELECT * FROM " + TABLE_TEMPERATURE_READINGS +
                " WHERE " + COLUMN_TIMESTAMP + " >= ? ORDER BY " + COLUMN_TIMESTAMP + " ASC";
        Cursor cursor = db.rawQuery(query, new String[]{String.valueOf(fromTimestamp)});

        if (cursor.moveToFirst()) {
            do {
                TemperatureReading reading = new TemperatureReading(
                        cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_TIMESTAMP)),
                        cursor.getFloat(cursor.getColumnIndexOrThrow(COLUMN_CPU_TEMP)),
                        cursor.getFloat(cursor.getColumnIndexOrThrow(COLUMN_AMBIENT_TEMP))
                );
                readings.add(reading);
            } while (cursor.moveToNext());
        }

        cursor.close();
        db.close();
        return readings;
    }

    // Alert operations
    public long insertAlert(String alertType, String message) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();

        values.put(COLUMN_TIMESTAMP, System.currentTimeMillis());
        values.put(COLUMN_ALERT_TYPE, alertType);
        values.put(COLUMN_ALERT_MESSAGE, message);
        values.put(COLUMN_IS_READ, 0);

        long id = db.insert(TABLE_ALERTS, null, values);
        db.close();
        return id;
    }

    public List<AlertRecord> getUnreadAlerts() {
        List<AlertRecord> alerts = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();

        String query = "SELECT * FROM " + TABLE_ALERTS +
                " WHERE " + COLUMN_IS_READ + " = 0 ORDER BY " + COLUMN_TIMESTAMP + " DESC";
        Cursor cursor = db.rawQuery(query, null);

        if (cursor.moveToFirst()) {
            do {
                AlertRecord alert = new AlertRecord(
                        cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_ID)),
                        cursor.getLong(cursor.getColumnIndexOrThrow(COLUMN_TIMESTAMP)),
                        cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_ALERT_TYPE)),
                        cursor.getString(cursor.getColumnIndexOrThrow(COLUMN_ALERT_MESSAGE)),
                        cursor.getInt(cursor.getColumnIndexOrThrow(COLUMN_IS_READ)) == 1
                );
                alerts.add(alert);
            } while (cursor.moveToNext());
        }

        cursor.close();
        db.close();
        return alerts;
    }

    public void markAlertAsRead(long alertId) {
        SQLiteDatabase db = this.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put(COLUMN_IS_READ, 1);

        db.update(TABLE_ALERTS, values, COLUMN_ID + " = ?", new String[]{String.valueOf(alertId)});
        db.close();
    }

    // Utility methods
    public void cleanOldData(long olderThanTimestamp) {
        SQLiteDatabase db = this.getWritableDatabase();

        // Keep only recent battery and temperature readings (older than 30 days)
        db.delete(TABLE_BATTERY_READINGS, COLUMN_TIMESTAMP + " < ?",
                new String[]{String.valueOf(olderThanTimestamp)});
        db.delete(TABLE_TEMPERATURE_READINGS, COLUMN_TIMESTAMP + " < ?",
                new String[]{String.valueOf(olderThanTimestamp)});

        // Keep read alerts for 7 days only
        long weekAgo = System.currentTimeMillis() - (7 * 24 * 60 * 60 * 1000);
        db.delete(TABLE_ALERTS, COLUMN_TIMESTAMP + " < ? AND " + COLUMN_IS_READ + " = 1",
                new String[]{String.valueOf(weekAgo)});

        db.close();
    }

    // Helper classes for data readings
    public static class BatteryReading {
        public long timestamp;
        public int level;
        public float voltage;
        public String health;

        public BatteryReading(long timestamp, int level, float voltage, String health) {
            this.timestamp = timestamp;
            this.level = level;
            this.voltage = voltage;
            this.health = health;
        }
    }

    public static class TemperatureReading {
        public long timestamp;
        public float cpuTemperature;
        public float ambientTemperature;

        public TemperatureReading(long timestamp, float cpuTemperature, float ambientTemperature) {
            this.timestamp = timestamp;
            this.cpuTemperature = cpuTemperature;
            this.ambientTemperature = ambientTemperature;
        }
    }

    public static class AlertRecord {
        public long id;
        public long timestamp;
        public String alertType;
        public String message;
        public boolean isRead;

        public AlertRecord(long id, long timestamp, String alertType, String message, boolean isRead) {
            this.id = id;
            this.timestamp = timestamp;
            this.alertType = alertType;
            this.message = message;
            this.isRead = isRead;
        }
    }
}