import os
import sys
import json
from ftplib import FTP
import xarray as xr
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# 🔐 FTP Credentials
USERNAME = os.getenv("FTP_USERNAME")
PASSWORD = os.getenv("FTP_PWD")
FTP_SERVER = "ftp.ptree.jaxa.jp"

# 🔑 Pointer key for this script
POINTER_KEY = "main"

DELETE_ORIGINAL_AFTER_TRIM = True

# --- Get the absolute path to the directory where this script is located ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TIMESTAMPS_FILE = os.path.join(SCRIPT_DIR, "../List of Files needed/himawari_timestamps_to_download_filtered.txt")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "download_progress.json")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "../../TOA reflectance and Cloud/Himawari Data")

# 🌍 Region of Interest
REGION = {
    "lat_min": 17,
    "lat_max": 47,
    "lon_min": 80.24,
    "lon_max": 130
}


# --- Progress Management Functions ---
def load_progress(filepath):
    """Loads nested download progress from the JSON file."""
    if not os.path.exists(filepath):
        # Create a default nested structure if the file doesn't exist
        return {
            "2016": {"cloud": 0, "main": 0},
            "2017": {"cloud": 0, "main": 0},
            "2018": {"cloud": 0, "main": 0},
            "2019": {"cloud": 0, "main": 0}
        }
    with open(filepath, 'r') as f:
        progress = json.load(f)
    # Ensure all years and keys exist for robustness
    for year in ['2016', '2017', '2018', '2019']:
        if year not in progress:
            progress[year] = {"cloud": 0, "main": 0}
        if "main" not in progress[year]:
            progress[year]["main"] = 0
        if "cloud" not in progress[year]:
            progress[year]["cloud"] = 0
    return progress

def save_progress(filepath, progress):
    """Saves the download progress to the JSON file."""
    with open(filepath, 'w') as f:
        json.dump(progress, f, indent=4)

def load_and_split_timestamps(filepath):
    """Loads the master list of timestamps and splits them by year."""
    with open(filepath, 'r') as f:
        all_timestamps = [line.strip() for line in f if line.strip()]
    
    timestamps_by_year = {'2016': [], '2017': [], '2018': [], '2019': []}
    for ts in all_timestamps:
        year = ts[:4]
        if year in timestamps_by_year:
            timestamps_by_year[year].append(ts)
    return timestamps_by_year


# --- Core Download and Process Functions ---
def find_remote_file(ftp, date_obj, hour_str):
    """Navigates FTP and finds the filename for a given timestamp."""
    y, m, d = date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d")
    ftp_dir = f"/jma/netcdf/{y}{m}/{d}/"
    ftp.cwd(ftp_dir)
    
    all_files = ftp.nlst()
    
    # Filter for the specific file matching the hour and full-disk type
    matching_files = [
        f for f in all_files
        if f"_{hour_str}_" in f and f.endswith("06001_06001.nc")
    ]
    
    if not matching_files:
        raise FileNotFoundError(f"Could not find main data file for {date_obj.date()} {hour_str} in {ftp_dir}")
        
    return matching_files[0] # Return the found filename

def download_file(ftp, remote_filename, local_path):
    """Downloads a single file from the current FTP directory."""
    with open(local_path, 'wb') as f:
        ftp.retrbinary(f"RETR {remote_filename}", f.write)

def crop_nc_file(nc_path, output_path, delete_original=False):
    """Crops the NetCDF file and deletes the original."""
    ds = xr.open_dataset(nc_path, decode_timedelta=False)
    try:
        ds_trimmed = ds.sel(
            latitude=slice(REGION["lat_max"], REGION["lat_min"]),
            longitude=slice(REGION["lon_min"], REGION["lon_max"])
        )
        ds_trimmed.to_netcdf(output_path, encoding={var: {"zlib": True} for var in ds_trimmed.data_vars})
        print(f"✂️  Trimmed and saved to {output_path}")
    finally:
        ds.close()
    
    if delete_original:
        try:
            os.remove(nc_path)
            print(f"🗑️  Successfully deleted original file: {nc_path}")
        except OSError as e:
            print(f"❗️ Error deleting original file: {e}")


# --- Main Download Session Logic ---
def run_download_session(year_to_download, num_files_to_download, all_timestamps, progress):
    timestamps_for_year = all_timestamps.get(year_to_download)
    if not timestamps_for_year:
        print(f"❌ Error: No timestamps found for the year {year_to_download}.")
        return

    start_index = progress[year_to_download].get(POINTER_KEY, 0)
    end_index = min(start_index + num_files_to_download, len(timestamps_for_year))

    if start_index >= len(timestamps_for_year):
        print(f"🎉 All '{POINTER_KEY}' files for {year_to_download} have already been downloaded!")
        return

    print(f"\n--- Starting Download Session for '{POINTER_KEY}' data (Year {year_to_download}) ---")
    print(f"Queue: {len(timestamps_for_year)} files | Current Progress: {start_index}")
    print(f"Attempting to download {end_index - start_index} file(s).")
    
    ftp = FTP(FTP_SERVER)
    ftp.login(USERNAME, PASSWORD)

    for i in range(start_index, end_index):
        timestamp_str = timestamps_for_year[i]
        print(f"\n[{i + 1}/{len(timestamps_for_year)}] Processing: {timestamp_str}")
        
        local_temp_path = None
        try:
            date_obj = datetime.strptime(timestamp_str[:8], '%Y%m%d')
            hour_str = timestamp_str[9:]
            
            remote_filename = find_remote_file(ftp, date_obj, hour_str)
            
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            local_temp_path = os.path.join(OUTPUT_DIR, f"temp_{remote_filename}")
            trimmed_output_path = os.path.join(OUTPUT_DIR, f"trimmed_{remote_filename}")

            if os.path.exists(trimmed_output_path):
                print("⏭️  Trimmed file already exists. Skipping.")
            else:
                download_file(ftp, remote_filename, local_temp_path)
                crop_nc_file(local_temp_path, trimmed_output_path, delete_original=DELETE_ORIGINAL_AFTER_TRIM)
            
            progress[year_to_download][POINTER_KEY] = i + 1
            save_progress(PROGRESS_FILE, progress)
            print(f"💾 Progress for '{POINTER_KEY}' ({year_to_download}) saved. Next index is {progress[year_to_download][POINTER_KEY]}.")

        except Exception as e:
            print(f"❗️ ERROR on file {timestamp_str}: {e}")
            print("Stopping session. You can rerun the script to retry.")
            if local_temp_path and os.path.exists(local_temp_path):
                os.remove(local_temp_path)
            break
    
    ftp.quit()
    print("\n--- Download Session Finished ---")


# --- Script Entry Point ---
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {os.path.basename(__file__)} <year> <number_of_files>")
        print("Example: python your_main_data_script.py 2016 10")
        sys.exit(1)
        
    try:
        year = sys.argv[1]
        num_files = int(sys.argv[2])
        if year not in ['2016', '2017', '2018', '2019']:
            raise ValueError("Year must be one of 2016, 2017, 2018, or 2019.")
    except (ValueError, IndexError) as e:
        print(f"❌ Invalid arguments: {e}")
        sys.exit(1)

    all_timestamps = load_and_split_timestamps(TIMESTAMPS_FILE)
    progress_data = load_progress(PROGRESS_FILE)
    
    run_download_session(year, num_files, all_timestamps, progress_data)