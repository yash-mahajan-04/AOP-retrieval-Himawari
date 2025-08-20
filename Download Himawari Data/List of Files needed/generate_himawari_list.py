import pandas as pd
import os

# --- NEW: FILTERS TO REDUCE FILE COUNT ---
# 1. Filter by daylight hours
# This assumes the 'datetime' column in your CSV is in UTC.
FILTER_BY_DAYLIGHT_HOURS = False
START_HOUR_UTC = 1  # 1:00 UTC
END_HOUR_UTC = 17 # 17:59 UTC

# 2. Make the temporal matching window stricter
REDUCE_TIME_WINDOW = True
NEW_TIME_DELTA_MINUTES = 30 # Match +/- 30 minutes

# 3. (Optional) Filter by a minimum AOD value to focus on hazy days
# To use this, change to True and set a threshold.
FILTER_BY_AOD = False
AOD_THRESHOLD = 0.4


# --- Configuration ---

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

GROUND_DATA_FILE = os.path.join(SCRIPT_DIR, "../../Aeronet Merging AOD FMF/Merged Ground Truth/AERONET_groundtruth_ALL.csv")
OUTPUT_FILE = "himawari_timestamps_to_download_total.txt"
SATELLITE_INTERVAL_MINUTES = 10 # Himawari's 10-minute interval


def generate_required_timestamps(csv_path):
    print(f"🔄 Reading ground data from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"❌ ERROR: File not found at '{csv_path}'")
        return

    df = pd.read_csv(csv_path, usecols=['datetime', 'AOD'], parse_dates=['datetime'])
    df.dropna(subset=['datetime', 'AOD'], inplace=True)
    print(f"Initial records found: {len(df)}")

    # --- Apply Filters ---
    if FILTER_BY_DAYLIGHT_HOURS:
        df = df[df['datetime'].dt.hour.between(START_HOUR_UTC, END_HOUR_UTC)]
        print(f"After daylight filter ({START_HOUR_UTC}:00-{END_HOUR_UTC}:59 UTC): {len(df)} records")

    if FILTER_BY_AOD:
        df = df[df['AOD'] >= AOD_THRESHOLD]
        print(f"After AOD filter (AOD >= {AOD_THRESHOLD}): {len(df)} records")

    if len(df) == 0:
        print("❌ No records left after filtering. Exiting.")
        return

    unique_ground_times = df['datetime'].unique()
    print(f"Found {len(unique_ground_times)} unique ground timestamps after filtering.")

    time_delta_minutes = NEW_TIME_DELTA_MINUTES if REDUCE_TIME_WINDOW else 30
    time_delta = pd.Timedelta(minutes=time_delta_minutes)
    satellite_freq = f"{SATELLITE_INTERVAL_MINUTES}min"
    required_timestamps = set()

    print(f"⚙️  Calculating required satellite timestamps with a +/- {time_delta_minutes} min window...")
    for ground_time in unique_ground_times:
        start_window = ground_time - time_delta
        end_window = ground_time + time_delta
        first_satellite_slot = start_window.ceil(satellite_freq)
        required_range = pd.date_range(start=first_satellite_slot, end=end_window, freq=satellite_freq)
        required_timestamps.update(required_range)

    print(f"✅ Found {len(required_timestamps)} unique satellite timestamps to download.")

    formatted_timestamps = sorted([ts.strftime('%Y%m%d_%H%M') for ts in required_timestamps])
    
    with open(OUTPUT_FILE, 'w') as f:
        for ts in formatted_timestamps:
            f.write(f"{ts}\n")

    print(f"💾 Saved filtered list to: {OUTPUT_FILE}")


# --- Run the script ---
if __name__ == "__main__":
    generate_required_timestamps(GROUND_DATA_FILE)