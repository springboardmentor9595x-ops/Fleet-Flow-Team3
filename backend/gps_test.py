import asyncio
import json
import websockets


VEHICLE_ID = "3006e2e3-4cea-4ae7-aa49-d9a1f4e9709f"

URL = (
    f"ws://127.0.0.1:8000"
    f"/ws/tracking/{VEHICLE_ID}"
)

# Destination used by FleetFlow
DESTINATION_LAT = 28.4744
DESTINATION_LON = 77.5040


async def main():

    # Start vehicle AWAY from destination
    latitude = 28.4831
    longitude = 77.5127

    speed = 30

    async with websockets.connect(URL) as ws:

        print("====================================")
        print("FleetFlow GPS Simulator Started")
        print(f"Vehicle: {VEHICLE_ID}")
        print("====================================")

        while True:

            gps_data = {
                "latitude": latitude,
                "longitude": longitude,
                "speed": speed,
            }

            await ws.send(
                json.dumps(gps_data)
            )

            response = await ws.recv()

            data = json.loads(response)

            print(
                f"GPS → "
                f"Lat: {data['latitude']} | "
                f"Lon: {data['longitude']} | "
                f"Speed: {data['speed']} km/h | "
                f"Distance: {data['distance_to_destination']} m | "
                f"Status: {data['status']}"
            )

            # Move vehicle TOWARD destination
            latitude -= 0.00010
            longitude -= 0.00010

            # Stop when destination is reached
            if (
                latitude <= DESTINATION_LAT
                and longitude <= DESTINATION_LON
            ):
                latitude = DESTINATION_LAT
                longitude = DESTINATION_LON

                print("====================================")
                print("🚚 Vehicle reached destination")
                print("====================================")

            await asyncio.sleep(2)


asyncio.run(main())