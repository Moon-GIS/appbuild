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
st.title("🌱 Vegetation Health Classification from CSV Coordinates")

# ---------------------
# FILE UPLOAD
# ---------------------
uploaded_file = st.file_uploader("Upload CSV with 'latitude' and 'longitude' columns", type="csv")

start_date = st.date_input("Start Date", value=pd.to_datetime("2024-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2024-01-31"))

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Check required columns
    if not {"latitude", "longitude"}.issubset(df.columns):
        st.error("CSV must have 'latitude' and 'longitude' columns")
    else:
        st.success(f"Loaded {len(df)} locations from CSV.")

        results = []
        Map = geemap.Map(center=[df["latitude"].mean(), df["longitude"].mean()], zoom=6)

        for idx, row in df.iterrows():
            lat, lon = row["latitude"], row["longitude"]
            point = ee.Geometry.Point(lon, lat)

            # Load Sentinel-2 imagery
            collection = (
                ee.ImageCollection("COPERNICUS/S2_SR")
                .filterBounds(point)
                .filterDate(str(start_date), str(end_date))
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
            )

            def add_ndvi(img):
                ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
                return img.addBands(ndvi)

            ndvi_img = collection.map(add_ndvi).median()
            mean_ndvi = ndvi_img.select("NDVI").reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(30),  # 30m radius
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

            # Add marker to map
            popup_text = f"NDVI: {ndvi_str}\nStatus: {status}"
            Map = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=6)
            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                icon=folium.Icon(color=color)
            ).add_to(Map)
            st_folium(Map, width="100%", height=600)

        # Show map and table
        Map.to_streamlit(width="100%", height=600)
        st.subheader("Classification Results")
        result_df = pd.DataFrame(results)
        st.dataframe(result_df)

        # Download button
        csv_buffer = BytesIO()
        result_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download Results CSV",
            data=csv_buffer.getvalue(),
            file_name="ndvi_classification.csv",
            mime="text/csv"
        )


