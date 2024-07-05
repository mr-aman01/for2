import asyncio
import json
from pyrogram import Client, filters
from config import BOT_TOKENS, API_ID, API_HASH

# Global variable to hold the JSON data
json_data = None

# Load JSON data from file
def load_json_data(filename):
    global json_data
    with open(filename, "r") as file:
        json_data = json.load(file)

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
            await message.reply_to_message.download(file_name="forward_data.json")
            load_json_data("forward_data.json")
            await message.reply_text("JSON file received and loaded successfully!")

            # Forward messages
            if json_data:
                target_channel_id = 123456789  # Replace with your target channel ID
                await forward_messages(client, json_data, target_channel_id)
                await message.reply_text("Done ✅")

    await bot.start()

async def main():
    tasks = []
    for token in BOT_TOKENS:
        tasks.append(start_bot(token))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
