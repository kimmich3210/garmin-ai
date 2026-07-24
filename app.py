import streamlit as st
import json
import glob
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Garmin Trænings-Dashboard", layout="wide")

json_files = glob.glob("garmin_maf_data_*.json")

if not json_files:
    st.warning("Ingen datafiler fundet endnu! Sørg for, at der ligger filer i mappen.")
else:
    health_history = []
    all_activities = []
    latest_data = None
    latest_date_str = ""
    
    # Sorter filer for at finde den aller nyeste
    sorted_files = sorted(json_files)
    
    for file in sorted_files:
        try:
            with open(file, "r", encoding="utf-8") as rf:
                file_data = json.load(rf)
                f_date_str = file_data.get("fetched_at", "")[:10]
                
                # Gem den nyeste fil til dagens analyse
                latest_data = file_data
                latest_date_str = f_date_str
                
                f_rhr = file_data.get("heart_rates", {}).get("restingHeartRate", None)
                f_hrv = file_data.get("hrv", {}).get("hrvSummary", {}).get("lastNightAvg", None)
                
                if f_date_str and (f_rhr is not None or f_hrv is not None):
                    health_history.append({
                        "DatoObj": datetime.strptime(f_date_str, "%Y-%m-%d"),
                        "Dato": f_date_str,
                        "Hvilepuls": f_rhr,
                        "HRV": f_hrv
                    })
                
                acts = file_data.get("activities", [])
                if acts and isinstance(acts, list):
                    all_activities.extend(acts)
        except Exception:
            pass

    # --- TOP: DAGLIG AI / GARMIN ANALYSE OG ANBEFALING ---
    st.subheader("💡 Dagens Trænings- og Restitutionsstatus")
    
    if latest_data:
        # Uddrag data fra seneste synkronisering
        rhr = latest_data.get("heart_rates", {}).get("restingHeartRate", "Ukendt")
        hrv_dict = latest_data.get("hrv", {}).get("hrvSummary", {})
        hrv_val = hrv_dict.get("lastNightAvg", "Ukendt")
        
        # Søvn (hvis det findes i data)
        sleep_data = latest_data.get("sleep", {})
        sleep_score = sleep_data.get("dailySleepDTO", {}).get("sleepScoreFeedback", "Ikke tilgængelig")
        sleep_duration_seconds = sleep_data.get("dailySleepDTO", {}).get("sleepTimeSeconds", 0)
        sleep_hours = round(sleep_duration_seconds / 3600, 1) if sleep_duration_seconds else "Ukendt"
        
        # Body Battery / Batteri (hvis det findes)
        body_battery = latest_data.get("bodyBattery", [])
        bb_charged = "Ukendt"
        if body_battery and isinstance(body_battery, list):
            bb_charged = body_battery[0].get("charged", "Ukendt")

        # Vis metrikker i små bokse
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Hvilepuls", f"{rhr} bpm" if rhr != "Ukendt" else "Ikke m.t.")
        col_m2.metric("Nat HRV", f"{hrv_val} ms" if hrv_val != "Ukendt" else "Ikke m.t.")
        col_m3.metric("Søvnvarighed", f"{sleep_hours} timer" if sleep_hours != "Ukendt" else "Ikke m.t.")
        col_m4.metric("Body Battery (Opladet)", f"{bb_charged}" if bb_charged != "Ukendt" else "Ikke m.t.")

        # Generer smart tekst baseret på tallene
        st.markdown("---")
        advice_text = f"**Status for i dag ({latest_date_str}):**\n\n"
        
        # Simpel intelligent vurdering
        is_good_to_go = True
        reasons = []
        
        if isinstance(rhr, (int, float)) and rhr > 60:  # Eksempelgrænse, tilpas efter behov
            is_good_to_go = False
            reasons.append("din hvilepuls er lidt højere end normalt")
        if isinstance(hrv_val, (int, float)) and hrv_val < 40: # Eksempelgrænse
            is_good_to_go = False
            reasons.append("din nat-HRV er lav, hvilket indikerer lavere restitution")
        if isinstance(sleep_hours, (int, float)) and sleep_hours < 6.5:
            is_good_to_go = False
            reasons.append("du har sovet i kortere tid end anbefalet")

        if is_good_to_go:
            advice_text += "🟢 **Klar til træning!** Dine værdier (søvn, hvilepuls og HRV) ser fornuftige ud. Det er en rigtig god dag til at gennemføre din planlagte MAF-løbetræning med fuldt fokus på pulszonen."
        else:
            reason_str = ", og ".join(reasons)
            advice_text += f"🟡 **Tag det roligt i dag:** Da {reason_str}, bør du lytte ekstra godt efter kroppen. Overvej om dagens træning skal skiftes ud med en rolig gåtur, restitution eller et lettere tempo, så du ikke overbelaster systemet."
            
        st.info(advice_text)
    else:
        st.warning("Kunne ikke indhente data til dagens analyse endnu.")

    st.divider()

    # --- SMÅ GRAFER FOR HVILEPULS & HRV (SIDSTE 14 DAGE) ---
    st.subheader("📊 Restitution (Sidste 14 dage)")
    
    if health_history:
        df_health = pd.DataFrame(health_history)
        fourteen_days_ago = datetime.now() - timedelta(days=14)
        df_health = df_health[df_health["DatoObj"] >= fourteen_days_ago].sort_values("DatoObj")
        
        if not df_health.empty:
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                fig_rhr = px.line(
                    df_health, x="Dato", y="Hvilepuls", 
                    markers=True, title="Hvilepuls (Sidste 14 dage)",
                    color_discrete_sequence=["#e377c2"],
                    line_shape="spline",
                    text="Hvilepuls"
                )
                fig_rhr.update_traces(texttemplate='%{y}', textposition="top center", line=dict(width=2.5), marker=dict(size=7))
                fig_rhr.update_layout(
                    template="plotly_white", 
                    margin=dict(l=10, r=10, t=30, b=10), 
                    height=280,
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True)
                )
                st.plotly_chart(fig_rhr, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
                
            with col_g2:
                fig_hrv = px.line(
                    df_health, x="Dato", y="HRV", 
                    markers=True, title="HRV Nat (Sidste 14 dage)",
                    color_discrete_sequence=["#2ca02c"],
                    line_shape="spline",
                    text="HRV"
                )
                fig_hrv.update_traces(texttemplate='%{y}', textposition="top center", line=dict(width=2.5), marker=dict(size=7))
                fig_hrv.update_layout(
                    template="plotly_white", 
                    margin=dict(l=10, r=10, t=30, b=10), 
                    height=280,
                    xaxis=dict(fixedrange=True),
                    yaxis=dict(fixedrange=True)
                )
                st.plotly_chart(fig_hrv, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
        else:
            st.info("Ingen historiske sundhedsdata fra de sidste 14 dage endnu.")

    st.divider()

    col_titel, col_filter = st.columns([2, 1])
    with col_titel:
        st.subheader("📈 MAF Løbetræning")
    with col_filter:
        time_filter = st.selectbox("Vælg periode:", ["Sidste måned", "Alle tilgængelige data"])

    if all_activities:
        act_list = []
        seen_ids = set()
        
        for act in all_activities:
            act_id = act.get("activityId")
            if act_id in seen_ids:
                continue
            seen_ids.add(act_id)
            
            name = act.get("activityName", "")
            activity_type = act.get("activityType", {}).get("typeKey", "")
            
            is_run = "run" in activity_type.lower() or "løb" in name.lower() or "running" in name.lower()
            
            if is_run:
                date_str = act.get("startTimeLocal", "")[:10]
                avg_hr = act.get("averageHR", 0)
                distance = act.get("distance", 0) / 1000 
                duration = act.get("duration", 0) / 60 
                
                pace_min_km = 0
                pace_str = "0:00"
                pace_sort = 0
                if distance > 0 and duration > 0:
                    pace_min_km = duration / distance
                    mins = int(pace_min_km)
                    secs = int(round((pace_min_km - mins) * 60))
                    if secs == 60:
                        mins += 1
                        secs = 0
                    pace_str = f"{mins}:{secs:02d}"
                    pace_sort = pace_min_km 
                    
                if date_str:
                    try:
                        act_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        act_date = datetime.now()
                        
                    act_list.append({
                        "Dato": act_date,
                        "DatoStr": date_str,
                        "Aktivitet": name if name else "Løb",
                        "Gennemsnitspuls": avg_hr,
                        "Distancet (km)": round(distance, 2),
                        "Pace": pace_str,
                        "_PaceSort": pace_sort
                    })
            
        df = pd.DataFrame(act_list)
        
        if not df.empty:
            if time_filter == "Sidste måned":
                one_month_ago = datetime.now() - timedelta(days=30)
                df_filtered = df[df["Dato"] >= one_month_ago].copy()
                if df_filtered.empty:
                    df_filtered = df.copy()
            else:
                df_filtered = df.copy()
            
            df_filtered = df_filtered.sort_values("Dato")
            
            # --- GRAF 1: GENNEMSNITSPULS (MAF) ---
            st.subheader("❤️ Gennemsnitspuls (MAF)")
            fig_hr = px.line(
                df_filtered, 
                x="DatoStr", 
                y="Gennemsnitspuls", 
                markers=True,
                hover_data=["Aktivitet", "Distancet (km)", "Pace"],
                color_discrete_sequence=["#1f77b4"],
                line_shape="spline",
                text="Gennemsnitspuls"
            )
            fig_hr.update_traces(texttemplate='%{y}', textposition="top center", line=dict(width=3), marker=dict(size=8))
            
            base_maf = 155
            fig_hr.add_hline(
                y=base_maf, 
                line_dash="dash", 
                line_color="#ff4b4b", 
                line_width=2,
                annotation_text=f"MAF Grænse ({base_maf} bpm)",
                annotation_position="top left"
            )
            
            fig_hr.update_layout(
                xaxis_title="Dato",
                yaxis_title="Puls (bpm)",
                hovermode="x unified",
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20),
                height=400,
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True)
            )
            st.plotly_chart(fig_hr, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})

            # --- GRAF 2: PACE ---
            st.subheader("⚡ Pace (min/km)")
            fig_pace = px.line(
                df_filtered, 
                x="DatoStr", 
                y="_PaceSort", 
                markers=True,
                hover_data=["Aktivitet", "Distancet (km)", "Gennemsnitspuls"],
                color_discrete_sequence=["#9467bd"],
                line_shape="spline",
                text=df_filtered["Pace"]
            )
            fig_pace.update_traces(texttemplate='%{text}', textposition="top center", line=dict(width=3), marker=dict(size=8))
            
            fig_pace.update_layout(
                xaxis_title="Dato",
                yaxis_title="Pace (min/km)",
                hovermode="x unified",
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20),
                height=400,
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True, autorange="reversed")
            )
            
            st.plotly_chart(fig_pace, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
            
            st.subheader("📋 Aktivitetsdetaljer (Løb)")
            display_df = df_filtered.drop(columns=["Dato", "_PaceSort"]).rename(columns={"DatoStr": "Dato"})
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Ingen løbeaktiviteter fundet i de indlæste datafiler.")
    else:
        st.info("Ingen aktivitetsdata fundet i filerne.")
