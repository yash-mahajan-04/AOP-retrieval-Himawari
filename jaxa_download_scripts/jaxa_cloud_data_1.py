import os
from ftplib import FTP
import xarray as xr
from datetime import datetime, timedelta

# 🔐 FTP Credentials
USERNAME = ""
PASSWORD = ""

# 📂 FTP Server
FTP_SERVER = "ftp.ptree.jaxa.jp"

# 📅 Date Range to Download
START_DATE = "2016-02-08"  # <-- Change start date here
END_DATE = "2016-02-08"    # <-- Change end date here

# ⏰ Hours to Download
HOURS = ["0500", "0530", "0600", "0630", "0700", "0730" , "0800" , "0830" , "0900"]  # <-- Change hours here if needed

# 📁 Output directory
OUTPUT_DIR = "himawari_data"

# 🌍 Region of Interest
REGION = {
    "lat_min": 17,
    "lat_max": 47,
    "lon_min": 80.24,
    "lon_max": 130
}

# 🛠️ Build remote FTP path and filename
def get_remote_path(date_obj, hour_str):
    year_month = date_obj.strftime("%Y%m")
    day = date_obj.strftime("%d")
    filename = f"NC_H08_{date_obj.strftime('%Y%m%d')}_{hour_str}_L2CLP010_FLDK.02401_02401.nc"
    remote_path = f"/pub/himawari/L2/CLP/010/{year_month}/{day}/{hour_str[:2]}/{filename}"
    return remote_path, filename

# 📡 Connect and download
def download_file(remote_path, filename):
    ftp = FTP(FTP_SERVER)
    ftp.login(USERNAME, PASSWORD)

    directory = os.path.dirname(remote_path)
    ftp.cwd(directory)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    local_filepath = os.path.join(OUTPUT_DIR, filename)

    with open(local_filepath, 'wb') as f:
        ftp.retrbinary(f"RETR {filename}", f.write)

    ftp.quit()
    print(f"✅ Downloaded {filename} to {local_filepath}")
    return local_filepath

# ✂️ Trim NetCDF file
def trim_file(local_filepath):
    ds = xr.open_dataset(local_filepath)

    try:
        ds_trimmed = ds.sel(
            latitude=slice(REGION["lat_max"], REGION["lat_min"]),
            longitude=slice(REGION["lon_min"], REGION["lon_max"])
        )

        trimmed_filepath = os.path.join(OUTPUT_DIR, f"trimmed_{os.path.basename(local_filepath)}")
        ds_trimmed.to_netcdf(trimmed_filepath, encoding={var: {"zlib": True} for var in ds_trimmed.data_vars})

        print(f"✅ Trimmed and saved to {trimmed_filepath}")
    finally:
        ds.close()
        print(f"🧹 Finished processing {local_filepath}")

# 🚀 Download and trim for a date
def download_and_trim_day(date_obj):
    downloaded_files = []
    for hour_full in HOURS:
        hour_folder = hour_full[:2]  # Extract only first 2 digits for FTP folder
        try:
            remote_path, filename = get_remote_path(date_obj, hour_full)
            local_filepath = download_file(remote_path, filename)
            downloaded_files.append(local_filepath)
            trim_file(local_filepath)
        except Exception as e:
            print(f"[!] Error downloading {hour_full}: {e}")
    return downloaded_files

# 🚀 Main function to loop over date range
def main():
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")

    current_dt = start_dt
    all_downloads = []

    while current_dt <= end_dt:
        print(f"\n📅 Processing {current_dt.date()}...")
        downloads = download_and_trim_day(current_dt)
        all_downloads.extend(downloads)
        current_dt += timedelta(days=1)

    print(f"\n✅ All done! {len(all_downloads)} files downloaded and trimmed.")

if __name__ == "__main__":
    main()
