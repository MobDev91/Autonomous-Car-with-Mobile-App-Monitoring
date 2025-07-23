package com.example.iotcarmonitoring;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class TripHistoryAdapter extends RecyclerView.Adapter<TripHistoryAdapter.TripViewHolder> {

    private List<TripRecord> tripHistory;
    private OnTripClickListener clickListener;

    public interface OnTripClickListener {
        void onTripClick(TripRecord trip);
    }

    public TripHistoryAdapter(List<TripRecord> tripHistory) {
        this.tripHistory = tripHistory;
    }

    public void setOnTripClickListener(OnTripClickListener listener) {
        this.clickListener = listener;
    }

    @NonNull
    @Override
    public TripViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_trip_record, parent, false);
        return new TripViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull TripViewHolder holder, int position) {
        TripRecord trip = tripHistory.get(position);
        holder.bind(trip);
    }

    @Override
    public int getItemCount() {
        return tripHistory.size();
    }

    public void updateTrips(List<TripRecord> newTrips) {
        this.tripHistory = newTrips;
        notifyDataSetChanged();
    }

    class TripViewHolder extends RecyclerView.ViewHolder {

        private TextView dateTimeText;
        private TextView distanceText;
        private TextView durationText;
        private TextView speedText;
        private TextView batteryText;
        private TextView efficiencyText;

        public TripViewHolder(@NonNull View itemView) {
            super(itemView);

            dateTimeText = itemView.findViewById(R.id.trip_datetime);
            distanceText = itemView.findViewById(R.id.trip_distance);
            durationText = itemView.findViewById(R.id.trip_duration);
            speedText = itemView.findViewById(R.id.trip_speed);
            batteryText = itemView.findViewById(R.id.trip_battery);
            efficiencyText = itemView.findViewById(R.id.trip_efficiency);

            itemView.setOnClickListener(v -> {
                if (clickListener != null) {
                    int position = getAdapterPosition();
                    if (position != RecyclerView.NO_POSITION) {
                        clickListener.onTripClick(tripHistory.get(position));
                    }
                }
            });
        }

        public void bind(TripRecord trip) {
            dateTimeText.setText(trip.getFormattedDateTime());
            distanceText.setText(trip.getFormattedDistance());
            durationText.setText(trip.getFormattedDuration());
            speedText.setText(trip.getFormattedAverageSpeed());
            batteryText.setText(trip.getBatteryConsumed() + "% used");
            efficiencyText.setText(trip.getEfficiencyRating());
        }
    }
}