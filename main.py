# main.py  –  ExploreMoreIL one-night availability watcher (POST version)
import os, time, requests, sys, json

# ─────────── CONFIG – EDIT THE NEXT FIVE LINES ─────────── #
LOCATION_ID = "201"                      # Eldon Hazlet; change if needed
ARRIVAL     = "06/28/2025"               # mm/dd/yyyy
DEPART      = "06/29/2025"               # mm/dd/yyyy (next morning)
CHECK_EVERY = 300                        # seconds between polls (5 min)
API_URL     = (
    "https://pa2wh3n7xa.execute-api.us-east-1.amazonaws.com/"
    "prod/v1/tenant/illinois/Spot/availability"
)
# ────────────────────────────────────────────────────────── #

# Pushover secrets come from Railway ▸ Variables
PUSH_USER  = os.environ["PUSHOVER_USER"]
PUSH_TOKEN = os.environ["PUSHOVER_TOKEN"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (campsite-watcher)",
    "Accept":      "application/json",
    "Origin":      "https://camp.exploremoreil.com",
    "Referer":     "https://camp.exploremoreil.com/",
}

POST_BODY = {
    "locationId": LOCATION_ID,
    "startDate":  ARRIVAL,
    "endDate":    DEPART,
    "lockCode":   None,
    "selectedSpotTypes":           None,
    "selectedProductClassifications": None,
    "selectedAttributes":          None,
    "selectedSpotId":              None,
    "onlyShowAvailable":           False,   # we’ll filter ourselves
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
    """POST to the API and return decoded JSON, or {} on any failure."""
    try:
        r = requests.post(API_URL, headers=HEADERS, json=POST_BODY, timeout=20)
    except Exception as exc:
        print("HTTP request failed:", exc, file=sys.stderr)
        return {}

    if "application/json" not in r.headers.get("Content-Type", ""):
        print("Non-JSON response:", r.status_code, r.text[:200], file=sys.stderr)
        return {}

    try:
        return r.json()
    except json.JSONDecodeError as exc:
        print("JSON decode failed:", exc, file=sys.stderr)
        return {}

def spot_is_available(spot: dict) -> bool:
    """
    ExploreMoreIL’s schema can be either:
        spot["availability"] == "Available"
      --or--
        spot["availabilities"]["2025-06-28"] == "Available"
    This helper handles both.
    """
    if "availability" in spot:
        return spot["availability"] == "Available"
    if "availabilities" in spot and isinstance(spot["availabilities"], dict):
        return all(v == "Available" for v in spot["availabilities"].values())
    return False

def main():
    alerted = set()                 # keep track of sites we already pinged
    while True:
        data = fetch_json()
        spots = data.get("spots") or data.get("data") or []
        for spot in spots:
            if spot_is_available(spot):
                name = spot.get("name", f"Spot {spot.get('spotId')}")
                if name not in alerted:
                    notify(f"{name} just opened for {ARRIVAL}!")
                    alerted.add(name)
                    print("🔔 Alert sent for", name, file=sys.stderr)
        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    main()
