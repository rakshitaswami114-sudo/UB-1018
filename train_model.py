import pandas as pd
import random

cities = {
"Bangalore": (12.9716, 77.5946),
"Mumbai": (19.0760, 72.8777),
"Delhi": (28.6139, 77.2090)
}

shelter_types = [
"Government School",
"Community Hall",
"Sports Complex",
"Town Hall",
"Public Auditorium",
"College Campus"
]

num_shelters_per_city = 20

data = []
for city, (base_lat, base_lon) in cities.items():
    for i in range(num_shelters_per_city):
        name = f"{random.choice(shelter_types)} {i+1}"
        lat = base_lat + random.uniform(-0.05, 0.05)
        lon = base_lon + random.uniform(-0.05, 0.05)
        capacity = random.randint(150, 1000)
        data.append({
            "shelter_name": name,
            "city": city,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "capacity": capacity
            })

df = pd.DataFrame(data)
df.to_csv("../data/flood_dataset.csv", index=False)

print("✅ shelters.csv generated successfully!")