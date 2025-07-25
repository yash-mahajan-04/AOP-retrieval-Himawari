import os
import pandas as pd
import numpy as np

# === Functions ===

def find_header_line(filepath, keyword):
    """Finds the header line by searching for the keyword."""
    with open(filepath, "r") as file:
        lines = file.readlines()
        for idx, line in enumerate(lines):
            if keyword in line:
                return idx
    return None  # not found

def load_aod_file(aod_path):
    header_line = find_header_line(aod_path, "Date(dd:mm:yyyy)")
    if header_line is None:
        raise ValueError(f"Cannot find AOD header in {aod_path}")
    aod = pd.read_csv(aod_path, skiprows=header_line)

    # Try converting date+time safely
    try:
        aod["Date"] = aod["Date(dd:mm:yyyy)"].astype(str).str.strip()
        aod["Time"] = aod["Time(hh:mm:ss)"].astype(str).str.strip()
        aod["datetime"] = pd.to_datetime(
            aod["Date"] + " " + aod["Time"], format="%d:%m:%Y %H:%M:%S"
        )
    except Exception:
        # fallback if date column is Excel-style float
        aod["datetime"] = pd.to_datetime(aod["Date(dd:mm:yyyy)"], unit="D", origin="1899-12-30") + \
                          pd.to_timedelta(pd.to_datetime(aod["Time(hh:mm:ss)"]).dt.strftime("%H:%M:%S"))

    aod_clean = aod[["datetime", "AOD_500nm", "440-870_Angstrom_Exponent", "Date(dd:mm:yyyy)", "Time(hh:mm:ss)"]].copy()
    aod_clean.columns = ["datetime", "AOD", "AE", "Date", "Time"]
    aod_clean.dropna(inplace=True)
    return aod_clean


def load_sda_file(sda_path):
    header_line = find_header_line(sda_path, "Date_(dd:mm:yyyy)")
    if header_line is None:
        raise ValueError(f"Cannot find SDA header in {sda_path}")
    sda = pd.read_csv(sda_path, skiprows=header_line)

    # Try converting date+time safely
    try:
        sda["Date"] = sda["Date_(dd:mm:yyyy)"].astype(str).str.strip()
        sda["Time"] = sda["Time_(hh:mm:ss)"].astype(str).str.strip()
        sda["datetime"] = pd.to_datetime(
            sda["Date"] + " " + sda["Time"], format="%d:%m:%Y %H:%M:%S"
        )
    except Exception:
        sda["datetime"] = pd.to_datetime(sda["Date_(dd:mm:yyyy)"], unit="D", origin="1899-12-30") + \
                          pd.to_timedelta(pd.to_datetime(sda["Time_(hh:mm:ss)"]).dt.strftime("%H:%M:%S"))

    sda_clean = sda[["datetime", "FineModeFraction_500nm[eta]"]].copy()
    sda_clean.columns = ["datetime", "FMF"]
    sda_clean.dropna(inplace=True)
    return sda_clean


# === Constants ===
station_coords = {
    "Chiayi": (23.452, 120.255),
    "Hong_Kong_PolyU": (22.3045, 114.1791),
    "Taihu": (31.421, 120.215),
    "Anmyon": (36.539, 126.330),
    "Beijing": (39.904, 116.407),
    "Beijing-CAMS": (39.905, 116.391),
    "Chiang_Mai_Met_Sta": (18.770, 98.980),
    "Fukuoka": (33.590, 130.401),
    "Gandhi_College": (25.870, 85.080),
    "Gwangju_GIST": (35.230, 126.840),
    "Hong_Kong_Sheung": (22.5000, 114.1000),
    "Lulin": (23.4686, 120.8736),
    "NAM_CO": (30.773, 90.962),
    "Osaka": (34.693, 135.502),
    "Pokhara": (28.209, 83.991),
    "QOMS_CAS": (28.365, 86.948),
    "Seoul_SNU": (37.460, 126.950),
    "Taipei_CWB": (25.037, 121.565),
    "XiangHe": (39.7610, 117.0060),
    "Kanpur": (26.512, 80.231),
    "Omkoi": (17.798, 98.431),
    "NGHIA_DO": (21.047, 105.799),
    "Nong_Khai": (17.877, 102.716),
    "Lumbini": (27.490, 83.279)
}

# === Directories ===
os.chdir(r"D:\TE\Major Project\AOD\Optimized Approach\Aeronet Merging AOD FMF")
aod_root = "./AOD/"
sda_root = "./FMF/"
output_root = "./Merged Ground Truth/"
os.makedirs(output_root, exist_ok=True)

# === Find all stations ===
stations = os.listdir(aod_root)
stations = [s for s in stations if os.path.isdir(os.path.join(aod_root, s))]

# === Initialize a list to collect all merged data === 🗃️
all_merged_data = []

for station_folder in stations:
    try:
        station_name = station_folder.split("_", 2)[-1]
        
        # 🔁 Skip per-station file output — we'll save one combined file later
        aod_folder = os.path.join(aod_root, station_folder)
        sda_folder = os.path.join(sda_root, station_folder)

        aod_files = [f for f in os.listdir(aod_folder) if f.endswith(".lev20")]
        sda_files = [f for f in os.listdir(sda_folder) if f.endswith(".ONEILL_lev20")]

        if not aod_files or not sda_files:
            print(f"⚠️ Missing files for {station_folder}, skipping...")
            continue

        aod_path = os.path.join(aod_folder, aod_files[0])
        sda_path = os.path.join(sda_folder, sda_files[0])

        # Load and merge
        aod_clean = load_aod_file(aod_path)
        sda_clean = load_sda_file(sda_path)
        merged = pd.merge(aod_clean, sda_clean, on="datetime", how="inner")
        merged.dropna(subset=["AOD", "AE", "FMF"], inplace=True)

        # Filter invalids
        invalid_mask = (merged["AOD"] < 0) | (merged["AE"] < 0) | (merged["FMF"] < 0)
        merged = merged[~invalid_mask]

        # Add station info
        lat, lon = station_coords.get(station_name, (np.nan, np.nan))
        merged["latitude"] = lat
        merged["longitude"] = lon
        merged["station"] = station_name  # 🆕 Add station name for context

        # 🔁 Append to master list
        all_merged_data.append(merged)

        print(f"✅ Processed: {station_name} with {len(merged)} rows")

    except Exception as e:
        print(f"❌ Error processing {station_folder}: {e}")

# === Combine and Save All Data ===
if all_merged_data:
    final_df = pd.concat(all_merged_data, ignore_index=True)
    output_path = os.path.join(output_root, "AERONET_groundtruth_ALL.csv")
    final_df.to_csv(output_path, index=False)
    print(f"\n🎉 Combined data saved to: {output_path}")
else:
    print("\n⚠️ No valid data found to merge.")


print("\n🎯 All stations processed!")
