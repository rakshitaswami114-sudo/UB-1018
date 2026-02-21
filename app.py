import streamlit as st
import pandas as pd
import joblib
import folium
import json
from streamlit_folium import st_folium
import datetime
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ---------------------------
# PAGE CONFIG (MUST BE FIRST)
# ---------------------------
st.set_page_config(layout="wide")

# ---------------------------
# Custom Styling
# ---------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Header
# ---------------------------
st.markdown("""
<h1 style='text-align: center; color: #1f4e79;'>
Hyperlocal AI Flood Risk System
</h1>
""", unsafe_allow_html=True)

st.markdown("### 🌧 Real-Time Street-Level Flood Intelligence")
st.markdown("**Model Version:** v1.0.0")
st.markdown("---")

# ---------------------------
# Load Model & Data
# ---------------------------
model = joblib.load("model/flood_model.pkl")
df = pd.read_csv("data/flood_dataset.csv")

# ---------------------------
# SIDEBAR NAVIGATION
# ---------------------------
st.sidebar.title("🌊 Navigation")

page = st.sidebar.radio(
    "Go To",
    [
        "📊 Dashboard",
        "🆘 Help & Evacuation",
        "🏠 Shelter Locations",
        "🛣 Safe Routes",
        "🚑 Emergency Services"
    ]
)

st.sidebar.markdown("---")

offline_mode = st.sidebar.checkbox("Enable Offline Survival Mode")

time_horizon = st.sidebar.selectbox(
    "Prediction Horizon",
    ["1 Hour", "3 Hours", "6 Hours"]
)
# ---------------------------
# 🌧 Live Rainfall Simulation
# ---------------------------
st.sidebar.markdown("### 🌧 Live Rainfall Simulation")

rainfall_1h_input = st.sidebar.slider(
    "Rainfall (1 Hour) mm",
    0, 200, 20
)

rainfall_3h_input = st.sidebar.slider(
    "Rainfall (3 Hours) mm",
    0, 300, 50
)

rainfall_6h_input = st.sidebar.slider(
    "Rainfall (6 Hours) mm",
    0, 500, 80
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Risk Legend")
st.sidebar.markdown("🟢 Monitor")
st.sidebar.markdown("🟠 Prepare")
st.sidebar.markdown("🔴 Evacuate")


# =====================================================
# 📊 DASHBOARD PAGE
# =====================================================
if page == "📊 Dashboard":

    m = folium.Map(
        location=[df.latitude.mean(), df.longitude.mean()],
        zoom_start=13
    )

    df_sim = df.copy()

    # Override rainfall dynamically
    df_sim["rainfall_1h"] = rainfall_1h_input
    df_sim["rainfall_3h"] = rainfall_3h_input
    df_sim["rainfall_6h"] = rainfall_6h_input

    feature_cols = [
        "rainfall_1h",
        "rainfall_3h",
        "rainfall_6h",
        "elevation",
        "drainage_capacity",
        "past_floods",
        "soil_moisture"
    ]

    df_sim["probability"] = model.predict_proba(
        df_sim[feature_cols]
    )[:, 1]

    # 🔥 Percentile thresholds (always 3 colors)
    low_threshold = df_sim["probability"].quantile(0.33)
    high_threshold = df_sim["probability"].quantile(0.66)

    high_risk = 0
    medium_risk = 0
    low_risk = 0

    predictions = []

    for _, row in df_sim.iterrows():

        prob = row["probability"]

        if prob <= low_threshold:
            color = "green"
            action = "Monitor"
            low_risk += 1

        elif prob <= high_threshold:
            color = "orange"
            action = "Prepare"
            medium_risk += 1

        else:
            color = "red"
            action = "Evacuate"
            high_risk += 1

        predictions.append({
            "street": row["street_name"],
            "probability": float(prob),
            "action": action
        })

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=7,
            popup=f"""
            <b>Street:</b> {row['street_name']}<br>
            <b>Probability:</b> {round(prob,2)}<br>
            <b>Action:</b> {action}
            """,
            color=color,
            fill=True,
            fill_opacity=0.8
        ).add_to(m)

    # KPI DISPLAY
    col1, col2, col3 = st.columns(3)

    col1.metric("🔴 High Risk Streets", high_risk)
    col2.metric("🟠 Medium Risk Streets", medium_risk)
    col3.metric("🟢 Low Risk Streets", low_risk)

    st.markdown("---")
    st.subheader("🌍 Street-Level Risk Map")
    st_folium(m, width=1200, height=600)

    # ---------------------------
    # Active Alerts
    # ---------------------------
    st.markdown("## 🚨 Active Alerts")

    alerts_found = False
    for item in predictions:
        if item["probability"] > 0.6:
            alerts_found = True
            st.error(f"{item['street']} — Immediate Evacuation Recommended")

    if not alerts_found:
        st.success("No critical alerts at this time.")

    # ---------------------------
    # Save Offline Cache
    # ---------------------------
    offline_data = {
        "timestamp": str(datetime.datetime.now()),
        "predictions": predictions
    }

    with open("offline_cache.json", "w") as f:
        json.dump(offline_data, f)

    # ---------------------------
    # OFFLINE MODE
    # ---------------------------
    if offline_mode:
        st.markdown("---")
        st.subheader("📴 Offline Survival Mode Active")

        try:
            with open("offline_cache.json", "r") as f:
                cached = json.load(f)

            st.write("Cached Data Timestamp:", cached["timestamp"])

            for item in cached["predictions"]:
                if item["probability"] > 0.6:
                    st.error(f"🚨 SMS ALERT SENT: Evacuate {item['street']} within 2 hours.")

        except:
            st.warning("No offline cache available yet.")

    # ---------------------------
    # Safety Instructions
    # ---------------------------
    st.markdown("---")
    st.subheader("🛟 Safety Instructions")

    safety_guides = {
        "Monitor": "Stay alert. Monitor rainfall updates.",
        "Prepare": "Move valuables to higher areas.",
        "Evacuate": "Proceed to nearest shelter immediately."
    }

    selected_action = st.selectbox(
        "Select Situation",
        ["Monitor", "Prepare", "Evacuate"]
    )

    st.info(safety_guides[selected_action])

    # ---------------------------
    # Model Explainability
    # ---------------------------
    st.markdown("---")
    st.subheader("🔍 Model Risk Drivers")

    importances = model.feature_importances_

    feature_names = [
        "Rainfall (1 Hour)",
        "Rainfall (3 Hours)",
        "Rainfall (6 Hours)",
        "Elevation",
        "Drainage Capacity",
        "Past Flood History",
        "Soil Moisture"
    ]

    importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance Score": importances
    }).sort_values(by="Importance Score", ascending=False)

    st.bar_chart(importance_df.set_index("Feature"))

# =====================================================
# 🆘 HELP PAGE
# =====================================================
elif page == "🆘 Help & Evacuation":

    st.header("🆘 Emergency Help & Evacuation Guide")

    st.subheader("🏠 Shelter Homes")
    st.info("""
    • City High School Shelter  
    • Community Hall  
    • District Sports Complex
    """)

    st.subheader("🛣 Safe Roads")
    st.success("""
    • Ring Road Elevated Section  
    • Highway Bypass Route
    """)

    st.subheader("🚍 Evacuation Transport")
    st.write("""
    • Government buses every 30 minutes  
    • Emergency pickup points at main junctions
    """)

    st.subheader("☎ Emergency Contacts")
    st.write("""
    Police: 100  
    Ambulance: 108  
    Disaster Control: 112
    """)
# =====================================================
# 🏠 SHELTER PAGE
# =====================================================
elif page == "🏠 Shelter Locations":

    st.header("🏠 Find Nearby Shelter")

    shelters_df = pd.read_csv("data/shelters.csv")

    # -------------------------
    # Major Cities List
    # -------------------------
    major_cities = [
        "Bangalore",
        "Mumbai",
        "Delhi",
        "Chennai",
        "Hyderabad",
        "Kolkata",
        "Pune",
        "Ahmedabad",
        "Jaipur",
        "Lucknow",
        "Bhopal",
        "Indore",
        "Nagpur",
        "Patna",
        "Kochi",
        "Visakhapatnam",
        "Surat",
        "Mysore",
        "Belgaum",
        "Davangere"
    ]

    # -------------------------
    # Location Mode
    # -------------------------
    # -------------------------
    # Location Mode
    # -------------------------
    location_mode = st.radio(
        "Choose Location Mode",
        ["Select City & Area", "Select City Only"]
    )
    
    # -------------------------
    # Area Centers (Preloaded Offline)
    # -------------------------
    area_centers = {

    "Bangalore": {
        "MG Road": (12.9756, 77.6050),
        "Whitefield": (12.9698, 77.7499),
        "Jayanagar": (12.9250, 77.5938),
        "Electronic City": (12.8456, 77.6603),
        "Indiranagar": (12.9719, 77.6412),
        "Koramangala": (12.9352, 77.6245),
        "Hebbal": (13.0358, 77.5970),
        "Yelahanka": (13.1007, 77.5963),
        "Rajajinagar": (12.9915, 77.5563),
        "Marathahalli": (12.9569, 77.7011)
    },

    "Mumbai": {
        "Andheri": (19.1136, 72.8697),
        "Bandra": (19.0596, 72.8295),
        "Dadar": (19.0183, 72.8424),
        "Colaba": (18.9067, 72.8147),
        "Borivali": (19.2290, 72.8570),
        "Kurla": (19.0728, 72.8826),
        "Powai": (19.1176, 72.9060),
        "Ghatkopar": (19.0850, 72.9080),
        "Vashi": (19.0760, 72.9986),
        "Chembur": (19.0522, 72.9005)
    },

    "Delhi": {
        "Connaught Place": (28.6315, 77.2167),
        "Dwarka": (28.5921, 77.0460),
        "Rohini": (28.7041, 77.1025),
        "Saket": (28.5245, 77.2066),
        "Karol Bagh": (28.6510, 77.1907),
        "Lajpat Nagar": (28.5677, 77.2436),
        "Janakpuri": (28.6219, 77.0878),
        "Pitampura": (28.7034, 77.1310),
        "Chandni Chowk": (28.6562, 77.2304),
        "Mayur Vihar": (28.6044, 77.2945)
    },

    "Chennai": {
        "T Nagar": (13.0418, 80.2341),
        "Adyar": (13.0067, 80.2572),
        "Velachery": (12.9791, 80.2186),
        "Anna Nagar": (13.0846, 80.2101),
        "Tambaram": (12.9249, 80.1275),
        "Guindy": (13.0067, 80.2206),
        "Porur": (13.0352, 80.1582),
        "Chromepet": (12.9516, 80.1462),
        "Egmore": (13.0722, 80.2609),
        "Mylapore": (13.0339, 80.2619)
    },

    "Hyderabad": {
        "Banjara Hills": (17.4126, 78.4482),
        "Gachibowli": (17.4401, 78.3489),
        "Hitech City": (17.4435, 78.3772),
        "Madhapur": (17.4483, 78.3915),
        "Secunderabad": (17.4399, 78.4983),
        "Kukatpally": (17.4948, 78.3996),
        "Ameerpet": (17.4375, 78.4483),
        "Uppal": (17.4058, 78.5591),
        "Mehdipatnam": (17.3950, 78.4420),
        "LB Nagar": (17.3457, 78.5522)
    },

    "Kolkata": {
        "Salt Lake": (22.5867, 88.4170),
        "Park Street": (22.5536, 88.3529),
        "Howrah": (22.5958, 88.2636),
        "New Town": (22.5752, 88.4796),
        "Dum Dum": (22.6246, 88.4294),
        "Garia": (22.4643, 88.3930),
        "Ballygunge": (22.5230, 88.3650),
        "Behala": (22.4989, 88.3197),
        "Tollygunge": (22.5016, 88.3459),
        "Esplanade": (22.5656, 88.3529)
    },

    "Pune": {
        "Shivaji Nagar": (18.5308, 73.8475),
        "Hinjewadi": (18.5910, 73.7389),
        "Kothrud": (18.5074, 73.8077),
        "Wakad": (18.5983, 73.7637),
        "Baner": (18.5590, 73.7868),
        "Hadapsar": (18.5089, 73.9260),
        "Viman Nagar": (18.5679, 73.9143),
        "Aundh": (18.5586, 73.8070),
        "Kharadi": (18.5510, 73.9474),
        "Swargate": (18.5008, 73.8586)
    },

    "Ahmedabad": {
        "Navrangpura": (23.0330, 72.5560),
        "Maninagar": (22.9997, 72.6000),
        "Satellite": (23.0272, 72.5086),
        "Bopal": (23.0340, 72.4650),
        "Vastrapur": (23.0395, 72.5296),
        "Chandkheda": (23.1090, 72.5907),
        "Thaltej": (23.0480, 72.5150),
        "Gota": (23.0910, 72.5330),
        "Naroda": (23.0700, 72.6700),
        "Ellis Bridge": (23.0260, 72.5670)
    },
    
    
    "Jaipur": {
        "Malviya Nagar": (26.8467, 75.8050),
        "Vaishali Nagar": (26.9110, 75.7410),
        "Mansarovar": (26.8500, 75.7650),
        "C-Scheme": (26.9140, 75.8040),
        "Bani Park": (26.9280, 75.7900),
        "Sanganer": (26.8206, 75.7880),
        "Jagatpura": (26.8550, 75.8400),
        "Adarsh Nagar": (26.9020, 75.8350),
        "Tonk Road": (26.8400, 75.8050),
        "Amer": (26.9855, 75.8513)
    },
    "Lucknow": {
        "Hazratganj": (26.8467, 80.9462),
        "Alambagh": (26.8206, 80.9060),
        "Gomti Nagar": (26.8500, 81.0000),
        "Indira Nagar": (26.8800, 80.9900),
        "Aliganj": (26.8900, 80.9400),
        "Chinhat": (26.8700, 81.0500),
        "Aminabad": (26.8506, 80.9270),
        "Rajajipuram": (26.8400, 80.8800),
        "Mahanagar": (26.8800, 80.9500),
        "Charbagh": (26.8315, 80.9200)
    },

    "Bhopal": {
        "MP Nagar": (23.2330, 77.4326),
        "Arera Colony": (23.2100, 77.4300),
        "Kolar Road": (23.1660, 77.4000),
        "Bairagarh": (23.2700, 77.3500),
        "Habibganj": (23.2300, 77.4400),
        "Shahpura": (23.2000, 77.4500),
        "Govindpura": (23.2500, 77.4500),
        "Kohefiza": (23.2700, 77.3800),
        "Ayodhya Nagar": (23.2800, 77.4800),
        "TT Nagar": (23.2400, 77.4100)
    },

    "Indore": {
        "Vijay Nagar": (22.7530, 75.8937),
        "Rajwada": (22.7196, 75.8577),
        "Palasia": (22.7300, 75.8800),
        "Sudama Nagar": (22.7000, 75.8200),
        "Bhawarkua": (22.6900, 75.8700),
        "Annapurna": (22.7100, 75.8300),
        "Rau": (22.6300, 75.8000),
        "MR 10": (22.7600, 75.8900),
        "Aerodrome Road": (22.7200, 75.8200),
        "Scheme 78": (22.7400, 75.9000)
    },

    "Nagpur": {
        "Sitabuldi": (21.1458, 79.0882),
        "Dharampeth": (21.1500, 79.0600),
        "Manish Nagar": (21.1000, 79.0800),
        "Sadar": (21.1600, 79.0800),
        "Wardha Road": (21.0900, 79.0500),
        "Hingna": (21.1200, 78.9800),
        "Kamptee": (21.2300, 79.1900),
        "Mankapur": (21.1700, 79.0500),
        "Trimurti Nagar": (21.1200, 79.0900),
        "Jaripatka": (21.1700, 79.1100)
    },

    "Patna": {
        "Boring Road": (25.6100, 85.1200),
        "Kankarbagh": (25.6000, 85.1600),
        "Rajendra Nagar": (25.6100, 85.1500),
        "Danapur": (25.6300, 85.0400),
        "Bailey Road": (25.6200, 85.1000),
        "Ashok Rajpath": (25.6200, 85.1700),
        "Patliputra": (25.6200, 85.0900),
        "Phulwari Sharif": (25.5900, 85.0900),
        "Gandhi Maidan": (25.6206, 85.1440),
        "Agam Kuan": (25.6200, 85.2000)
    },

    "Kochi": {
        "Fort Kochi": (9.9650, 76.2425),
        "Edappally": (10.0270, 76.3080),
        "Kakkanad": (10.0159, 76.3419),
        "Vyttila": (9.9670, 76.3210),
        "Aluva": (10.1076, 76.3516),
        "Thrippunithura": (9.9480, 76.3490),
        "Marine Drive": (9.9816, 76.2773),
        "Palarivattom": (9.9980, 76.3070),
        "Mattancherry": (9.9570, 76.2590),
        "Kaloor": (9.9985, 76.2910)
    },

    "Visakhapatnam": {
        "RK Beach": (17.7100, 83.3200),
        "MVP Colony": (17.7400, 83.3400),
        "Gajuwaka": (17.6900, 83.2000),
        "Dwaraka Nagar": (17.7300, 83.3000),
        "Madhurawada": (17.8000, 83.3600),
        "Seethammadhara": (17.7500, 83.3100),
        "Simhachalam": (17.7700, 83.2500),
        "Anakapalle": (17.6900, 83.0100),
        "Pendurthi": (17.7800, 83.2100),
        "Gopalapatnam": (17.7500, 83.2400)
    },

    "Surat": {
        "Adajan": (21.2000, 72.7900),
        "Vesu": (21.1500, 72.7700),
        "Varachha": (21.2100, 72.8500),
        "Katargam": (21.2200, 72.8300),
        "Athwa": (21.1700, 72.8000),
        "Udhna": (21.1700, 72.8500),
        "Sachin": (21.0900, 72.8800),
        "Piplod": (21.1600, 72.7800),
        "Rander": (21.2100, 72.8000),
        "Dindoli": (21.1500, 72.8700)
    },

    "Mysore": {
        "VV Mohalla": (12.3200, 76.6400),
        "Gokulam": (12.3300, 76.6300),
        "Kuvempunagar": (12.3000, 76.6200),
        "Nazarbad": (12.3100, 76.6600),
        "Saraswathipuram": (12.3100, 76.6300),
        "Hebbal": (12.3500, 76.6400),
        "Chamrajpura": (12.3000, 76.6600),
        "Bannimantap": (12.3300, 76.6700),
        "Hootagalli": (12.3400, 76.6100),
        "Jayalakshmipuram": (12.3200, 76.6200)
    },

    "Belgaum": {
        "Tilakwadi": (15.8573, 74.5080),
        "Shahapur": (15.8700, 74.5200),
        "Camp": (15.8520, 74.5100),
        "Vadgaon": (15.8600, 74.4900),
        "Angol": (15.8400, 74.5000),
        "Khasbag": (15.8550, 74.4950),
        "Mahantesh Nagar": (15.8600, 74.5300),
        "Kanbargi": (15.8300, 74.4800),
        "Udyambag": (15.8200, 74.5000),
        "Hindwadi": (15.8500, 74.5200)
    },

    "Davangere": {
        "PJ Extension": (14.4644, 75.9218),
        "Saraswathi Nagar": (14.4700, 75.9100),
        "Vidyagiri": (14.4500, 75.9000),
        "KTJ Nagar": (14.4600, 75.9400),
        "Shamanur": (14.4800, 75.9200),
        "MCC B Block": (14.4600, 75.9100),
        "Hadadi Road": (14.4700, 75.9300),
        "Vinobha Nagar": (14.4550, 75.9150),
        "Anjaneya Badavane": (14.4400, 75.9050),
        "Bethur Road": (14.4800, 75.9500)
    }

}

    # -------------------------
    # SELECT CITY FIRST
    # -------------------------
    selected_city = st.selectbox("Select Your City", major_cities)

    # -------------------------
    # OPTION 1: Select Area
    # -------------------------
    if location_mode == "Select City & Area":

        selected_area = st.selectbox(
            "Select Your Area",
            list(area_centers[selected_city].keys())
        )

        user_lat, user_lon = area_centers[selected_city][selected_area]

    # -------------------------
    # OPTION 2: City Center
    # -------------------------
    else:

        city_data = shelters_df[shelters_df["city"] == selected_city]
        user_lat = city_data["latitude"].mean()
        user_lon = city_data["longitude"].mean()

    # -------------------------
    # Filter Shelters by City
    # -------------------------
    filtered_shelters = shelters_df[
        shelters_df["city"] == selected_city
    ]

    # -------------------------
    # Distance Calculation
    # -------------------------
    import math

    def calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat/2)**2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon/2)**2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    distances = []

    for _, row in filtered_shelters.iterrows():
        dist = calculate_distance(
            user_lat,
            user_lon,
            row["latitude"],
            row["longitude"]
        )
        distances.append(dist)

    filtered_shelters["distance_km"] = distances
    filtered_shelters = filtered_shelters.sort_values("distance_km")

    # -------------------------
    # Show Table
    # -------------------------
    st.subheader("Available Shelters (Nearest First)")
    st.dataframe(filtered_shelters[
        ["shelter_name", "city", "capacity", "distance_km"]
    ])

    # -------------------------
    # Show Map
    # -------------------------
    st.write("Latitude:", user_lat)
    st.write("Longitude:", user_lon)
    shelter_map = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=13
    )

    # User marker
    folium.Marker(
        location=[user_lat, user_lon],
        popup="Your Selected Location",
        icon=folium.Icon(color="red")
    ).add_to(shelter_map)

    # Shelter markers
    for _, row in filtered_shelters.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"{row['shelter_name']} (Capacity: {row['capacity']})",
            icon=folium.Icon(color="blue")
        ).add_to(shelter_map)

    st_folium(shelter_map, width=1200, height=600)

    # Add user location marker
    folium.Marker(
        location=[user_lat, user_lon],
        popup="Your Location",
        icon=folium.Icon(color="red")
    ).add_to(shelter_map)

    # Add shelter markers
    for _, row in filtered_shelters.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"""
            {row['shelter_name']}<br>
            Capacity: {row['capacity']}<br>
            Distance: {round(row['distance_km'],2)} km
            """,
            icon=folium.Icon(color="blue")
        ).add_to(shelter_map)

# =====================================================
# 🛣 SAFE ROUTES PAGE
# =====================================================
elif page == "🛣 Safe Routes":

    st.header("🛣 Smart Safe Route & Street Risk Analyzer")

    col_left, col_right = st.columns([2, 1])

    # ---------------------------
    # LEFT COLUMN → SEARCH
    # ---------------------------
    with col_left:

        st.subheader("🔎 Street Risk Checker")

        search_city = st.selectbox(
            "Select City",
            df["city"].unique()
        )
        # Filter streets based on selected city
        city_streets = df[df["city"] == search_city]["street_name"].unique()
        if len(city_streets) > 0:
            search_street = st.selectbox(
                "Select Street",
                sorted(city_streets)
            )
        else:
            search_street = None
            st.warning("No streets found for selected city.")

        if search_street:

            df_sim = df.copy()

            df_sim["rainfall_1h"] = rainfall_1h_input
            df_sim["rainfall_3h"] = rainfall_3h_input
            df_sim["rainfall_6h"] = rainfall_6h_input

            feature_cols = [
                "rainfall_1h",
                "rainfall_3h",
                "rainfall_6h",
                "elevation",
                "drainage_capacity",
                "past_floods",
                "soil_moisture"
            ]

            df_sim["probability"] = model.predict_proba(
                df_sim[feature_cols]
            )[:, 1]
            filtered = df_sim[
                (df_sim["city"] == search_city) &
                (df_sim["street_name"] == search_street)
            ]

            if not filtered.empty:

                row = filtered.iloc[0]
                prob = row["probability"]
                # Get safer alternative streets in same city 
                safer_streets = df_sim[
                    (df_sim["city"] == search_city) &
                    (df_sim["probability"] < prob)
                ].sort_values("probability").head(3)
                st.markdown("---")
                st.subheader(f"📍 {row['street_name']}")

                st.write("Risk Probability:", round(prob * 100, 2), "%")

                if prob < 0.3:
                    st.success("✅ SAFE TO TRAVEL")
                elif prob < 0.6:
                    st.warning("⚠ MODERATE RISK")
                else:
                    st.error("🚨 HIGH FLOOD RISK")

            else:
                st.warning("Street not found in selected city.")

    # ---------------------------
    # RIGHT COLUMN → ROUTES
    # ---------------------------
    with col_right:
        st.subheader("🛣 Smart Recommendations")
        if search_street and not filtered.empty and prob is not None:
            if prob < 0.3:
                st.success("✅ This street is safe. No rerouting needed.")
            elif prob < 0.6:
                st.warning("⚠ Moderate risk detected.")
                st.info("Consider safer nearby streets:")
                for _, safe_row in safer_streets.iterrows():
                    st.success(f"• {safe_row['street_name']}")

            else:
                st.error("🚨 High Flood Risk! Avoid this street.")
                st.info("Recommended safer alternatives:")
                for _, safe_row in safer_streets.iterrows():
                    st.success(f"• {safe_row['street_name']}")

        else:
            st.info("Enter a street name to get route recommendations.")
# ====================================================
# 🚑 EMERGENCY SERVICES PAGE
# =====================================================
elif page == "🚑 Emergency Services":

    st.header("🚑 Emergency Response Units")

    st.write("• 5 Ambulances Deployed")
    st.write("• 3 Fire Rescue Units Active")
    st.write("• 2 Rapid Response Teams Stationed")


    st.info("Nearest Hospital: City General Hospital")

