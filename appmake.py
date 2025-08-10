import streamlit as st
import ee
import geemap.foliumap as geemap
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import BytesIO

# ---------------------
# PAGE CONFIG
# ---------------------
st.set_page_config(layout="wide", page_title="Vegetation Health Classifier")

# ---------------------
# EARTH ENGINE AUTHENTICATION
# ---------------------
SERVICE_ACCOUNT = st.secrets["google_earth_engine"]["client_email"]
PRIVATE_KEY = st.secrets["google_earth_engine"]["private_key"]

credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, key_data=PRIVATE_KEY)
ee.Initialize(credentials)

# ---------------------
# TITLE
# ---------------------
st.title("🌱 Vegetation Health Classification from CSV Coordinates + NDVI Background")

# ---------------------
# FILE UPLOAD
# ---------------------
uploaded_file = st.file_uploader("Upload CSV with 'latitude' and 'longitude' columns", type="csv")

start_date = st.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2024-01-31"))

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if not {"latitude", "longitude"}.issubset(df.columns):
        st.error("CSV must have 'latitude' and 'longitude' columns")
    else:
        st.success(f"Loaded {len(df)} locations from CSV.")

        results = []

        # --- Create geemap Map ---
        m = geemap.Map(center=[df["latitude"].mean(), df["longitude"].mean()], zoom=6)

        # --- Create NDVI background layer ---
        s2_collection = (
            ee.ImageCollection("COPERNICUS/S2_SR")
            .filterBounds(ee.Geometry.Point(df["longitude"].mean(), df["latitude"].mean()))
            .filterDate(str(start_date), str(end_date))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
        )

        def add_ndvi(img):
            ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
            return img.addBands(ndvi)

        ndvi_img = s2_collection.map(add_ndvi).median().select("NDVI")

        # Visualization parameters for NDVI
        ndvi_vis = {
            "min": 0.0,
            "max": 1.0,
            "palette": ["red", "yellow", "green"]
        }

        m.add_layer(ndvi_img, ndvi_vis, "NDVI Background")

        # --- Loop over CSV points and add markers ---
        for idx, row in df.iterrows():
            lat, lon = row["latitude"], row["longitude"]
            point = ee.Geometry.Point(lon, lat)

            # NDVI at point
            mean_ndvi = ndvi_img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(30),
                scale=10
            ).get("NDVI").getInfo()

            # Classification
            if mean_ndvi is None:
                status = "No Data"
                color = "gray"
                ndvi_str = "N/A"
            elif mean_ndvi > 0.5:
                status = "Healthy"
                color = "green"
                ndvi_str = f"{mean_ndvi:.3f}"
            elif mean_ndvi > 0.2:
                status = "Moderately Healthy"
                color = "orange"
                ndvi_str = f"{mean_ndvi:.3f}"
            else:
                status = "Non-Healthy"
                color = "red"
                ndvi_str = f"{mean_ndvi:.3f}"

            results.append({"latitude": lat, "longitude": lon, "NDVI": ndvi_str, "Status": status})

            # Add folium marker to same map
            folium.Marker(
                location=[lat, lon],
                popup=f"NDVI: {ndvi_str}\nStatus: {status}",
                icon=folium.Icon(color=color)
            ).add_to(m)

        # --- Add legend ---
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px; height: 130px; 
                    border:2px solid grey; z-index:9999; font-size:14px;
                    background-color:white; padding: 10px;">
        <b>Legend</b><br>
        <i class="fa fa-map-marker" style="color:green"></i> Healthy<br>
        <i class="fa fa-map-marker" style="color:orange"></i> Moderately Healthy<br>
        <i class="fa fa-map-marker" style="color:red"></i> Non-Healthy<br>
        <i class="fa fa-map-marker" style="color:gray"></i> No Data
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        # --- Show map ---
        st_folium(m, width="100%", height=600)

        # --- Show results table ---
        st.subheader("Classification Results")
        result_df = pd.DataFrame(results)
        st.dataframe(result_df)

        # --- Download button ---
        csv_buffer = BytesIO()
        result_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download Results CSV",
            data=csv_buffer.getvalue(),
            file_name="ndvi_classification.csv",
            mime="text/csv"
        )
