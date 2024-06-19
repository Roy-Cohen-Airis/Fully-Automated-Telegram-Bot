import asyncio
import json
from telethon.sync import TelegramClient
from telethon.tl.types import MessageService
from telethon.errors import ChatForwardsRestrictedError  # Import ChatForwardsRestrictedError
import re

def contains_hebrew(text):
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]+(?:[\s\u0020]+[\u0590-\u05FF]+)*')  # Pattern for Hebrew characters and spaces
    return bool(hebrew_pattern.search(text))

def contains_arabic(text):
    arabic_pattern = re.compile(r'[\u0600-\u06FF]+(?:[\s\u0020]+[\u0600-\u06FF]+)*')  # Pattern for Arabic characters and spaces
    return bool(arabic_pattern.search(text))

class TelegramForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)
        self.source_channels_arabic = []
        self.source_channels_hebrew = []
            
    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))
            
    async def list_chats(self):
        print('List chats called')
        await self.client.connect()
        print('Client connected')
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))
        print('User authorized')

        dialogs = await self.client.get_dialogs()
        print('Got dialogs')
        self.source_channels_arabic = []
        self.source_channels_hebrew = []

        for dialog in dialogs:
            if dialog.title not in ['Settlers Bot', 'Arab Telegram Bot', 'Ben Rotem']:

                if contains_arabic(dialog.title) or  dialog.title in ['תרגום מקורות - איו"ש ומזרח י-ם', '301 העולם הערבי'] :

                    self.source_channels_arabic.append(dialog)

                    print (f' {dialog.title[::-1]} , {dialog.id} , Added to Arabic')

                else:

                    if contains_hebrew(dialog.title):

                        self.source_channels_hebrew.append(dialog)

                        print (f' {dialog.title[::-1]} , {dialog.id} , Added to Hebrew')

        print('Disconnecting client')
        await self.client.disconnect()
        print('Client disconnected')
        
    async def forward_media_message(self, destination_channel_id, message):
        if message.photo:
            await self.client.send_file(destination_channel_id, message.photo, caption=message.text)
        elif message.video:
            await self.client.send_file(destination_channel_id, message.video, caption=message.text)
    
    async def forward_messages_to_channel(self, source_channel_ids, destination_channel_id):
        while True:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                await self.client.send_code_request(self.phone_number)
                await self.client.sign_in(self.phone_number, input('Enter the code: '))
            
            last_message_ids = {}
            for chat_id in source_channel_ids:
                last_message_ids[chat_id.id] = (await self.client.get_messages(chat_id.id, limit=1))[0].id
            
            print("Starting message forwarding...")
            while True:
                print("Checking for messages and forwarding them...")
                for chat_id in source_channel_ids:
                    try:
                        messages = await self.client.get_messages(chat_id.id, min_id=last_message_ids[chat_id.id], limit=None)
                        for message in reversed(messages):
                            if not isinstance(message, MessageService):
                                if message.media:
                                    await self.forward_media_message(destination_channel_id, message)
                                    print("Message with media forwarded")
                                else:
                                    await self.client.forward_messages(destination_channel_id, message)
                                    print("Text Message forwarded")
                                last_message_ids[chat_id.id] = max(last_message_ids[chat_id.id], message.id)
                    except ChatForwardsRestrictedError as e:
                        print(f"Skipping chat {chat_id.id} as message forwarding is restricted.")
                await asyncio.sleep(1)

async def main():
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        config = {}
        
    api_id = config.get("api_id") or input("Enter your API ID: ")
    api_hash = config.get("api_hash") or input("Enter your API Hash: ")
    phone_number = config.get("phone_number") or input("Enter your phone number: ")
    forwarder = TelegramForwarder(api_id, api_hash, phone_number)
    
    print("Starting Forwarding Messages:")
    
    await forwarder.start()
    await forwarder.list_chats()

    # Pre-configured source and destination channels
    source_channel_sets = [
        (forwarder.source_channels_arabic, -4201337742),
        (forwarder.source_channels_hebrew, -4273847685)
    ]
    tasks = [forwarder.forward_messages_to_channel(source_channel_ids, destination_channel_id) for source_channel_ids, destination_channel_id in source_channel_sets]
    
    await asyncio.gather(*tasks)
    
if __name__ == "__main__":
    asyncio.run(main())









