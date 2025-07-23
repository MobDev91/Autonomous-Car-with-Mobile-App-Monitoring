package com.example.iotcarmonitoring;

import android.os.Bundle;
import android.widget.Button;
import android.widget.Switch;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class SimulationControlActivity extends AppCompatActivity {

    private TextView statusText;
    private Switch simulationSwitch;
    private Button normalScenarioBtn;
    private Button lowBatteryBtn;
    private Button overheatingBtn;
    private Button longTripBtn;

    private CarDataManager dataManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_simulation_control);

        initializeViews();
        setupListeners();

        // Get the data manager instance (you might need to pass this differently)
        dataManager = new CarDataManager(this);

        updateStatus();
    }

    private void initializeViews() {
        statusText = findViewById(R.id.simulation_status_text);
        simulationSwitch = findViewById(R.id.simulation_switch);
        normalScenarioBtn = findViewById(R.id.btn_normal_scenario);
        lowBatteryBtn = findViewById(R.id.btn_low_battery);
        overheatingBtn = findViewById(R.id.btn_overheating);
        longTripBtn = findViewById(R.id.btn_long_trip);
    }

    private void setupListeners() {
        simulationSwitch.setOnCheckedChangeListener((buttonView, isChecked) -> {
            dataManager.setSimulationMode(isChecked);
            updateStatus();
        });

        normalScenarioBtn.setOnClickListener(v -> {
            dataManager.forceSimulationScenario("NORMAL");
            updateStatus();
        });

        lowBatteryBtn.setOnClickListener(v -> {
            dataManager.forceSimulationScenario("LOW_BATTERY");
            updateStatus();
        });

        overheatingBtn.setOnClickListener(v -> {
            dataManager.forceSimulationScenario("OVERHEATING");
            updateStatus();
        });

        longTripBtn.setOnClickListener(v -> {
            dataManager.forceSimulationScenario("LONG_TRIP");
            updateStatus();
        });
    }

    private void updateStatus() {
        if (dataManager.isInSimulationMode()) {
            statusText.setText("Simulation Mode: ACTIVE\nReal-time data simulation running");
            simulationSwitch.setChecked(true);
            enableScenarioButtons(true);
        } else {
            statusText.setText("Real Mode: Connecting to Raspberry Pi...");
            simulationSwitch.setChecked(false);
            enableScenarioButtons(false);
        }
    }

    private void enableScenarioButtons(boolean enabled) {
        normalScenarioBtn.setEnabled(enabled);
        lowBatteryBtn.setEnabled(enabled);
        overheatingBtn.setEnabled(enabled);
        longTripBtn.setEnabled(enabled);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (dataManager != null) {
            dataManager.cleanup();
        }
    }
}