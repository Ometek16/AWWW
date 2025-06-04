import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RouletteConsumer(AsyncWebsocketConsumer):
    ROULETTE_GROUP_NAME = 'roulette_group'

    async def connect(self):
        await self.accept()
        print(f"WebSocket connected: {self.channel_name}")
        await self.channel_layer.group_add(
            self.ROULETTE_GROUP_NAME,
            self.channel_name
        )
        print(f"Added {self.channel_name} to group {self.ROULETTE_GROUP_NAME}")

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected: {self.channel_name} with code {close_code}")
        await self.channel_layer.group_discard(
            self.ROULETTE_GROUP_NAME,
            self.channel_name
        )
        print(f"Removed {self.channel_name} from group {self.ROULETTE_GROUP_NAME}")

    async def roulette_message(self, event):
        await self.send(text_data=json.dumps(event)) # <--- KLUCZOWA ZMIANA!
        print(f"Sent message to {self.channel_name}: {event}") # Zmień print, żeby pokazywał cały event