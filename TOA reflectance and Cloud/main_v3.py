import xarray as xr
import numpy as np
import pandas as pd
import os
import re
import pickle
from glob import glob
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


# === Station Coordinates ===
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

# === Settings ===
input_folder = "TOA reflectance and Cloud/Himawari Data"
cloud_folder = "TOA reflectance and Cloud/Cloud Mask Data"
output_folder = "toa_filtered_near_stations"
os.makedirs(output_folder, exist_ok=True)

# === Load Precomputed Pixel Masks ===
with open("Pixels Close To Stations/precomputed_masks.pkl", "rb") as f:
    precomputed_masks = pickle.load(f)

grid_shape = precomputed_masks["_grid_shape"]
nc_files = glob(os.path.join(input_folder, "*.nc"))

# === Process Each Himawari File ===
for nc_path in nc_files:
    print(f"\n📦 Processing {os.path.basename(nc_path)}")

    match = re.search(r'(\d{8})_(\d{4})', nc_path)
    if not match:
        print("⚠️ Skipping, date not found in filename")
        continue

    date_str, time_str = match.group(1), match.group(2)
    date_fmt = f"{date_str[6:8]}:{date_str[4:6]}:{date_str[0:4]}"
    time_fmt = f"{time_str[:2]}:{time_str[2:]}:00"
    timestamp = f"{date_str}_{time_str}"

    out_path = os.path.join(output_folder, f"toa_filtered_{timestamp}.csv")
    if os.path.exists(out_path):
        print(f"⏭️ Already exists: {out_path}")
        continue

    cloud_match = glob(os.path.join(cloud_folder, f"*{timestamp}*.nc"))
    if not cloud_match:
        print(f"☁️ No cloud mask file found for {timestamp}")
        continue
    cloud_path = cloud_match[0]

    try:
        ds = xr.open_dataset(nc_path)
        ds_cloud = xr.open_dataset(cloud_path)

        all_rows = []

        for name in station_coords:
            if name not in precomputed_masks:
                print(f"⚠️ Skipping {name} (not found in precomputed masks)")
                continue

            # === 1. Load Precomputed Data for the Station ===
            # These are the original coordinates and indices for ALL pixels near the station.
            mask_indices = precomputed_masks[name]["mask_indices"] # Shape (N, 2)
            lats_nearby = np.array(precomputed_masks[name]["lat"])       # Shape (N,)
            lons_nearby = np.array(precomputed_masks[name]["lon"])       # Shape (N,)

            # Unpack row and column indices for easier use.
            row_idx_nearby = mask_indices[:, 0]
            col_idx_nearby = mask_indices[:, 1]

            # === 2. Get Cloud Mask for Nearby Pixels ===
            # Interpolate the cloud data to the exact coordinates of our nearby pixels.
            cltype_interp = ds_cloud["CLTYPE"].interp(
                latitude=xr.DataArray(lats_nearby, dims="points"),
                longitude=xr.DataArray(lons_nearby, dims="points"),
                method="nearest"
            ).values.astype("int")

            # Create a boolean filter for cloud-free pixels (cloud type == 0).
            is_cloud_free = (cltype_interp == 0)
            
            num_nearby = len(lats_nearby)
            num_cloud_free = np.sum(is_cloud_free)

            print(f"📌 {name}: {num_nearby} pixels nearby | ☁️ {num_cloud_free} cloud-free")

            if num_cloud_free == 0:
                continue
            
            # === 3. Filter Indices to Get ONLY Cloud-Free Pixels ===
            # This is the key step! We select only the indices that correspond to cloud-free pixels.
            cf_row_idx = row_idx_nearby[is_cloud_free]
            cf_col_idx = col_idx_nearby[is_cloud_free]
            
            # === 4. Extract Data Using the Final, Filtered Indices ===
            # Now we access the large Himawari arrays only once, using our small list of final indices.
            # This is much more efficient.
            
            # --- TOA Reflectance ---
            # Get Solar Zenith Angle for just the cloud-free pixels
            soz_vals = ds["SOZ"].values[cf_row_idx, cf_col_idx]
            cos_theta_s = np.cos(np.deg2rad(soz_vals))
            cos_theta_s[cos_theta_s <= 0] = np.nan # Avoid division by zero

            reflectance_all = {}
            for i in range(1, 7):
                albedo_vals = ds[f"albedo_0{i}"].values[cf_row_idx, cf_col_idx]
                reflectance_all[f"rho_0{i}"] = albedo_vals / cos_theta_s
                
            # --- Brightness Temperature ---
            brightness = {
                f"bt_{i:02}": ds[f"tbb_{i:02}"].values[cf_row_idx, cf_col_idx]
                for i in range(7, 17)
            }

            # --- Angle Geometry ---
            SAA = ds["SAA"].values[cf_row_idx, cf_col_idx]
            SOA = ds["SOA"].values[cf_row_idx, cf_col_idx]
            SAZ = ds["SAZ"].values[cf_row_idx, cf_col_idx] # Viewing Zenith Angle

            RA = np.abs(SAA - SOA)
            RA = np.where(RA > 180, 360 - RA, RA)

            # === 5. Build the Final DataFrame ===
            df = pd.DataFrame(reflectance_all)
            df = df.assign(**brightness) # A clean way to add multiple columns from a dict

            df["SOZ"] = soz_vals
            df["VZ"] = SAZ
            df["RA"] = RA
            # Filter the original lat/lon arrays to get the coordinates of the cloud-free pixels
            df["latitude"] = lats_nearby[is_cloud_free]
            df["longitude"] = lons_nearby[is_cloud_free]
            df["Station"] = name
            df["Date"] = date_fmt
            df["Time"] = time_fmt

            all_rows.append(df)

        if all_rows:
            pd.concat(all_rows).to_csv(out_path, index=False)
            print(f"✅ Saved: {out_path}")
        else:
            print("🚫 No cloud-free pixels found near any station for this timestamp.")

    except Exception as e:
        # Using f-string with exception for more direct error message
        print(f"❌ Error processing {os.path.basename(nc_path)}: {e}")