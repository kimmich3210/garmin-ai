import os
import json
from datetime import date
from garminconnect import Garmin

# Hent e-mail og adgangskode fra GitHub Secrets
email = os.getenv("GARMIN_EMAIL")
password = os.getenv("GARMIN_PASSWORD")

if not email or not password:
    raise ValueError("FEJL: GARMIN_EMAIL eller GARMIN_PASSWORD mangler i GitHub Secrets!")

print("Logger ind på Garmin via e-mail...")
client = Garmin(email, password)
client.login()
print(" [OK] Succesfuldt logget ind!")

today = date.today().isoformat()
print(f"Henter og analyserer MAF- og pulsdata for i dag ({today})...\n" + "="*50)

# Beregn MAF 180-formlen (180 - alder)
# Fødselsdag 24. juni 2001 -> 25 år i 2026
age = 25 
base_maf = 180 - age
print(f"🎯 Din teoretiske MAF-grænse (180-formel): {base_maf} slag/min\n" + "-"*50)

all_data = {}

def fetch_safe(name, func, *args):
    try:
        res = func(*args)
        print(f" [OK] {name}")
        return res
    except Exception as e:
        print(f" [X] {name} (Fejl: {e})")
        return None

all_data["stats"] = fetch_safe("Daglige Statistikker", client.get_stats, today)
all_data["heart_rates"] = fetch_safe("Pulsdata & Hvilepuls", client.get_heart_rates, today)
all_data["hrv"] = fetch_safe("HRV (Restitution)", client.get_hrv_data, today)
all_data["sleep"] = fetch_safe("Søvndata", client.get_sleep_data, today)
all_data["training_status"] = fetch_safe("Træningsstatus", client.get_training_status, today)
all_data["activities"] = fetch_safe("Seneste Aktiviteter", client.get_activities, 0, 3)

filename = f"garmin_maf_data_{today}.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print("\n" + "="*50)
print("📊 MAF & RESTITUTIONSRAPPORT")
print("="*50)

stats = all_data.get("stats") or {}
hr_data = all_data.get("heart_rates") or {}
print(f"• Hvilepuls: {hr_data.get('restingHeartRate', 'Ikke tilgængelig')} slag/min")
print(f"• Skridt i dag: {stats.get('totalSteps', 'Ikke tilgængelig')}")

hrv_data = all_data.get("hrv") or {}
if hrv_data:
    last_night_hrv = hrv_data.get('hrvSummary', {}).get('lastNightAvg', 'Ikke tilgængelig')
    print(f"• HRV (Natgennemsnit): {last_night_hrv} ms")
else:
    print("• HRV: Ingen data fundet for i dag endnu.")

activities = all_data.get("activities")
if activities and isinstance(activities, list) and len(activities) > 0:
    print("\n🏃 Seneste træningspas:")
    for act in activities[:3]:
        name = act.get('activityName', 'Ukendt aktivitet')
        duration_min = round(act.get('duration', 0) / 60, 1)
        avg_hr = act.get('averageHR', 'N/A')
        print(f"  - {name}: {duration_min} min | Snitpuls: {avg_hr} bpm")
else:
    print("\n🏃 Seneste aktiviteter: Ingen fundet for i dag.")

print("="*50)
print(f"Alt data er gemt i '{filename}'")
