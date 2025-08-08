import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Vegetation Health Checker", layout="wide")

st.title("🌱 Vegetation Health Dashboard")

# User inputs
lat = st.number_input("Enter Latitude", value=34.0837, format="%.6f")
lon = st.number_input("Enter Longitude", value=74.7973, format="%.6f")

# Dummy NDVI check (replace with real API or satellite data)
ndvi_value = 0.65 if (lat and lon) else None

if ndvi_value:
    if ndvi_value > 0.5:
        health_status = "Healthy"
        color = "green"
    else:
        health_status = "Unhealthy"
        color = "red"

    st.success(f"NDVI: {ndvi_value:.2f} → **{health_status} vegetation**")

    # Show location on map
    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.CircleMarker(
        location=[lat, lon],
        radius=10,
        popup=f"NDVI: {ndvi_value:.2f} ({health_status})",
        color=color,
        fill=True
    ).add_to(m)
    st_folium(m, width=700, height=500)
