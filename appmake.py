import streamlit as st
import geemap
import folium
from folium import plugins
import ee

# Initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

st.set_page_config(page_title="NDVI Checker", layout="wide")

st.title("🌱 NDVI Vegetation Health Checker")

# Input coordinates
lat = st.number_input("Latitude", value=22.5726, format="%.6f")
lon = st.number_input("Longitude", value=88.3639, format="%.6f")

if st.button("Check NDVI"):
    # Sentinel-2 image collection
    collection = ee.ImageCollection("COPERNICUS/S2_SR") \
        .filterBounds(ee.Geometry.Point(lon, lat)) \
        .filterDate('2024-01-01', '2024-12-31') \
        .sort('CLOUDY_PIXEL_PERCENTAGE') \
        .first()
    
    if collection:
        ndvi_img = collection.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndvi_value = ndvi_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=ee.Geometry.Point(lon, lat),
            scale=10
        ).get('NDVI').getInfo()

        st.write(f"📍 **Latitude:** {lat}, **Longitude:** {lon}")
        st.write(f"🌿 **NDVI Value:** {ndvi_value:.3f}")

        if ndvi_value >= 0.6:
            st.success("Healthy vegetation 🌱")
        elif ndvi_value >= 0.3:
            st.warning("Moderate vegetation 🍂")
        else:
            st.error("Unhealthy vegetation 🚨")

        # Show map
        m = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], popup="Selected Location").add_to(m)
        map_html = m._repr_html_()
        st.components.v1.html(map_html, height=500)
    else:
        st.error("No satellite image found for this location/date range.")

