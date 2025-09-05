# Satellite Pixel Mask Pre-computation

This project provides a Python script, `precompute_station_masks.py`, to efficiently identify and save the coordinates of satellite data pixels that are located near a list of ground-based monitoring stations.

This pre-computation step is designed to optimize data analysis workflows by avoiding the need to repeatedly perform expensive distance calculations. The output is a single, compact file that maps each ground station to its nearby satellite pixels, ready for quick lookups in other programs.

---

## How It Works 🛰️

The main script (`precompute_station_masks.py`) performs the following steps:

1.  **Load Data**: It loads the latitude and longitude grid from a specified satellite data file (e.g., a Himawari NetCDF file).
2.  **Calculate Distances**: For each ground station in a predefined list, it uses the **Haversine formula** to calculate the great-circle distance from the station to every single pixel in the satellite grid. .
3.  **Create Masks**: It creates a boolean "mask" to identify all pixels that fall within a configurable distance threshold (e.g., within 2 km) of each station.
4.  **Extract Coordinates**: The script extracts the latitude and longitude coordinates of all the identified nearby pixels for each station.
5.  **Save Output**: All the extracted coordinate data is saved into a single binary file named `precomputed_masks.pkl` using Python's `pickle` module. This file allows for extremely fast loading of the pre-computed data in other analyses.

---

## Requirements

You'll need Python 3 and the following libraries to run the script.

-   `xarray` (to read NetCDF files)
-   `numpy`
-   `pandas`

You can install them using pip:
```bash
pip install xarray numpy pandas
```

---

## Setup and Usage

Follow these steps to generate your pre-computed mask file.

### 1. File Placement

Place your satellite NetCDF data file in the location expected by the script. According to the default configuration, this is:
`../TOA reflectance and Cloud/Himawari Data/trimmed_NC_H08_20191202_0200_R21_FLDK.06001_06001.nc`

### 2. Configuration

Open `precompute_station_masks.py` and modify the variables in the "Settings" section if needed:
-   `max_distance_km`: The search radius around each station in kilometers.
-   `himawari_nc_path`: The path to your input satellite data file.
-   `output_mask_file`: The name of the output pickle file.
-   `station_coords`: You can add, remove, or modify the ground stations in this dictionary.

### 3. Run the Script

Execute the script from your terminal:
```bash
python precompute_station_masks.py
```
The script will print the progress for each station and save the `precompute_masks.pkl` file in the same directory upon completion.

---

## Output File

The script generates a single file, `precomputed_masks.pkl`, which is a pickled Python dictionary with the following structure:
```bash
{
    "_grid_shape": (6001, 6001),  # The shape of the original satellite grid
    "Chiayi": {
        "lat": [23.45, 23.46, ...],
        "lon": [120.25, 120.26, ...],
        "mask_indices": [[row1, col1], [row2, col2], ...]
    },
    "Kanpur": {
        # ... same structure
    },
    # ... other stations
}
```

---

## Verify the Output ✅

A utility script, `verify.py`, is included to help you quickly inspect the contents of the generated `precomputed_masks.pkl` file.

Simply run it from your terminal:
```bash
python verify.py
```
It will print a list of the stations found in the file, the shape of the grid used for the computation, and a sample of the data for one station to confirm that the output is valid.