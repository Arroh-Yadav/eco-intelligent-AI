"""
Generates realistic synthetic hourly energy usage data for campus buildings.
Includes daily + weekly seasonality and deliberately injected anomalies so
the anomaly detector + AI insight layer always have something meaningful
to catch during a demo.

Run: python data_generator.py
Output: data/energy_usage.csv
"""

import os
import numpy as np
import pandas as pd

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

BUILDINGS = ["Engineering Block", "Main Library", "Hostel Block A"]
DAYS_OF_HISTORY = 45
FREQ = "h"


def daily_pattern(hour: int) -> float:
    """Higher usage 9am-6pm, low overnight, small evening bump."""
    if 9 <= hour <= 18:
        return 1.4
    if 19 <= hour <= 22:
        return 1.0
    return 0.5


def weekly_multiplier(dayofweek: int) -> float:
    """Lower usage on weekends (5=Sat, 6=Sun)."""
    return 0.6 if dayofweek >= 5 else 1.0


def generate_building_series(building: str, timestamps: pd.DatetimeIndex, base_load: float) -> pd.DataFrame:
    n = len(timestamps)
    values = np.zeros(n)

    for i, ts in enumerate(timestamps):
        seasonal = daily_pattern(ts.hour) * weekly_multiplier(ts.dayofweek)
        noise = np.random.normal(0, 0.08)
        values[i] = base_load * seasonal * (1 + noise)

    df = pd.DataFrame({"timestamp": timestamps, "building": building, "usage_kwh": values})

    # --- Inject deliberate anomalies (spikes) at fixed, reproducible points ---
    anomaly_positions = [
        int(n * 0.55),        # mid-history spike (e.g. HVAC left running)
        int(n * 0.55) + 3,
        int(n * 0.82),        # a second, sharper spike near the end (recent, demo-relevant)
        int(n * 0.82) + 1,
    ]
    for pos in anomaly_positions:
        if 0 <= pos < n:
            df.loc[pos, "usage_kwh"] *= np.random.uniform(2.0, 2.8)

    return df


def main():
    timestamps = pd.date_range(
        end=pd.Timestamp.now().floor("h"),
        periods=DAYS_OF_HISTORY * 24,
        freq=FREQ,
    )

    base_loads = {
        "Engineering Block": 120.0,
        "Main Library": 80.0,
        "Hostel Block A": 60.0,
    }

    all_data = [generate_building_series(b, timestamps, base_loads[b]) for b in BUILDINGS]
    result = pd.concat(all_data, ignore_index=True)
    result["usage_kwh"] = result["usage_kwh"].round(2)

    os.makedirs("data", exist_ok=True)
    result.to_csv("data/energy_usage.csv", index=False)
    print(f"Generated {len(result)} rows across {len(BUILDINGS)} buildings -> data/energy_usage.csv")


if __name__ == "__main__":
    main()
