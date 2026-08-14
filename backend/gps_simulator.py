import asyncio
import json

import websockets


import sys

VEHICLE_ID = sys.argv[1] if len(sys.argv) > 1 else "72793178-ddc6-45d5-96ad-91457c1c31fb"

WS_URL = f"ws://127.0.0.1:8000/ws/tracking/{VEHICLE_ID}"


GPS_POINTS = [
    (28.4744, 77.5040, 20),
    (28.4746, 77.5043, 25),
    (28.4749, 77.5047, 30),
    (28.4752, 77.5051, 35),
    (28.4755, 77.5055, 40),
    (28.4758, 77.5059, 35),
]


async def main():

    print("Connecting to FleetFlow WebSocket...")

    try:
        async with websockets.connect(
            WS_URL,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=5,
        ) as websocket:

            print("Connected to FleetFlow WebSocket")
            print("Starting GPS simulation...\n")

            while True:
                for latitude, longitude, speed in GPS_POINTS:

                    gps_data = {
                        "latitude": latitude,
                        "longitude": longitude,
                        "speed": speed,
                        "recorded_time": "2026-08-11T18:00:00",
                    }

                    # Send GPS data
                    await websocket.send(
                        json.dumps(gps_data)
                    )

                    print("GPS sent:", speed, "km/h")

                    # Wait briefly for backend response
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=3,
                        )

                    except asyncio.TimeoutError:
                        pass

                    # Wait before next GPS point
                    await asyncio.sleep(2)

    except websockets.exceptions.ConnectionClosed as error:
        print(
            f"\nWebSocket connection closed: {error}"
        )

    except Exception as error:
        print(
            f"\nGPS simulator error: {error}"
        )


if __name__ == "__main__":
    asyncio.run(main())