import subprocess

scripts = [
    # "Aeronet Merging AOD FMF/aeronet_v3.py",
    "TOA reflectance and Cloud/main_v3.py",
    "Spatial Temporal Matching/datetime_latlon_v5.py",
]

for script in scripts:
    print(f"\n🔄 Running: {script}")

    result = subprocess.run(["python",script])

    if result.returncode!=0:
        print(f"❌ Error in {script}:\n{result.stderr}")
        break
    else:
        print(f"✅ Completed: {script}\n{result.stdout}")