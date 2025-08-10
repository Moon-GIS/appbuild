import streamlit as st
import ee
import geemap.foliumap as geemap

# Load secrets from Streamlit
SERVICE_ACCOUNT = st.secrets["google_earth_engine"]["service_account"]
PRIVATE_KEY = st.secrets["google_earth_engine"]["private_key"]

# Authenticate Earth Engine using service account
credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, key_data=PRIVATE_KEY)
ee.Initialize(credentials)

st.title("Google Earth Engine in Streamlit (Service Account)")

# Example: Load and display a satellite image
dataset = ee.Image('COPERNICUS/S2_SR/20210701T043601_20210701T043603_T46QDD') \
            .select(['B4', 'B3', 'B2'])  # RGB bands

Map = geemap.Map(center=[27.7, 85.3], zoom=8)  # Example: Kathmandu
vis_params = {'min': 0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}
Map.addLayer(dataset, vis_params, "Sentinel-2 RGB")
Map.addLayerControl()

Map.to_streamlit(height=600)
