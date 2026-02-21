import pandas as pd
import numpy as np

np.random.seed(42)
rows = 300

cities = ["Bangalore", "Delhi", "Mumbai", "Hyderabad", "Chennai"]

data = pd.DataFrame({
    "city": np.random.choice(cities, rows),
    "street_name": [f"Street_{i}" for i in range(rows)],
    "latitude": np.random.uniform(12.8, 13.2, rows),
    "longitude": np.random.uniform(77.4, 77.8, rows),
    "rainfall_1h": np.random.uniform(0, 60, rows),
    "rainfall_3h": np.random.uniform(0, 150, rows),
    "rainfall_6h": np.random.uniform(0, 250, rows),
    "elevation": np.random.uniform(5, 100, rows),
    "drainage_capacity": np.random.uniform(0.2, 1.0, rows),
    "past_floods": np.random.randint(0, 6, rows),
    "soil_moisture": np.random.uniform(0.2, 0.9, rows),
})

data["flood_label"] = np.where(
    (data["rainfall_3h"] > 100) &
    (data["elevation"] < 30) &
    (data["drainage_capacity"] < 0.4) &
    (data["soil_moisture"] > 0.6),
    1,
    0
)

data.to_csv("flood_dataset.csv", index=False)

print("Flood dataset recreated successfully.")