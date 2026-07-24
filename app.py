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
    
    sorted_files = sorted(json_files)
    
    for file in sorted_files:
        try:
            with open(file, "r", encoding="utf-8") as rf:
                file_data = json.load(rf)
                f_date_str = file_data.get("fetched_at", "")[:10]
                
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

    # --- TOP: PRÆCIS OG DATO-BASERET ANALYSE MED TAL OG PROCENTER ---
    st.subheader("🧠 Dybdegående Dagsanalyse & Restitutionsstatus")
    
    if latest_data:
        # Uddrag præcise værdier
        rhr = latest_data.get("heart_rates", {}).get("restingHeartRate", None)
        
        hrv_data = latest_data.get("hrv", {})
        hrv_val = hrv_data.get("hrvSummary", {}).get("lastNightAvg", None)
        
        sleep_data = latest_data.get("sleep", {})
        sleep_dto = sleep_data.get("dailySleepDTO", {})
        sleep_duration_seconds = sleep_dto.get("sleepTimeSeconds", None)
        sleep_hours = round(sleep_duration_seconds / 3600, 1) if sleep_duration_seconds else None
        
        bb_data = latest_data.get("bodyBattery", [])
        bb_charged = None
        if bb_data and isinstance(bb_data, list):
            bb_charged = bb_data[0].get("charged", None)
            
        stress_data = latest_data.get("stress", {})
        avg_stress = stress_data.get("avgStressLevel", None)

        # Vis tallene i professionelle metrik-bokse
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        col_m1.metric("Hvilepuls", f"{rhr} bpm" if rhr is not None else "Ikke tilgængelig")
        col_m2.metric("Nat HRV", f"{hrv_val} ms" if hrv_val is not None else "Ikke tilgængelig")
        col_m3.metric("Søvnvarighed", f"{sleep_hours} timer" if sleep_hours is not None else "Ikke tilgængelig")
        col_m4.metric("Body Battery", f"{bb_charged}%" if bb_charged is not None else "Ikke tilgængelig")
        col_m5.metric("Gns. Stress", f"{avg_stress}/100" if avg_stress is not None else "Ikke tilgængelig")

        st.markdown("---")
        st.markdown(f"### 📋 Detaljeret køreplan og datagrundlag for d. {latest_date_str}")
        
        points = []
        score = 0
        total_metrics = 0
        
        if rhr is not None:
            total_metrics += 1
            if rhr <= 58:
                score += 1
                points.append(f"• **Hvilepuls ({rhr} bpm):** Ligger på et rigtig fint og lavt niveau, hvilket indikerer god grundform og hvile.")
            else:
                points.append(f"• **Hvilepuls ({rhr} bpm):** Ligger lidt højere, hvilket kan være tegn på let træthed.")

        if hrv_val is not None:
            total_metrics += 1
            if hrv_val >= 45:
                score += 1
                points.append(f"• **Nat-HRV ({hrv_val} ms):** Højt og stabilt niveau, der viser at det autonome nervesystem er i god balance.")
            else:
                points.append(f"• **Nat-HRV ({hrv_val} ms):** Er i den lavere ende, hvilket betyder at kroppen har arbejdet under natten.")

        if sleep_hours is not None:
            total_metrics += 1
            if sleep_hours >= 7.0:
                score += 1
                points.append(f"• **Søvn ({sleep_hours} timer):** Godkendt søvnlængde, der sikrer genopbygning af muskler.")
            else:
                points.append(f"• **Søvn ({sleep_hours} timer):** For lidt søvn i forhold til optimal restitution.")

        if bb_charged is not None:
            total_metrics += 1
            if bb_charged >= 70:
                score += 1
                points.append(f"• **Body Battery Opladning ({bb_charged}%):** Kroppens energiniveau er ladet godt op til en ny dag.")
            else:
                points.append(f"• **Body Battery Opladning ({bb_charged}%):** Lavere opladning end normalt.")

        if avg_stress is not None:
            total_metrics += 1
            if avg_stress <= 30:
                score += 1
                points.append(f"• **Gennemsnitlig Stress ({avg_stress}/100):** Lavt stressniveau i døgnet, hvilket skåner kroppen.")
            else:
                points.append(f"• **Gennemsnitlig Stress ({avg_stress}/100):** Forhøjet stressniveau, som kræver ekstra opmærksomhed.")

        for p in points:
            st.markdown(p)

        st.write("") # Brug standard tom linje i stedet for HTML-hack

        # Endelig konklusion baseret på de faktiske tal
        if total_metrics == 0:
            st.warning("⚠️ Ingen detaljerede sundhedsmetrikker fundet i dagens datafil endnu.")
        elif score >= (total_metrics / 2):
            st.success(f"🟢 **Konklusion ({score}/{total_metrics} parametre i top):** Tallene viser, at din kroppens reserver er fine. Du kan roligt gennemføre dagens planlagte træning med fokus på zonen.")
        else:
            st.warning(f"🟡 **Konklusion ({score}/{total_metrics} parametre godkendt):** Flere nøgletal viser, at kroppen er mærket af belastning. Overvej at tage det med ro eller skrue ned for intensiteten i dag.")
    else:
        st.warning("Kunne ikke indhente data til analysen.")

    st.divider()

    # --- RESTITUTION (SIDSTE 14 DAGE) ---
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
