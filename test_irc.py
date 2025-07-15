import asyncio
import websockets

# Replace with your bot's username and OAuth token (starting with 'oauth:')
USERNAME = "thecherryo_bot"
TOKEN = "oauth:8y16tjg3mfmsq6ow4p8i5n0pdj7h1o"  # Make sure it's "oauth:<token>"
CHANNEL = "thecherryo"

async def connect_to_twitch():
    uri = "wss://irc-ws.chat.twitch.tv:443"

    async with websockets.connect(uri) as websocket:
        # Send authentication messages
        await websocket.send(f"PASS {TOKEN}")
        await websocket.send(f"NICK {USERNAME}")
        await websocket.send(f"JOIN #{CHANNEL}")

        print(f"Connected to #{CHANNEL}'s chat as {USERNAME}")

        while True:
            try:
                message = await websocket.recv()
                print(">>", message.strip())

                # Respond to PINGs to stay connected
                if message.startswith("PING"):
                    await websocket.send("PONG :tmi.twitch.tv")

            except websockets.exceptions.ConnectionClosed:
                print("Connection closed, reconnecting...")
                break

if __name__ == "__main__":
    asyncio.run(connect_to_twitch())
