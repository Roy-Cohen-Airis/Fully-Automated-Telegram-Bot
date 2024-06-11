import asyncio
import json
from telethon.sync import TelegramClient
from telethon.tl.types import MessageService

class TelegramForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)
        
    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))
            
    last_message_ids = {}  # Dictionary to store the last message ID for each chat
            
    async def forward_media_message(self, destination_channel_id, message):
        if message.photo:
            await self.client.send_file(destination_channel_id, message.photo, caption=message.text)
        elif message.video:
            await self.client.send_file(destination_channel_id, message.video, caption=message.text)
    
    async def list_chats(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))
        dialogs = await self.client.get_dialogs()
        chats_file = open(f"chats_of_{self.phone_number}.txt", "w", encoding="utf-8")
        for dialog in dialogs:
            print(f"Chat ID: {dialog.id}, Title: {dialog.title}")
            chats_file.write(f"Chat ID: {dialog.id}, Title: {dialog.title} \n")
        chats_file.close()
        print("List of groups printed successfully!")
        
    async def forward_messages_to_channel(self, source_channel_ids, destination_channel_id):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            await self.client.sign_in(self.phone_number, input('Enter the code: '))
        last_message_ids = {}
        for chat_id in source_channel_ids:
            last_message_ids[chat_id] = (await self.client.get_messages(chat_id, limit=1))[0].id
        while True:
            print("Checking for messages and forwarding them...")
            for chat_id in source_channel_ids:
                messages = await self.client.get_messages(chat_id, min_id=last_message_ids[chat_id], limit=None)
                for message in reversed(messages):
                    if message.media:
                        await self.forward_media_message(destination_channel_id, message)
                        print("Message with media forwarded")
                    else:
                        await self.client.forward_messages(destination_channel_id, message)
                        print("Text Message forwarded")
                    last_message_ids[chat_id] = max(last_message_ids[chat_id], message.id)
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
    
   
    #print("List Chats")
    #await forwarder.list_chats()
    # Pre-configured source and destination channels
    source_channel_sets = [
        ([-1001421349015,-1001878410681,-1001147552061,-1001226199638,-1001186306992,-1001475851155, -1001269989140,-1001748568448,-1001452511519,-1001574173609,-1001406113886,-1001327147906,-1001430460151,-1001285011113,-1001091851405,-1001179278075,-1001007352301,-1001773838153,-1001007216566,-1001335679367,-1002013905167,-1001813502918,-1001681314755,-1001666879095,-1001847467060,-1001519645101,-1001236978606,-1001865897759,-1001508053355,-1001759225147,-1001812691700,-1001618513432,-1001351007284], -4201337742),
        ([-1001406113886,-1001167251135,-1001465878333,-1001450174131,-1001764803881,-1001445744051,-1002057790816,-1001164580231,-4276673834], -4273847685)
            ]

    tasks = [forwarder.forward_messages_to_channel(source_channel_ids, destination_channel_id) for source_channel_ids, destination_channel_id in source_channel_sets]
    await asyncio.gather(*tasks)
        
if __name__ == "__main__":
    asyncio.run(main())
