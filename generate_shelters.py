import pandas as pd
import random


cities = {
    "Bangalore": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Bhopal": (23.2599, 77.4126),
    "Indore": (22.7196, 75.8577),
    "Nagpur": (21.1458, 79.0882),
    "Patna": (25.5941, 85.1376),
    "Kochi": (9.9312, 76.2673),
    "Visakhapatnam": (17.6868, 83.2185),
    "Surat": (21.1702, 72.8311),
    "Mysore": (12.2958, 76.6394),
    "Belgaum": (15.8497, 74.4977),
    "Davangere": (14.4644, 75.9218)
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
df.to_csv("shelters.csv", index=False)

print("✅ shelters.csv generated successfully!")