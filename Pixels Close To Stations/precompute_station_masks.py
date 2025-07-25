import xarray as xr
import numpy as np
import pandas as pd
import os
import pickle

# === Haversine Distance Function ===
def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

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
max_distance_km = 2.0
himawari_nc_path = "../TOA reflectance and Cloud/Himawari Data/trimmed_NC_H08_20191202_0200_R21_FLDK.06001_06001.nc"
output_mask_file = "precomputed_masks.pkl"

# === Load Himawari Data ===
ds = xr.open_dataset(himawari_nc_path)
lat_vals = ds["latitude"].values
lon_vals = ds["longitude"].values
lon_2d, lat_2d = np.meshgrid(lon_vals, lat_vals)

# === Precompute Masks ===
precomputed = {
    "_grid_shape": lat_2d.shape
}

for name, (lat_c, lon_c) in station_coords.items():
    distances = haversine_np(lat_c, lon_c, lat_2d, lon_2d)
    mask = distances <= max_distance_km
    if not np.any(mask):
        print(f"🚫 No nearby pixels found for {name}. Skipping.")
        continue

    lats = lat_2d[mask].flatten()
    lons = lon_2d[mask].flatten()

    precomputed[name] = {
        "lat": lats,
        "lon": lons,
        "mask_indices": np.argwhere(mask)  # Optional: can help in debugging or advanced use
    }

    print(f"✅ {name}: {len(lats)} nearby pixels found")

# === Save to File ===
with open(output_mask_file, "wb") as f:
    pickle.dump(precomputed, f)

print(f"\n💾 Precomputed masks saved to: {output_mask_file}")
