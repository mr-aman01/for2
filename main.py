import json
import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from config import Config

# Initialize the bot clients
bot1 = Client(
    "forward_bot1",
    bot_token=Config.BOT_TOKEN1,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

bot2 = Client(
    "forward_bot2",
    bot_token=Config.BOT_TOKEN2,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

bot3 = Client(
    "forward_bot3",
    bot_token=Config.BOT_TOKEN3,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# List of bots for round-robin
bots = [bot1, bot2, bot3]

# Store the loaded messages and the file name
messages = []
file_name = ""

# Load the JSON data from the uploaded file
async def load_json_data(file_path):
    global messages, file_name
    with open(file_path, "r") as file:
        messages = json.load(file)
    file_name = os.path.basename(file_path)

# Command to start the bot
@bot1.on_message(filters.command("start") & filters.user(Config.AUTH_USERS))
async def start(client, message):
    await message.reply_text("Bot started! Use /forward to begin forwarding messages.")

# Command to initiate forwarding
@bot1.on_message(filters.command("forward") & filters.user(Config.AUTH_USERS))
async def forward_messages(client, message):
    await message.reply_text("Please upload the JSON file.")
    
    # Wait for the user to upload the JSON file
    @bot1.on_message(filters.document & filters.user(Config.AUTH_USERS))
    async def handle_document(client, document_message):
        if document_message.document.file_name.endswith(".json"):
            file_path = await document_message.download()
            await load_json_data(file_path)  # Load the JSON data from the file

            # Send the file name to the target channel
            await message.reply_text(f"File '{document_message.document.file_name}' received. Send the channel ID where you want to forward the messages:")
            
            os.remove(file_path)  # Clean up the file after loading

            # Wait for the user to reply with the target channel ID
            @bot1.on_message(filters.text & filters.user(Config.AUTH_USERS))
            async def handle_channel_id(client, channel_id_message):
                target_channel_id = int(channel_id_message.text)
                
                await message.reply_text("Forwarding messages...")

                # Send the file name as the first message to the target channel
                await bot1.send_message(target_channel_id, f"Forwarding messages from '{file_name}'")

                # Forward the messages to the target channel
                bot_index = 0
                for msg in messages:
                    current_bot = bots[bot_index]
                    while True:
                        try:
                            await current_bot.get_chat(target_channel_id)  # Ensure the bot has met the target channel
                            await current_bot.copy_message(
                                chat_id=target_channel_id,
                                from_chat_id=msg["chatid"],
                                message_id=msg["msgid"]
                            )
                            break
                        except FloodWait as e:
                            await message.reply_text(f"Rate limit exceeded. Waiting for {e.value} seconds.")
                            await asyncio.sleep(e.value)
                        except Exception as e:
                            await message.reply_text(f"Failed to forward message ID {msg['msgid']}: {e}")
                            break
                    bot_index = (bot_index + 1) % len(bots)

                await client.send_message(target_channel_id, "Done ✅")
                await message.reply_text("Done forwarding messages.")
                # Remove the inner handler after use
                bot1.remove_handler(handle_channel_id)

        else:
            await message.reply_text("Uploaded file is not a JSON file. Please try again.")
        # Remove the inner handler after use
        bot1.remove_handler(handle_document)

# Start the bots
bot1.start()
bot2.start()
bot3.start()

# Run the main event loop
asyncio.get_event_loop().run_forever()
