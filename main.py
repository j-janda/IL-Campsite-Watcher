# main.py — ExploreMoreIL cancellation watcher
import os, time, requests, datetime, sys, json

# ---------- EDIT THESE FOUR LINES ----------
LOCATION_ID     = 201                # Eldon Hazlet; change if needed
START_DATE      = "2025-06-28"       # arrival
END_DATE        = "2025-06-29"       # departure (next morning)
CHECK_EVERY_SEC = 300                # poll every 5 min (be nice)
# -------------------------------------------

#––– Leave these as generic names; secrets live in Railway Variables –––
PUSH_USER  = os.environ["PUSHOVER_USER"]
PUSH_TOKEN = os.environ["PUSHOVER_TOKEN"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (campsite-watcher)",   # looks like a browser
    "Accept":      "application/json, text/plain, */*",
}

def notify(msg: str) -> None:
    """Send a Pushover push notification."""
    try:
        requests.post("https://api.pushover.net/1/messages.json",
                      data={
                          "token":   PUSH_TOKEN,
                          "user":    PUSH_USER,
                          "title":   "ExploreMoreIL site open!",
                          "message": msg,
                      },
                      timeout=10)
    except Exception as exc:
        print("Pushover send failed:", exc, file=sys.stderr)

def check() -> dict:
    """Query ExploreMoreIL for availability JSON. Return {} on any failure."""
    url = (
        "https://camp.exploremoreil.com/api/availability"
        f"?locationId={LOCATION_ID}"
        f"&startDate={START_DATE}&endDate={END_DATE}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as exc:
        print("HTTP request failed:", exc, file=sys.stderr)
        return {}

    # If the site didn’t hand us JSON, log the first 300 chars so we know why.
    if "application/json" not in r.headers.get("Content-Type", ""):
        print(f"Non-JSON response {r.status_code}: {r.text[:300]!r}",
              file=sys.stderr)
        return {}

    try:
        return r.json()
    except json.JSONDecodeError as exc:
        print("JSON decode failed:", exc, "first 200:", r.text[:200],
              file=sys.stderr)
        return {}

def main():
    seen = set()  # remember which sites we’ve already alerted on
    while True:
        data = check()
        # data structure: {"spots": [ { "name": "...", "availabilities": {...}}, … ]}
        for spot in data.get("spots", []):
            # A spot is good if *all* nights in our range read "Available"
            if all(a == "Available" for a in spot["availabilities"].values()):
                if spot["name"] not in seen:
                    seen.add(spot["name"])
                    notify(f"{spot['name']} just opened for {START_DATE}!")
                    print(f"🔔 {spot['name']} available — alert sent", file=sys.stderr)
        time.sleep(CHECK_EVERY_SEC)

if __name__ == "__main__":
    main()
