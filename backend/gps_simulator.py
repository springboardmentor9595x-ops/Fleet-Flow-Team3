import asyncio
import json
import urllib.request
import urllib.error

# ================================================================
# FleetFlow Multi-Vehicle GPS Simulator
# Fetches all vehicles from the API and simulates GPS for each
# ================================================================

BASE_URL = "http://127.0.0.1:8000"
WS_BASE  = "ws://127.0.0.1:8000"

# Default credentials — change if needed
EMAIL    = "admin@fleetflow.com"
PASSWORD = "pass123"

# Simulation route (loops endlessly): lat, lon, speed_km/h
ROUTE = [
    (28.6139, 77.2090, 20),
    (28.6150, 77.2110, 30),
    (28.6162, 77.2130, 40),
    (28.6175, 77.2150, 35),
    (28.6188, 77.2170, 45),
    (28.6200, 77.2190, 50),
    (28.6188, 77.2210, 40),
    (28.6175, 77.2190, 35),
    (28.6162, 77.2170, 30),
    (28.6150, 77.2150, 25),
]

# Small per-vehicle offset so markers don't stack on top of each other
OFFSETS = [
    (0.000,  0.000),
    (0.002,  0.003),
    (-0.002, 0.004),
    (0.004, -0.002),
    (-0.003,-0.003),
]


def get_token():
    """Login and return JWT token."""
    import urllib.parse
    data = urllib.parse.urlencode({
        "username": EMAIL,
        "password": PASSWORD,
    }).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())["access_token"]


def get_vehicles(token):
    """Fetch all vehicle IDs and registration numbers."""
    req = urllib.request.Request(
        f"{BASE_URL}/vehicles/",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as res:
        vehicles = json.loads(res.read())
    return [(v["vehicle_id"], v.get("registration_number", v["vehicle_id"])) for v in vehicles]


async def simulate_vehicle(vehicle_id, reg_number, offset, delay_start):
    """Simulate GPS for a single vehicle."""
    import websockets

    ws_url = f"{WS_BASE}/ws/tracking/{vehicle_id}"
    lat_off, lon_off = offset
    await asyncio.sleep(delay_start)  # stagger starts

    while True:
        try:
            print(f"[{reg_number}] Connecting to {ws_url}")
            async with websockets.connect(
                ws_url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5,
            ) as ws:
                print(f"[{reg_number}] Connected ✅")
                idx = 0
                while True:
                    lat, lon, speed = ROUTE[idx % len(ROUTE)]
                    payload = {
                        "latitude":  round(lat + lat_off, 6),
                        "longitude": round(lon + lon_off, 6),
                        "speed":     speed,
                        "recorded_time": "2026-08-14T00:00:00",
                    }
                    await ws.send(json.dumps(payload))
                    print(f"[{reg_number}] GPS → lat={payload['latitude']}, lon={payload['longitude']}, speed={speed} km/h")
                    try:
                        resp = await asyncio.wait_for(ws.recv(), timeout=3)
                        data = json.loads(resp)
                        if data.get("event"):
                            print(f"[{reg_number}] 🔔 Event: {data['event']}")
                    except asyncio.TimeoutError:
                        pass
                    idx += 1
                    await asyncio.sleep(2)

        except Exception as e:
            print(f"[{reg_number}] ❌ Error: {e}. Reconnecting in 3s...")
            await asyncio.sleep(3)


import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def main():
    print("=" * 60)
    print("  FleetFlow Multi-Vehicle GPS Simulator")
    print("=" * 60)

    try:
        token = get_token()
        print(f"✅ Logged in as {EMAIL}")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"❌ Login failed: HTTP 401 Unauthorized")
            print(f"   The user '{EMAIL}' does not exist or wrong password.")
            print(f"   Please sign up with email '{EMAIL}' and password '{PASSWORD}' in the Frontend Dashboard, then create a vehicle.")
        else:
            print(f"❌ Login failed: {e}")
        return
    except Exception as e:
        print(f"❌ Login failed: {e}")
        print("   Check that the backend is running.")
        return

    try:
        vehicles = get_vehicles(token)
    except Exception as e:
        print(f"❌ Failed to fetch vehicles: {e}")
        return

    if not vehicles:
        print("⚠️  No vehicles found. Register vehicles first via /vehicles/.")
        return

    print(f"\nFound {len(vehicles)} vehicle(s):")
    for vid, reg in vehicles:
        print(f"  • {reg}  ({vid})")

    print("\nStarting GPS simulation for all vehicles...\n")

    tasks = []
    for i, (vid, reg) in enumerate(vehicles):
        offset = OFFSETS[i % len(OFFSETS)]
        # Stagger starts by 0.5s per vehicle
        task = asyncio.create_task(simulate_vehicle(vid, reg, offset, delay_start=i * 0.5))
        tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        import websockets
    except ImportError:
        print("Installing websockets...")
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        import websockets

    asyncio.run(main())