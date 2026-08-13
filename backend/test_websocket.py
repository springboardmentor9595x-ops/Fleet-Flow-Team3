import asyncio
import json
import websockets

VEHICLE_ID = "3006e2e3-4cea-4ae7-aa49-d9a1f4e9709f"


async def test():
    url = f"ws://127.0.0.1:8000/ws/tracking/{VEHICLE_ID}"

    async with websockets.connect(url) as websocket:
        print("Connected to FleetFlow WebSocket")

        gps_data = {
            "latitude": 28.4744,
            "longitude": 77.5040,
            "speed": 35,
            "recorded_time": "2026-08-11T18:00:00"
        }

        await websocket.send(json.dumps(gps_data))

        print("GPS data sent:")
        print(gps_data)

        response = await websocket.recv()

        print("Response:")
        print(response)


asyncio.run(test())