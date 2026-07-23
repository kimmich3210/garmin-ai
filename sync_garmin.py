import os
import json
from datetime import date
from garminconnect import Garmin

# Log ind på Garmin
client = Garmin(
    os.getenv("EMAIL"),
    os.getenv("PASSWORD"),
    prompt_mfa=lambda: input("MFA code: "),
)
client.login("~/.garminconnect")

today = date.today().isoformat()
print(f"Henter og analyserer MAF- og pulsdata for i dag ({today})...\n" + "="*50)

# 1. Beregn MAF 180-formlen (180 - alder)
# Din fødselsdag er 24. juni 2001, så du er 25 år i 2026
age = 25 
base_maf = 180 - age
print(f"🎯 Din teoretiske MAF-grænse (180-formel): {base_maf} slag/min\n" + "-"*50)

# 2. Hent sundheds- og træningsdata
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

# Gem data ned
filename = f"garmin_maf_data_{today}.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

# 3. Udskriv en læsevenlig MAF-rapport direkte i terminalen
print("\n" + "="*50)
print("📊 MAF & RESTITUTIONSRAPPORT")
print("="*50)

# Hvilepuls & Skridt
stats = all_data.get("stats") or {}
hr_data = all_data.get("heart_rates") or {}
print(f"• Hvilepuls: {hr_data.get('restingHeartRate', 'Ikke tilgængelig')} slag/min")
print(f"• Skridt i dag: {stats.get('totalSteps', 'Ikke tilgængelig')}")

# HRV (Hovedindikator for restitution før MAF-tur)
hrv_data = all_data.get("hrv") or {}
if hrv_data:
    # Prøv at finde nightly status eller 7-dages gennemsnit
    last_night_hrv = hrv_data.get('hrvSummary', {}).get('lastNightAvg', 'Ikke tilgængelig')
    print(f"• HRV (Natgennemsnit): {last_night_hrv} ms")
else:
    print("• HRV: Ingen data fundet for i dag endnu.")

# Seneste aktiviteter tjek
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