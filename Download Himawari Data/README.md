# Himawari Data Download Manager

This document provides instructions for using the collaborative download pipeline to fetch Himawari-8 Cloud Mask and Main L2 data from the JAXA FTP server.

The system is designed to be resilient and support multiple users working in parallel on different datasets.

---
## 📂 Project Structure

-   **/Download Himawari Data**:
    -   **/jaxa_download_scripts**: Contains the core downloader scripts.
        -   `run_downloader.py`: The main **Orchestrator** script. This is the only script you need to run for downloads.
        -   `jaxa_cloud_data_1.py`: The dedicated downloader for **Cloud Mask** data. It is called by the orchestrator.
        -   `JAXA_PTree.py`: The dedicated downloader for **Main L2** data. It is also called by the orchestrator.
        -   `download_progress.json`: A critical file that tracks the download progress for both data types across all years. **This file should be regularly committed to Git.**
    -   **/List of Files needed**: Contains the scripts and lists for generating the download queue.
        -   `generate_himawari_list.py`: A preparatory script that creates the master "to-do" list of files to download based on ground data.
        -   `himawari_timestamps_to_download_filtered.txt`: This is a filtered version of the master list of all timestamps that need to be downloaded.
        -   `subsample_list.py`: A script which subsamples the original master list to create a distributed and fitered version with less number of timestamps.

---
## ⚙️ Setup Instructions

### 1. Prerequisites
-   Python 3.8+
-   Git installed and configured.


### 2. Set Up the Environment
It is highly recommended to use a Python virtual environment.
```bash
# Create a virtual environment
python -m venv venv

# Activate it (on Windows PowerShell)
.\venv\Scripts\Activate

# Activate it (on macOS/Linux)
source venv/bin/activate
```

### 3. Install Dependencies
Install all required packages from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` does not exist, the first user should create it with `pip freeze > requirements.txt`)*

### 4. Configure Credentials
The download scripts require FTP credentials to access the JAXA server.
- In the project's root directory, create a file named **`.env`**.
- Add your credentials to this file as follows:
  ```
  FTP_USERNAME="your_jaxa_email@example.com"
  FTP_PWD="your_jaxa_password"
  ```
The `.gitignore` file is configured to prevent your credentials from being uploaded to GitHub.

---
## 🚀 How to Run the Download Process

### Step 1: Generate the File List (If not already done)
This step creates the master list of timestamps to download. This usually only needs to be done once.
```bash
python "Download Himawari Data/List of Files needed/generate_himawari_list.py"
```
After running above script, you need to run the following command -
```bash
python "Download Himawari Data/List of Files needed/subsample_list.py"
```
This will create the final filtered list which will be used in the project.

Note: You may not need to do this step because the list is already available on the repository.

### Step 2: Run the Orchestrator
This is the main step for downloading data. The orchestrator script handles everything automatically.

**Before you run:** Pull the latest changes from GitHub to get the most recent `download_progress.json`.
```bash
git pull
```

**Run the command:** Execute the script from the project root directory, specifying the `<year>` and `<number_of_files>` to download.
```bash
# Example: Download the next 20 pairs of files for 2019
python "Download Himawari Data/jaxa_download_scripts/run_downloader.py" 2019 20
```
The script will first check if the cloud and main data pointers are synchronized. If not, it will "catch up" the lagging dataset before starting the new batch download.

**After you run:** Push your changes to share the updated progress with your team.
```bash
git add "Download Himawari Data/jaxa_download_scripts/download_progress.json"
git commit -m "feat: Update download progress for 2019"
git push
```

---
## ⚠️ Troubleshooting Common Errors

Here are solutions to errors you or your teammates might encounter.

### 1. `FileNotFoundError`
-   **Error Message**: `FileNotFoundError: [Errno 2] No such file or directory: '../List of Files needed/...'`
-   **Cause**: You are running the script from the wrong directory.
-   **Solution**: Always run the `python ...` commands from the project's root directory.

### 2. `ModuleNotFoundError: No module named 'dotenv'`
-   **Error Message**: The script fails inside the subprocess, complaining about a missing module that you know is installed.
-   **Cause**: The script is being executed by your system's global Python, not the Python inside your virtual environment.
-   **Solution**: This has been fixed in the orchestrator script by using `sys.executable`. If it occurs, ensure your virtual environment (`venv`) is activated correctly before running the script.

### 3. `UnicodeEncodeError: 'charmap' codec can't encode character...`
-   **Error Message**: The script crashes when trying to print emoji characters (e.g., 📡, ✅).
-   **Cause**: This is a common issue on **Windows**. The default PowerShell/CMD terminal uses an old character encoding.
-   **Solution**: Before running the script, execute the following command in your PowerShell terminal. This tells Python to use the modern UTF-8 encoding.
    ```powershell
    $env:PYTHONUTF8=1
    ```
    Then run the download command as usual in the same terminal.

### 4. Command Error due to Spaces in Path
-   **Error Message**: The terminal gives an error saying it cannot find the script.
-   **Cause**: Your folder name `Download Himawari Data` contains spaces.
-   **Solution**: Wrap the entire path to the script in **double quotes (`"`)**.
    ```bash
    # Correct command
    python "Download Himawari Data/jaxa_download_scripts/run_downloader.py" 2019 10
    ```
