import asyncio
import json

import websockets


async def main() -> None:
    uri = "ws://127.0.0.1:8000/ws/device-states"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")

        while True:
            message = await websocket.recv()

            try:
                data = json.loads(message)
                print("Received WebSocket message:")
                print(json.dumps(data, ensure_ascii=False, indent=2))
            except json.JSONDecodeError:
                print("Received raw message:")
                print(message)


if __name__ == "__main__":
    asyncio.run(main())