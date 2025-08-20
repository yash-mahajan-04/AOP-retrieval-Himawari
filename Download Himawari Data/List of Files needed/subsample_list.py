# The original, large list of 120k timestamps.
ORIGINAL_FILE = "himawari_timestamps_to_download.txt" 

# The new, smaller file that will be created.
OUTPUT_FILE = "himawari_timestamps_to_download_filtered.txt"

# The interval for sub-sampling (e.g., 5 means take every 5th file).
SAMPLING_INTERVAL = 5

# --- Main Script ---
try:
    print(f"📖 Reading from '{ORIGINAL_FILE}'...")
    with open(ORIGINAL_FILE, 'r') as f:
        all_timestamps = [line.strip() for line in f if line.strip()]
    
    print(f"Original number of timestamps: {len(all_timestamps)}")

    # Use list slicing to select every Nth item from the list.
    subsampled_timestamps = all_timestamps[::SAMPLING_INTERVAL]
    
    print(f"📉 Sub-sampling every {SAMPLING_INTERVAL}th timestamp...")
    print(f"New number of timestamps: {len(subsampled_timestamps)}")

    # Write the new, smaller list to the output file.
    with open(OUTPUT_FILE, 'w') as f:
        for ts in subsampled_timestamps:
            f.write(f"{ts}\n")
            
    print(f"✅ Successfully created '{OUTPUT_FILE}' with {len(subsampled_timestamps)} timestamps.")

except FileNotFoundError:
    print(f"❌ ERROR: The input file '{ORIGINAL_FILE}' was not found. Please check the filename.")