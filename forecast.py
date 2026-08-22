"""
Forecasting + anomaly detection for building energy usage.

Uses Holt-Winters exponential smoothing (statsmodels) instead of Prophet:
much faster to install, no compiler toolchain needed, and plenty accurate
for a 24-hour hackathon build with hourly seasonality.
"""

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

FORECAST_HOURS = 72
ANOMALY_STD_THRESHOLD = 2.5
ROLLING_WINDOW = 24  # hours
SAME_HOUR_LOOKBACK_DAYS = 14  # compare each hour against the same hour on previous days


def load_data(path: str = "data/energy_usage.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df


def detect_anomalies(series_df: pd.DataFrame) -> pd.DataFrame:
    """Flags points that deviate more than ANOMALY_STD_THRESHOLD std devs
    from the typical usage at that SAME hour-of-day over recent days.

    This avoids false positives from normal daily ramp-ups (e.g. 8am->9am
    jump every day is expected, not anomalous) by comparing like-for-like.
    """
    df = series_df.copy().sort_values("timestamp").reset_index(drop=True)
    df["hour"] = df["timestamp"].dt.hour
    df["is_weekend"] = df["timestamp"].dt.dayofweek >= 5

    lookback_points = SAME_HOUR_LOOKBACK_DAYS  # one point per matching day at that hour

    baseline_mean = pd.Series(index=df.index, dtype=float)
    baseline_std = pd.Series(index=df.index, dtype=float)

    for (hour, _is_weekend), group in df.groupby(["hour", "is_weekend"]):
        idx = group.index
        vals = group["usage_kwh"]
        rolling_mean = vals.rolling(lookback_points, min_periods=4).mean()
        rolling_std = vals.rolling(lookback_points, min_periods=4).std()
        baseline_mean.loc[idx] = rolling_mean.values
        baseline_std.loc[idx] = rolling_std.values

    df["rolling_mean"] = baseline_mean
    df["rolling_std"] = baseline_std

    deviation = (df["usage_kwh"] - baseline_mean).abs()
    std_threshold = ANOMALY_STD_THRESHOLD * baseline_std
    # Relative floor: at low-usage hours (e.g. overnight) noise is naturally
    # small in absolute terms, so a std-only rule can under-flag a real
    # spike. Also catch anything >=40% above its same-hour typical usage.
    relative_threshold = 0.4 * baseline_mean

    df["is_anomaly"] = (
        (deviation > std_threshold) | (deviation > relative_threshold)
    ).fillna(False)

    return df.drop(columns=["hour", "is_weekend"])


def forecast_series(series_df: pd.DataFrame, periods: int = FORECAST_HOURS) -> pd.DataFrame:
    """Fits Holt-Winters on one building's hourly series and returns a
    forecast dataframe with timestamp + predicted_kwh."""
    df = series_df.copy().sort_values("timestamp").reset_index(drop=True)
    ts = df.set_index("timestamp")["usage_kwh"].asfreq("h")
    ts = ts.interpolate()

    model = ExponentialSmoothing(
        ts,
        trend=None,
        seasonal="add",
        seasonal_periods=24,  # daily seasonality
        initialization_method="estimated",
    ).fit()

    forecast_values = model.forecast(periods)
    forecast_index = pd.date_range(
        start=ts.index[-1] + pd.Timedelta(hours=1), periods=periods, freq="h"
    )

    return pd.DataFrame({"timestamp": forecast_index, "predicted_kwh": forecast_values.values})


def get_building_analysis(df: pd.DataFrame, building: str) -> dict:
    """Convenience wrapper: filters to one building and returns historical
    (with anomalies flagged) + forecast dataframes."""
    building_df = df[df["building"] == building]
    historical_with_anomalies = detect_anomalies(building_df)
    forecast_df = forecast_series(building_df)

    return {
        "historical": historical_with_anomalies,
        "forecast": forecast_df,
        "anomaly_count": int(historical_with_anomalies["is_anomaly"].sum()),
    }
