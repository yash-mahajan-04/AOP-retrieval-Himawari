import pickle

with open("precomputed_masks.pkl", "rb") as f:
    data = pickle.load(f)

print("Available stations:", list(data.keys()))  # Exclude _grid_shape
print("Grid shape used:", data["_grid_shape"])

# Check one station
kanpur = data["Kanpur"]
print(f"Kanpur: {len(kanpur['lat'])} lat/lon pairs")
print("Sample lat/lon:", list(zip(kanpur["lat"], kanpur["lon"]))[:5])
