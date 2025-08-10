import streamlit as st
import ee
import geemap.foliumap as geemap

# Load secrets from Streamlit
SERVICE_ACCOUNT = st.secrets["google_earth_engine"]["client_email"]
PRIVATE_KEY = st.secrets["google_earth_engine"]["private_key"]

# Authenticate Earth Engine using service account
credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, key_data=PRIVATE_KEY)
ee.Initialize(credentials)

st.title("🌱 Vegetation Health Dashboard (NDVI)")

# Example: Sentinel-2 NDVI for given lat/lon
lat = st.number_input("Enter Latitude", value=22.5726)   # Default Kolkata
lon = st.number_input("Enter Longitude", value=88.3639)  # Default Kolkata

# Date range
start_date = st.date_input("Start Date", value=ee.Date("2024-01-01").format().getInfo())
end_date = st.date_input("End Date", value=ee.Date("2024-01-31").format().getInfo())

if st.button("Generate NDVI Map"):
    point = ee.Geometry.Point(lon, lat)

    # Load Sentinel-2 surface reflectance
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR")
        .filterBounds(point)
        .filterDate(str(start_date), str(end_date))
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
    )

    # Compute NDVI
    def add_ndvi(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi)

    ndvi_collection = collection.map(add_ndvi)
    ndvi_image = ndvi_collection.median()

    # Visualization parameters
    ndvi_params = {"min": -1, "max": 1, "palette": ["blue", "white", "green"]}

    # Create map
    Map = geemap.Map(center=[lat, lon], zoom=12)
    Map.addLayer(ndvi_image.select("NDVI"), ndvi_params, "NDVI")
    Map.addLayer(point, {"color": "red"}, "Location")
    Map.addLayerControl()
    Map.to_streamlit(height=600)

    # Get mean NDVI value
    mean_ndvi = ndvi_image.select("NDVI").reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point.buffer(30),  # 30m radius
        scale=10
    ).get("NDVI").getInfo()

    if mean_ndvi is not None:
        st.success(f"Mean NDVI at location: {mean_ndvi:.3f}")
        if mean_ndvi > 0.5:
            st.write("✅ Healthy vegetation")
        elif mean_ndvi > 0.2:
            st.write("⚠ Moderately healthy vegetation")
        else:
            st.write("❌ Unhealthy vegetation")
    else:
        st.warning("No NDVI data available for this location and date range.")
