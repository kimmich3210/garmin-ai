from datetime import datetime, timedelta
from garminconnect import Garmin
import json
import os

email = "DIN_EMAIL"
password = "DIT_PASSWORD"

tokenstore = os.path.expanduser("~/.garminconnect")

print("Logger ind på Garmin Connect...")
try:
    api = Garmin()
    api.login(tokenstore)
    print("Logget ind via gemte tokens!")
except Exception:
    print("Logger ind med brugernavn, adgangskode og MFA...")
    try:
        api = Garmin(
            email=email,
            password=password,
            prompt_mfa=lambda: input("Indtast MFA-kode fra Garmin: ").strip()
        )
        api.login(tokenstore)
        print("Login succesfuldt og tokens gemt!")
    except Exception as e:
        print(f"Fejl ved login: {e}")
        exit()

days_to_fetch = 30
print(f"Henter data og historik for de sidste {days_to_fetch} dage...")

for i in range(days_to_fetch):
    target_date = datetime.now() - timedelta(days=i)
    date_str = target_date.strftime("%Y-%m-%d")
    filename = f"garmin_maf_data_{date_str}.json"
    
    if os.path.exists(filename):
        print(f"Skipper {date_str} (findes allerede)")
        continue

    print(f"Henter data for {date_str}...")
    try:
        stats = api.get_stats(date_str)
    except Exception:
        stats = {}

    try:
        hr_data = api.get_heart_rates(date_str)
    except Exception:
        hr_data = {}

    try:
        hrv = api.get_hrv_data(date_str)
    except Exception:
        hrv = {}

    day_data = {
        "fetched_at": date_str,
        "stats": stats,
        "hrv": hrv,
        "heart_rates": hr_data,
        "activities": []
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(day_data, f, ensure_ascii=False, indent=4)

start_date_str = (datetime.now() - timedelta(days=days_to_fetch)).strftime("%Y-%m-%d")
end_date_str = datetime.now().strftime("%Y-%m-%d")

try:
    print("Henter træningsaktiviteter...")
    activities = api.get_activities_by_date(start_date_str, end_date_str)
    
    for act in activities:
        act_date_str = act.get("startTimeLocal", "")[:10]
        filename = f"garmin_maf_data_{act_date_str}.json"
        
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                day_data = json.load(f)
            
            if "activities" not in day_data:
                day_data["activities"] = []
                
            existing_ids = [a.get("activityId") for a in day_data["activities"]]
            if act.get("activityId") not in existing_ids:
                day_data["activities"].append(act)
                
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(day_data, f, ensure_ascii=False, indent=4)
                
    print("Alle historiske data og træninger er hentet og gemt succesfuldt!")

except Exception as e:
    print(f"Fejl ved hentning af aktiviteter: {e}")
