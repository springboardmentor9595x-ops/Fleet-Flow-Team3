import asyncio
import json

import websockets


VEHICLE_ID = "3006e2e3-4cea-4ae7-aa49-d9a1f4e9709f"

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

                print("GPS sent:")
                print(gps_data)

                # Wait briefly for backend response
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=3,
                    )

                    print("Response:")
                    print(response)

                except asyncio.TimeoutError:
                    print(
                        "No response received, continuing..."
                    )

                print("-" * 50)

                # Wait before next GPS point
                await asyncio.sleep(2)

            print("\nGPS simulation completed.")

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