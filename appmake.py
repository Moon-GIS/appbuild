import streamlit as st
import geemap.folium as geemap
import ee

# Initialize Earth Engine
ee.Authenticate()
# Replace 'your-project-id' with your actual Google Cloud Project ID
ee.Initialize(project='glowing-market-422115-t8')

st.title("Vegetation Health Checker")
st.write("Enter latitude & longitude to check crop health")

# User Input
lat = st.number_input("Latitude", value=34.0837)
lon = st.number_input("Longitude", value=74.7973)

# Date Range
start_date = "2025-07-01"
end_date = "2025-08-01"

# Sentinel-2 Dataset
collection = (ee.ImageCollection('COPERNICUS/S2_SR')
              .filterDate(start_date, end_date)
              .filterBounds(ee.Geometry.Point(lon, lat))
              .sort('CLOUD_COVER')
              .first())

# NDVI Calculation
ndvi = collection.normalizedDifference(['B8', 'B4']).rename('NDVI')

# Get NDVI value at point
point = ee.Geometry.Point(lon, lat)
ndvi_value = ndvi.reduceRegion(ee.Reducer.mean(), point, 10).get('NDVI').getInfo()

# Classification
if ndvi_value is not None:
    if ndvi_value > 0.4:
        health_status = "🌱 Healthy Vegetation"
    elif ndvi_value > 0.2:
        health_status = "⚠️ Moderate Stress"
    else:
        health_status = "🚨 Poor Health"
else:
    health_status = "No data available for this point"

# Output
st.metric(label="NDVI Value", value=f"{ndvi_value:.2f}" if ndvi_value else "N/A")
st.subheader(health_status)

# Map Visualization
Map = geemap.Map(center=(lat, lon), zoom=12)
Map.addLayer(ndvi, {'min': 0, 'max': 1, 'palette': ['brown', 'yellow', 'green']}, 'NDVI')
Map.add_marker(location=[lat, lon], popup=health_status) # Corrected method name

Map.to_streamlit()
