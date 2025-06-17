# main.py — ExploreMoreIL cancellation watcher
import os, time, requests, datetime, sys

# ---------- EDIT THESE FOUR LINES ----------
LOCATION_ID     = 201                # Eldon Hazlet; change if needed
START_DATE      = "2025-06-28"       # arrival
END_DATE        = "2025-06-29"       # departure (next morning)
CHECK_EVERY_SEC = 300                # poll every 5 min (be nice)
# -------------------------------------------

PUSH_USER  = os.environ["uujy7e2wzzo8vvo6mozeot5t5hwfx7"]
PUSH_TOKEN = os.environ["ar9j7bwysjw22ssbrxepmwvmphpjvy"]

def notify(msg):
    requests.post("https://api.pushover.net/1/messages.json",
                  data={"token": PUSH_TOKEN, "user": PUSH_USER,
                        "title": "ExploreMoreIL site open!", "message": msg})

def check():
    url = (f"https://camp.exploremoreil.com/api/availability"
           f"?locationId={LOCATION_ID}"
           f"&startDate={START_DATE}&endDate={END_DATE}")
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def main():
    seen = set()
    while True:
        try:
            for spot in check().get("spots", []):
                if all(a == "Available" for a in spot["availabilities"].values()):
                    if spot["name"] not in seen:
                        seen.add(spot["name"])
                        notify(f"{spot['name']} just opened for {START_DATE}!")
        except Exception as e:
            print("Check failed:", e, file=sys.stderr)
        time.sleep(CHECK_EVERY_SEC)

if __name__ == "__main__":
    main()
