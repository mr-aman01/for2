# main.py

import asyncio
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from config import BOT_TOKENS, API_ID, API_HASH

# Global variable to hold the JSON data
json_data = None

# Load JSON data from file
def load_json_data():
    global json_data
    with open("data.json", "r") as file:
        json_data = json.load(file)

# Pin a message with batch name
async def pin_message(client, target_chat_id, batch_name):
    message = await client.send_message(target_chat_id, f"Batch Name: {batch_name}")
    await client.pin_chat_message(target_chat_id, message.message_id)

# Forward messages from JSON data
async def forward_messages(client, data, target_channel_id):
    for msg in data:
        try:
            await client.copy_message(chat_id=target_channel_id,
                                      from_chat_id=msg["chatid"],
                                      message_id=msg["msgid"])
        except Exception as e:
            print(f"Failed to forward message ID {msg['msgid']}: {e}")

# Initialize and start bot
async def start_bot(token):
    bot = Client("bot", bot_token=token, api_id=API_ID, api_hash=API_HASH)

    @bot.on_message(filters.command("forward"))
    async def handle_forward_command(client, message):
        global json_data
        if message.reply_to_message and message.reply_to_message.document:
            # Download the JSON file
            await message.reply_to_message.download(file_name="data.json")
            load_json_data()
            await message.reply_text("JSON file received and loaded successfully!")

    await bot.start()
    await bot.idle()

async def main():
    tasks = []
    for token in BOT_TOKENS:
        tasks.append(start_bot(token))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
