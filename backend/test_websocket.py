import asyncio
import websockets
import json

async def test():
    url = "ws://127.0.0.1:8000/gps/ws/2c22ec37-5616-479b-bf90-e3d1f87d828b"

    async with websockets.connect(url) as websocket:
        print("WebSocket connected!")

        message = {
            "latitude": 11.0168,
            "longitude": 76.9558,
            "speed": 45
        }

        await websocket.send(json.dumps(message))

        response = await websocket.recv()

        print("Received:")
        print(response)

asyncio.run(test())


@'
import asyncio
import json
import websockets

vehicle_id = "31a4e79f-80b4-4412-84c1-06722ecbb6ec"

async def live_tracking():
    url = f"ws://127.0.0.1:8000/gps/ws/{vehicle_id}"

    async with websockets.connect(url) as socket:

        lat = 12.9716
        lon = 77.5946

        while True:
            await socket.send(json.dumps({
                "latitude": lat,
                "longitude": lon,
                "speed": 42
            }))

            print(f"Sent: {lat}, {lon}")

            lat += 0.0005
            lon += 0.0005

            await asyncio.sleep(3)

asyncio.run(live_tracking())
'@ | .\venv\Scripts\python.exe -