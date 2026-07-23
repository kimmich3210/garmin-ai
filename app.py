import streamlit as st
import json
import os
from datetime import date

st.set_page_title("Garmin MAF & Restitutions-Dashboard", layout="wide")

st.title("🏃 Garmin MAF & Restitutions-Dashboard")
st.write("Velkommen til dit personlige overblik over dine sundheds- og træningsdata fra Garmin.")

# Find den nyeste JSON-fil med data
json_files = [f for f in os.listdir(".") if f.startswith("garmin_maf_data_") and f.endswith(".json")]

if not json_files:
    st.warning("Ingen datafiler fundet endnu! Kør din GitHub Action for at hente data.")
else:
    # Sorter så vi tager den nyeste fil
    latest_file = sorted(json_files)[-1]
    st.info(f"Viser data fra filen: {latest_file}")
    
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Opret et layout med kolonner til nøgletal
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

    # MAF Beregning
    st.subheader("🎯 MAF 180-Træningsgrænse")
    age = 25
    base_maf = 180 - age
    st.write(f"Baseret på din alder ({age} år) er din teoretiske makspuls for MAF-træning: **{base_maf} slag/min**.")
    st.progress(base_maf / 200, text=f"MAF-grænse: {base_maf} bpm")

    st.divider()

    # Aktiviteter
    st.subheader("🏃 Seneste Aktiviteter")
    activities = data.get("activities")
    if activities and isinstance(activities, list) and len(activities) > 0:
        for act in activities:
            name = act.get('activityName', 'Ukendt aktivitet')
            duration_min = round(act.get('duration', 0) / 60, 1)
            avg_hr = act.get('averageHR', 'N/A')
            st.write(f"- **{name}**: {duration_min} minutter | Gennemsnitspuls: {avg_hr} bpm")
    else:
        st.write("Ingen registrerede aktiviteter for i dag endnu.")
