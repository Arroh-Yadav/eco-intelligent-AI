"""
Loads REAL campus building electricity data from the Building Data Genome
Project 2 (BDG2) dataset — a peer-reviewed, ASHRAE-competition dataset of
real hourly electricity meters from 1,636 real buildings worldwide
(Miller et al., Scientific Data, 2020: https://doi.org/10.1038/s41597-020-00712-x)

This replaces the synthetic data_generator.py with genuine measured data
from real education-sector buildings, while producing the exact same
output schema (timestamp, building, usage_kwh) so nothing else in the
app needs to change.

SETUP (one-time):
1. Go to https://www.kaggle.com/datasets/claytonmiller/buildingdatagenomeproject2
2. Sign up free, click Download
3. Unzip into a folder, note the paths to metadata.csv and electricity_cleaned.csv
4. Update METADATA_PATH and ELECTRICITY_PATH below to point at those files

Run: python real_data_loader.py
Output: data/energy_usage.csv (same schema as data_generator.py)
"""

import os

import pandas as pd

# --- EDIT THESE TWO PATHS to wherever you unzipped the Kaggle download ---
METADATA_PATH = "bdg2_raw/metadata.csv"
ELECTRICITY_PATH = "bdg2_raw/electricity_cleaned.csv"

NUM_BUILDINGS = 3          # how many real buildings to include in the demo
DAYS_OF_HISTORY = 45       # trim to this many most-recent days for speed/relevance
PRIMARY_USE_FILTER = "Education"  # BDG2 category for university/college buildings


def main():
    if not os.path.exists(METADATA_PATH) or not os.path.exists(ELECTRICITY_PATH):
        raise FileNotFoundError(
            "Couldn't find the BDG2 files. Download them from "
            "https://www.kaggle.com/datasets/claytonmiller/buildingdatagenomeproject2 "
            "and update METADATA_PATH / ELECTRICITY_PATH at the top of this script."
        )

    print("Loading metadata...")
    metadata = pd.read_csv(METADATA_PATH)

    education_buildings = metadata[
        metadata["primaryspaceusage"] == PRIMARY_USE_FILTER
    ]["building_id"].tolist()

    if not education_buildings:
        raise ValueError(
            f"No buildings found with primaryspaceusage == '{PRIMARY_USE_FILTER}'. "
            "Check the metadata.csv column values — they may differ slightly "
            "(e.g. 'Higher Education') and you may need to adjust PRIMARY_USE_FILTER."
        )

    print(f"Found {len(education_buildings)} education-sector buildings.")

    print("Loading electricity meter data (this file is large, may take a moment)...")
    # Only load the timestamp column + the education buildings we actually want,
    # to avoid pulling all ~1600 building columns into memory.
    usecols_available = pd.read_csv(ELECTRICITY_PATH, nrows=0).columns.tolist()
    selected_buildings = [b for b in education_buildings if b in usecols_available][:NUM_BUILDINGS]

    if not selected_buildings:
        raise ValueError(
            "None of the education buildings from metadata.csv match column "
            "names in electricity_cleaned.csv. Print usecols_available and "
            "education_buildings to debug the ID format mismatch."
        )

    print(f"Using real buildings: {selected_buildings}")

    timestamp_col = usecols_available[0]  # BDG2's first column is the timestamp
    electricity = pd.read_csv(
        ELECTRICITY_PATH, usecols=[timestamp_col] + selected_buildings
    )
    electricity[timestamp_col] = pd.to_datetime(electricity[timestamp_col])

    # Reshape from wide (one column per building) to our long schema
    long_df = electricity.melt(
        id_vars=[timestamp_col], var_name="building", value_name="usage_kwh"
    )
    long_df = long_df.rename(columns={timestamp_col: "timestamp"})
    long_df = long_df.dropna(subset=["usage_kwh"])

    # Trim to most recent DAYS_OF_HISTORY per building for demo speed/relevance
    trimmed_frames = []
    for building, group in long_df.groupby("building"):
        group = group.sort_values("timestamp")
        cutoff = group["timestamp"].max() - pd.Timedelta(days=DAYS_OF_HISTORY)
        trimmed_frames.append(group[group["timestamp"] >= cutoff])

    result = pd.concat(trimmed_frames, ignore_index=True)
    result["usage_kwh"] = result["usage_kwh"].round(2)

    os.makedirs("data", exist_ok=True)
    result.to_csv("data/energy_usage.csv", index=False)

    print(
        f"Saved {len(result)} rows of REAL campus building data "
        f"({len(selected_buildings)} buildings, {DAYS_OF_HISTORY} days) "
        "-> data/energy_usage.csv"
    )
    print(
        "Source: Building Data Genome Project 2 (Miller et al., 2020) — "
        "https://doi.org/10.1038/s41597-020-00712-x"
    )


if __name__ == "__main__":
    main()
