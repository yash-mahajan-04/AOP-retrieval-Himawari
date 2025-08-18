import os
import sys
import json
import subprocess

# This script assumes it is in the same directory as the downloaders.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CLOUD_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "jaxa_cloud_data_1.py")
MAIN_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "JAXA_PTree.py")

PROGRESS_FILE = os.path.join(SCRIPT_DIR, "download_progress.json")


# --- Progress Management Function ---
def load_progress(filepath):
    """Loads and validates the nested download progress from the JSON file."""
    if not os.path.exists(filepath):
        print("Progress file not found. Please run one of the download scripts once to create it.")
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

# --- Main Orchestrator Logic ---
def run_orchestrator(year, batch_size):
    """
    Manages the download process by synchronizing and then batch-downloading
    both cloud and main data files.
    """
    print("--- 🚀 Starting Download Orchestrator ---")

    # --- 1. Catch-up Phase ---
    print("\n--- 🔍 Phase 1: Checking and Synchronizing Pointers ---")
    
    while True:
        progress = load_progress(PROGRESS_FILE)
        if not progress: return

        cloud_ptr = progress[year].get("cloud", 0)
        main_ptr = progress[year].get("main", 0)

        if cloud_ptr == main_ptr:
            print(f"✅ Pointers are synchronized for {year} at index {cloud_ptr}.")
            break

        if cloud_ptr < main_ptr:
            print(f"🟡 Cloud data is behind by {main_ptr - cloud_ptr} file(s). Catching up...")
            script_to_run = CLOUD_SCRIPT_PATH
            lagging_type = "Cloud"
        else:
            print(f"🟡 Main data is behind by {cloud_ptr - main_ptr} file(s). Catching up...")
            script_to_run = MAIN_SCRIPT_PATH
            lagging_type = "Main"
            
        # Construct the full, quoted path for the command
        command_path = f'"{script_to_run}"'

        print(f"Executing: {os.path.basename(sys.executable)} {os.path.basename(script_to_run)} {year} 1")
        
        result = subprocess.run([sys.executable, script_to_run, year, "1"], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ ERROR while running {lagging_type} script to catch up.")
            print(result.stderr)
            return
    
    # --- 2. Batch Download Phase ---
    print(f"\n--- 🔄 Phase 2: Starting Batch Download for {batch_size} Pairs ---")
    
    current_progress = load_progress(PROGRESS_FILE)[year]['cloud'] # Get latest progress
    
    for i in range(batch_size):
        print(f"\n--- Downloading Pair {i + 1}/{batch_size} (Index {current_progress + i}) ---")

        print("Downloading Cloud Data...")
        result_cloud = subprocess.run([sys.executable, CLOUD_SCRIPT_PATH, year, "1"], capture_output=True, text=True)
        if result_cloud.returncode != 0:
            print("❌ ERROR downloading cloud file. Stopping batch.")
            print(result_cloud.stderr)
            return
            
        print("Downloading Main Data...")
        result_main = subprocess.run([sys.executable, MAIN_SCRIPT_PATH, year, "1"], capture_output=True, text=True)
        if result_main.returncode != 0:
            print("❌ ERROR downloading main data file. Stopping batch.")
            print(result_main.stderr)
            return

    print("\n--- ✅ Batch Download Session Finished Successfully! ---")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {os.path.basename(__file__)} <year> <batch_size>")
        print("Example: python run_downloader.py 2017 10")
        sys.exit(1)
        
    try:
        target_year = sys.argv[1]
        target_batch_size = int(sys.argv[2])
        if target_year not in ['2016', '2017', '2018', '2019']:
            raise ValueError("Year must be one of 2016, 2017, 2018, or 2019.")
    except (ValueError, IndexError) as e:
        print(f"❌ Invalid arguments: {e}")
        sys.exit(1)

    run_orchestrator(target_year, target_batch_size)