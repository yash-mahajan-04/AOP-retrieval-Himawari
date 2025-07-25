import os
import pandas as pd
import numpy as np
from glob import glob
import warnings

# Ignore the specific warning from the previous step if it appears
warnings.filterwarnings("ignore", message="invalid value encountered in cast")

# === Haversine Distance Function ===
def haversine_np(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees).
    Vectorized version.
    """
    R = 6371.0  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# === 1. SETUP: Define Paths and Parameters ===
satellite_data_folder = "toa_filtered_near_stations"
ground_data_folder = "Aeronet Merging AOD FMF/Merged Ground Truth"
output_file = "Final_Matched_Data.csv"
TIME_DELTA_MINUTES = 30
TIME_WINDOW = pd.Timedelta(minutes=TIME_DELTA_MINUTES)

# === 2. LOAD THE SINGLE GROUND DATA FILE ===
print("🔄 Loading the combined AERONET ground station data file...")

# 👉 Please update this to the exact name of your single CSV file
ground_data_filename = "AERONET_groundtruth_ALL.csv" # <--- EXAMPLE FILENAME
ground_data_file_path = os.path.join(ground_data_folder, ground_data_filename)

if not os.path.exists(ground_data_file_path):
    raise FileNotFoundError(
        f"Error: The ground data file was not found at {ground_data_file_path}\n"
        f"Please make sure the `ground_data_filename` is correct."
    )

master_ground_df = pd.read_csv(ground_data_file_path)

# *** MODIFICATION START ***
# Rename lowercase 'datetime' and 'station' columns to the expected names
master_ground_df.rename(columns={'datetime': 'Datetime', 'station': 'Station'}, inplace=True)

# Convert the existing 'Datetime' column to a proper datetime object
master_ground_df['Datetime'] = pd.to_datetime(master_ground_df['Datetime'], errors='coerce')

# Drop rows with invalid dates and the now-redundant original columns
master_ground_df.dropna(subset=['Datetime'], inplace=True)
# Use errors='ignore' in case the 'Date'/'Time' columns don't exist
master_ground_df.drop(columns=['Date', 'Time'], inplace=True, errors='ignore')
# *** MODIFICATION END ***

print(f"✅ Loaded data for {master_ground_df['Station'].nunique()} stations from the master file.")


# === 3. PROCESS SATELLITE FILES AND FIND MATCHES ===
satellite_files = sorted(glob(os.path.join(satellite_data_folder, "*.csv")))
final_matches = []

print(f"\n🛰️  Processing {len(satellite_files)} satellite files to find matches...")

for sat_file in satellite_files:
    sat_df = pd.read_csv(sat_file)
    if sat_df.empty:
        continue

    # Create the satellite datetime column
    sat_df['Datetime'] = pd.to_datetime(
        sat_df['Date'] + ' ' + sat_df['Time'],
        format="%d:%m:%Y %H:%M:%S"
    )

    for station_name, station_pixels_df in sat_df.groupby('Station'):
        # Average the satellite data
        closest_pixel_data = station_pixels_df.mean(numeric_only=True).to_dict()
        closest_pixel_data['Station'] = station_name
        sat_time = station_pixels_df['Datetime'].iloc[0]
        closest_pixel_data['Datetime_sat'] = sat_time

        # Define time window
        start_time = sat_time - TIME_WINDOW
        end_time = sat_time + TIME_WINDOW

        # Select ground data for the current station within the time window
        temporal_matches = master_ground_df[
            (master_ground_df['Station'] == station_name) &
            (master_ground_df['Datetime'] >= start_time) &
            (master_ground_df['Datetime'] <= end_time)
        ]

        if temporal_matches.empty:
            continue

        # Aggregate ground data
        aggregated_ground_data = temporal_matches[['AOD', 'AE', 'FMF']].mean().to_dict()
        aggregated_ground_data = {
            'AOD_ground_mean': aggregated_ground_data['AOD'],
            'AE_ground_mean': aggregated_ground_data['AE'],
            'FMF_ground_mean': aggregated_ground_data['FMF'],
            'num_ground_matches': len(temporal_matches)
        }

        # Combine satellite and ground data
        final_row = {**closest_pixel_data, **aggregated_ground_data}
        final_matches.append(final_row)

# === 4. SAVE FINAL DATASET ===
if final_matches:
    final_df = pd.DataFrame(final_matches)

    # Define and reorder columns for a clean output
    cols_to_keep = [
        'Datetime_sat', 'Station',
        'rho_01', 'rho_02', 'rho_03', 'rho_04', 'rho_05', 'rho_06',
        'bt_07', 'bt_08', 'bt_09', 'bt_10', 'bt_11', 'bt_12', 'bt_13', 'bt_14', 'bt_15', 'bt_16',
        'SOZ', 'VZ', 'RA',
        'latitude', 'longitude',
        'AOD_ground_mean', 'AE_ground_mean', 'FMF_ground_mean', 'num_ground_matches'
    ]
    final_cols = [col for col in cols_to_keep if col in final_df.columns]
    final_df = final_df[final_cols]
    
    final_df.sort_values(by=['Datetime_sat', 'Station'], inplace=True)
    final_df.to_csv(output_file, index=False)
    print(f"\n✅ Success! Saved {len(final_df)} matched records to {output_file}")
else:
    print("\n❌ No matches found between satellite and ground data.")