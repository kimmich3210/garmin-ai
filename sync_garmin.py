import os
import json
import base64
from datetime import date
from garminconnect import Garmin

token_input = os.getenv("GARMIN_TOKEN_B64")
if not token_input:
    raise ValueError("FEJL: GARMIN_TOKEN_B64 miljøvariablen er tom eller mangler!")

print(f"Token-længde modtaget: {len(token_input)} tegn")

# Prøv at dekode hvis det er Base64, ellers brug direkte
token_data = None
try:
    cleaned_input = token_input.strip()
    decoded_bytes = base64.b64decode(cleaned_input, validate=False)
    token_json = decoded_bytes.decode("utf-8")
    token_data = json.loads(token_json)
    print(" [OK] Token blev succesfuldt dekodet fra Base64.")
except Exception:
    try:
        token_data = json.loads(token_input)
        print(" [OK] Token blev indlæst direkte som JSON.")
    except Exception as e:
        print(f" [X] Kunne ikke parse token. Indhold start: {token_input[:30]}...")
        raise e

# Log ind på Garmin via token
client = Garmin()
client.login(token_data)

today = date.today().isoformat()
print(f"Henter og analyserer MAF- og pulsdata for i dag ({today})...\n" + "="*50)

# 1. Beregn MAF 180-formlen (180 - alder)
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
