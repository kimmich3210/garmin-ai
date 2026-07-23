import streamlit as st
import json
import os
import glob

st.set_page_config(page_title="Garmin MAF & Restitutions-Dashboard", layout="wide")

st.title("🏃 Garmin MAF & Restitutions-Dashboard")
st.write("Velkommen til dit personlige overblik over dine sundheds- og træningsdata fra Garmin.")

# Find den nyeste JSON-fil med data
json_files = glob.glob(r"C:\Users\kimen\Desktop\garmin-ai\garmin_maf_data_*.json")

if not json_files:
    st.warning("Ingen datafiler fundet endnu! Sørg for, at der ligger en garmin_maf_data_*.json fil i mappen.")
else:
    latest_file = sorted(json_files)[-1]
    st.info(f"Viser data fra filen: {latest_file}")
    
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    col1, col2, col3 = st.columns(3)
    
    stats = data.get("stats", {})
    hr_data = data.get("heart_rates", {})
    hrv_data = data.get("hrv", {})
    
    with col1:
        resting_hr = hr_data.get('restingHeartRate', 'N/A')
        st.metric("Hvilepuls", f"{resting_hr} bpm")
        
    with col2:
        steps = stats.get('totalSteps', 'N/A')
        st.metric("Skridt i dag", steps)
        
    with col3:
        last_night_hrv = hrv_data.get('hrvSummary', {}).get('lastNightAvg', 'N/A')
        st.metric("HRV (Natgennemsnit)", f"{last_night_hrv} ms")

    st.divider()

    st.subheader("🎯 MAF 180-Træningsgrænse")
    age = 25
    base_maf = 180 - age
    st.write(f"Baseret på din alder ({age} år) er din teoretiske makspuls for MAF-træning: **{base_maf} slag/min**.")
    st.progress(base_maf / 200, text=f"MAF-grænse: {base_maf} bpm")