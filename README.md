# Machine Learning for Aerosol Optical Property Retrieval from Geostationary Satellites 🛰️

Currently, this project serves as an end-to-end data processing pipeline designed to collocate Himawari satellite observations with ground-based AERONET aerosol measurements. It automates the entire workflow, from processing raw data files to generating a final, unified dataset ready for analysis and machine learning applications.

The master script, **`run_pipeline.py`**, executes all necessary steps in the correct sequence.

---

## The Workflow

The pipeline consists of four main stages, each handled by a dedicated script. The `run_pipeline.py` script manages the execution of this entire workflow.

****

1.  **Ground Data Consolidation** (`aeronet_v3.py`)
    * **Input**: Raw AERONET data files for Aerosol Optical Depth (AOD) and Fine Mode Fraction (FMF) from multiple stations.
    * **Process**: Reads, cleans, and merges all ground-based measurements into a single, time-indexed master file.
    * **Output**: `AERONET_groundtruth_ALL.csv`

2.  **Satellite Pixel Pre-computation** (`precompute_station_masks.py`)
    * **Input**: A reference satellite data file (for its coordinate grid) and a list of ground station coordinates.
    * **Process**: Calculates and saves the indices of all satellite pixels that are within a specified radius of each ground station. This is a one-time optimization step.
    * **Output**: `precomputed_masks.pkl`

3.  **Cloud-Free Satellite Data Extraction** (`main_v3.py`)
    * **Input**: The pre-computed pixel masks, raw satellite data files, and their corresponding cloud mask files.
    * **Process**: For each satellite observation, it uses the pre-computed masks to efficiently find nearby pixels, filters out any that are cloudy, and extracts the relevant data (reflectance, brightness temperature, etc.).
    * **Output**: A folder of timestamped CSV files (`toa_filtered_near_stations/`).

4.  **Spatio-Temporal Matching** (`datetime_latlon_v5.py`)
    * **Input**: The filtered satellite data CSVs and the consolidated ground truth file.
    * **Process**: For each satellite observation, it searches for ground measurements at the same station within a specific time window (e.g., +/- 30 minutes). It then aggregates both datasets to create a final, matched data point.
    * **Output**: `Final_Matched_Data.csv`

---

## Requirements


You can install all of the requirements using pip:
```bash
pip install requirements.txt
```

---

## Project Directory Structure

To run the pipeline, your project must be organized in the following structure. **Raw data must be placed in the designated input folders.**

```
📁 Project_Root/
│
├── 📜 run_pipeline.py                 (MASTER SCRIPT - RUN THIS FILE)
│
├── 📁 Aeronet Merging AOD FMF/
│   ├── 📜 aeronet_v3.py
│   ├── 📁 AOD/                        (RAW INPUT: Place AOD files here such that each station's file is inside a dedicated folder with the same folder name as the file)
│   ├── 📁 FMF/                        (RAW INPUT: Same as AOD)
│   └── 📁 Merged Ground Truth/        (Intermediate Output 1)
│       └── AERONET_groundtruth_ALL.csv
│
├── 📁 Pixels Close To Stations/
│   ├── 📜 precompute_station_masks.py
|   ├── 📜 verify.py
│   └── 📜 precomputed_masks.pkl      (Intermediate Output 2)
│
├── 📁 TOA reflectance and Cloud/
│   ├── 📜 main_v3.py
│   ├── 📁 Himawari Data/              (RAW INPUT: Place satellite .nc files here)
│   ├── 📁 Cloud Mask Data/            (RAW INPUT: Place cloud mask .nc files here)
│   └── 📁 toa_filtered_near_stations/ (Intermediate Output 3)
│
├── 📁 Spatial Temporal Matching/
│   └── 📜 datetime_latlon_v5.py
│
└── 📜 Final_Matched_Data.csv          (FINAL OUTPUT)
```

---

## How to Run the Full Pipeline

1.  **Setup Folders**: Create the directory structure exactly as shown above.
2.  **Place Raw Data**: Populate the four **RAW INPUT** folders with your data files: `AOD/`, `FMF/`, `Himawari Data/`, and `Cloud Mask Data/`.
3.  **Check Configuration**: Briefly check the configuration variables (e.g., file paths, station coordinates) inside each of the individual scripts to ensure they match your data.
4.  **Execute**: Navigate to the `Project_Root` directory in your terminal and run the master script:
    ```bash
    python run_pipeline.py
    ```
This single command will execute all four stages of the pipeline in order. The script will print the progress of each stage.

---

## Final Output File Format ✅

The pipeline generates a single file, **`Final_Matched_Data.csv`**, in the project root. Each row represents a successful collocation between a satellite overpass and ground measurements.

| Column                | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `Datetime_sat`        | The timestamp of the satellite observation.                                 |
| `Station`             | The name of the ground station where the match occurred.                    |
| `rho_01` to `rho_06`  | **Averaged** Top-of-Atmosphere (TOA) reflectance for bands 1-6.             |
| `bt_07` to `bt_16`    | **Averaged** brightness temperature (in Kelvin) for bands 7-16.             |
| `SOZ`, `VZ`, `RA`     | **Averaged** Solar Zenith, Viewing Zenith, and Relative Azimuth angles.     |
| `latitude`, `longitude` | **Averaged** coordinates of the satellite pixels used in the match.         |
| `AOD_ground_mean`     | **Averaged** Aerosol Optical Depth from ground measurements.                |
| `AE_ground_mean`      | **Averaged** Angstrom Exponent from ground measurements.                    |
| `FMF_ground_mean`     | **Averaged** Fine Mode Fraction from ground measurements.                   |
| `num_ground_matches`  | The number of ground measurements that were averaged for the match.         |
