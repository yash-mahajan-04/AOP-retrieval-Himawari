import os
from ftplib import FTP
from datetime import datetime, timedelta
import xarray as xr
from tqdm import tqdm
import getpass

# 🔐 FTP Credentials
USERNAME = ""
PASSWORD = ""

# 📅 Date Range
START_DATE = "2016-09-12"
END_DATE = "2016-09-12"

# 📁 Output Folder
OUTPUT_DIR = "himawari_trimmed"

# 🌍 Region of Interest
REGION = {
    "lat_min": 17,
    "lat_max": 47,
    "lon_min": 80.24,
    "lon_max": 130
}

# ⏰ Timestamps to download (4-hourly)
HOURS = ["0200" , "0300" , "0400" , "0500" , "0600" , "0700"] #, "0400", "0800", "1200", "1600", "2000"

# 📡 Connect to JAXA FTP
def connect_ftp():
    ftp = FTP("ftp.ptree.jaxa.jp")
    ftp.login(USERNAME, PASSWORD)
    return ftp

# ⬇️ Download a file from FTP
def download_file(ftp, remote_path, local_path):
    with open(local_path, 'wb') as f:
        ftp.retrbinary(f"RETR " + remote_path, f.write)

# ✂️ Crop and compress NetCDF file
def crop_nc_file(nc_path, output_path):
    ds = xr.open_dataset(nc_path, decode_timedelta=True)
    try:
        lat = ds["latitude"]
        lon = ds["longitude"]

        # Create a region mask
        mask = (
            (lat >= REGION["lat_min"]) & (lat <= REGION["lat_max"]) &
            (lon >= REGION["lon_min"]) & (lon <= REGION["lon_max"])
        )

        # Apply mask to all relevant variables
        data_vars = {
            var: ds[var].where(mask, drop=True)
            for var in ds.data_vars
            if "latitude" in ds[var].dims and "longitude" in ds[var].dims
        }

        # Save subset with compression
        subset = xr.Dataset(data_vars)
        subset.to_netcdf(output_path, encoding={var: {"zlib": True} for var in subset.data_vars})

    finally:
        ds.close()
        os.remove(nc_path)

# 🛠️ Download and process data for a single day
def download_and_process_day(ftp, date):
    y, m, d = date.strftime("%Y"), date.strftime("%m"), date.strftime("%d")
    ftp_dir = f"/jma/netcdf/{y}{m}/{d}/"

    try:
        ftp.cwd(ftp_dir)
    except:
        print(f"[!] No directory for {date.date()}, skipping.")
        return

    all_files = ftp.nlst()

    # Filter: 8-hourly + full-disk files
    matching_files = [
        f for f in all_files
        if any(f"_{h}_" in f for h in HOURS) and f.endswith("06001_06001.nc")
    ]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for fname in tqdm(matching_files, desc=f"Processing {date.date()}", leave=False):
        local_temp = f"temp_{fname}"
        trimmed_output = os.path.join(OUTPUT_DIR, f"trimmed_{fname}")

        if os.path.exists(trimmed_output):
            continue

        try:
            download_file(ftp, fname, local_temp)
            crop_nc_file(local_temp, trimmed_output)
        except Exception as e:
            print(f"[!] Error with {fname}: {e}")
            if os.path.exists(local_temp):
                os.remove(local_temp)

# 🚀 Main function
def main():
    ftp = connect_ftp()
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE, "%Y-%m-%d")

    current = start
    while current <= end:
        download_and_process_day(ftp, current)
        current += timedelta(days=1)

    ftp.quit()
    print("\n✅ All done!")

if __name__ == "__main__":
    main()
