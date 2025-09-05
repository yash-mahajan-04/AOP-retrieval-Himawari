# AERONET Data Processing and Merging Script

This Python script (`aeronet_v3.py`) is designed to automate the processing of aerosol data from the AERONET (AErosol RObotic NETwork). It reads raw data files for Aerosol Optical Depth (AOD) and Fine Mode Fraction (FMF), cleans them, merges them based on timestamps, and consolidates the data from multiple ground stations into a single, analysis-ready CSV file.

---

## Features

-   **Automated Header Detection**: Dynamically locates the data table within AERONET text files, ignoring metadata headers.
-   **Robust Data Loading**: Parses and cleans key variables: AOD at 500nm, Angstrom Exponent (440-870nm), and Fine Mode Fraction (FMF) at 500nm.
-   **Intelligent Timestamp Parsing**: Correctly creates `datetime` objects from date and time columns, with a fallback mechanism for different file formats (e.g., text vs. Excel-style dates).
-   **Time-based Merging**: Precisely merges AOD and FMF data for each station using an inner join on the common `datetime` column.
-   **Data Cleaning & Validation**: Automatically removes rows with missing data and filters out physically impossible negative values for AOD, AE, and FMF.
-   **Geolocation & Station Identification**: Enriches the final dataset by adding the latitude, longitude, and name for each station from a predefined dictionary.
-   **Consolidated Output**: Processes all specified station folders and combines their data into a single master CSV file for easy analysis.

---

## Requirements

Before running the script, make sure you have the following installed:
-   Python 3.x
-   Pandas library
-   NumPy library

You can install the required libraries using pip:
```bash
pip install pandas numpy
```

Project Structure for this code is expected to be as follows:
```
📁 Aeronet Merging AOD FMF/
│
├── 📜 aeronet_v3.py
│
├── 📁 AOD/
│   ├── 📁 YYYYMMDD_YYYYMMDD_StationName1/
│   │   └── YYYYMMDD_YYYYMMDD_StationName1.lev20
│   ├── 📁 YYYYMMDD_YYYYMMDD_StationName2/
│   │   └── YYYYMMDD_YYYYMMDD_StationName2.lev20
│   └── ...
│
└── 📁 FMF/
    ├── 📁 YYYYMMDD_YYYYMMDD_StationName1/
    │   └── YYYYMMDD_YYYYMMDD_StationName1.ONEILL_lev20
    ├── 📁 YYYYMMDD_YYYYMMDD_StationName2/
    │   └── YYYYMMDD_YYYYMMDD_StationName2.ONEILL_lev20
    └── ...
```

---

## Usage
1. **Organize Files**: Arrange your AERONET .lev20 (AOD) and .ONEILL_lev20 (FMF/SDA) files according to the Directory Structure shown above.

2. **Update Station Coordinates**: If you are processing data from stations not already listed in the station_coords dictionary within the script, you must add them. The script extracts the station name from the folder name (e.g., Chiayi from 1_Taiwan_Chiayi).

3. **Run the Script**: Open a terminal or command prompt, navigate to the project folder, and execute the script:

```bash
python aeronet_v3.py
```
4. **Check the Output**: The script will create a new directory named Merged Ground Truth. Inside this folder, you will find the final consolidated file: AERONET_groundtruth_ALL.csv.

---
## Output File Format

The output file `AERONET_groundtruth_ALL.csv` will contain the following columns:

| Column      | Description                                                | Example        |
|-------------|------------------------------------------------------------|----------------|
| `datetime`    | The precise UTC timestamp of the measurement.              | `2021-01-15 02:30:00` |
| `AOD`         | Aerosol Optical Depth measured at 500nm.                   | `0.452`        |
| `AE`          | Angstrom Exponent calculated between 440nm and 870nm.      | `1.21`         |
| `Date`        | The original date string from the source file.             | `15:01:2021`   |
| `Time`        | The original time string from the source file.             | `02:30:00`     |
| `FMF`         | Fine Mode Fraction of AOD at 500nm.                        | `0.85`         |
| `latitude`    | Latitude of the AERONET station in decimal degrees.        | `23.452`       |
| `longitude`   | Longitude of the AERONET station in decimal degrees.       | `120.255`      |
| `station`     | The name of the AERONET station.                           | `Chiayi`       |