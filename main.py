# main.py  –  Eldon Hazlet one-night watcher  (uses isSpotAvailable)
import os, time, requests, sys, json

# ─── CONFIGURE THESE ─────────────────────────────────────────────────
LOCATION_ID   = "201"         # Eldon Hazlet; change if needed
ARRIVAL       = "06/28/2025"  # mm/dd/yyyy
DEPART        = "06/29/2025"  # mm/dd/yyyy (next morning)
CHECK_EVERY   = 300           # seconds between polls (5 min)
API_URL       = ("https://pa2wh3n7xa.execute-api.us-east-1.amazonaws.com/"
                 "prod/v1/tenant/illinois/Spot/availability")
# ─────────────────────────────────────────────────────────────────────

# Pushover keys live in Railway ▸ Variables
PUSH_USER  = os.environ["PUSHOVER_USER"]
PUSH_TOKEN = os.environ["PUSHOVER_TOKEN"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (campsite-watcher)",
    "Accept": "application/json",
    "Origin": "https://camp.exploremoreil.com",
    "Referer": "https://camp.exploremoreil.com/",
}

POST_BODY = {
    "locationId": LOCATION_ID,
    "startDate":  ARRIVAL,
    "endDate":    DEPART,
    "lockCode":   None,
    "selectedSpotTypes":             None,
    "selectedProductClassifications": None,
    "selectedAttributes":            None,
    "selectedSpotId":                None,
    "onlyShowAvailable":             False
}

def notify(msg: str) -> None:
    try:
        requests.post("https://api.pushover.net/1/messages.json",
                      data={"token": PUSH_TOKEN, "user": PUSH_USER,
                            "title": "ExploreMoreIL site open!",
                            "message": msg},
                      timeout=10)
    except Exception as exc:
        print("Pushover send failed:", exc, file=sys.stderr)

def fetch_json() -> dict:
    try:
        r = requests.post(API_URL, headers=HEADERS, json=POST_BODY, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        print("HTTP error:", exc, file=sys.stderr)
        return {}
    if "application/json" not in r.headers.get("Content-Type", ""):
        print("HTML instead of JSON (first 120 chars):", r.text[:120],
              file=sys.stderr)
        return {}
    try:
        return r.json()
    except json.JSONDecodeError as exc:
        print("JSON decode failed:", exc, file=sys.stderr)
        return {}

def main():
    alerted = set()
    poll = 0
    while True:
        poll += 1
        data = fetch_json()
        spots = data.get("spots") or data.get("data") or []
        found = False
        for spot in spots:
            if spot.get("isSpotAvailable") is True:      # ← key you found
                name = spot.get("name", f"Spot {spot.get('id')}")
                found = True
                if name not in alerted:
                    notify(f"{name} just opened for {ARRIVAL}!")
                    alerted.add(name)
                    print(f"🔔  Alert sent for {name}", file=sys.stderr)
        # heartbeat so you always see something every poll
        print(f"Poll {poll}: {'FOUND availability' if found else 'none'} "
              f"({len(spots)} spots scanned)", file=sys.stderr)
        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    main()
