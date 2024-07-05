import asyncio
import json
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, PeerIdInvalid
from config import BOT_TOKENS  # Import BOT_TOKENS from config.py

# Load JSON data from file
def load_json_data(file_name):
    with open(file_name, "r") as file:
        data = json.load(file)
    return data

# Function to forward messages
async def forward_messages(bot, messages, target_channel_id):
    try:
        # Send the batch name as the first message to the target channel and pin it
        batch_name = messages[0]["batch"]
        pinned_message = await bot.send_message(target_channel_id, f"Batch: {batch_name}")

        try:
            await bot.pin_chat_message(target_channel_id, pinned_message.message_id)
        except Exception as e:
            print(f"Failed to pin message: {e}")
        
        # Forward the messages to the target channel
        for msg in messages:
            while True:
                try:
                    await bot.get_chat(target_channel_id)  # Ensure the bot has met the target channel
                    await bot.copy_message(
                        chat_id=target_channel_id,
                        from_chat_id=msg["chatid"],
                        message_id=msg["msgid"]
                    )
                    break
                except FloodWait as e:
                    print(f"Rate limit exceeded. Waiting for {e.value} seconds.")
                    await asyncio.sleep(e.value)
                except PeerIdInvalid as e:
                    print(f"Failed to forward message ID {msg['msgid']}: Peer ID invalid.")
                    break
                except Exception as e:
                    print(f"Failed to forward message ID {msg['msgid']}: {e}")
                    break
        print("Done forwarding messages.")
    except Exception as e:
        print(f"Error during message forwarding: {e}")

# Initialize clients for each bot token
clients = [Client(f"bot_{i+1}", bot_token=token) for i, token in enumerate(BOT_TOKENS)]

# Command to trigger message forwarding
@Client.on_message(filters.command("forward") & filters.private)
async def handle_forward_command(client, message):
    try:
        # Check if a JSON file is attached
        if not message.document or not message.document.file_name.endswith(".json"):
            await message.reply_text("Please upload a JSON file.")
            return
        
        # Download and read the JSON data
        json_file = await message.download()
        messages = load_json_data(json_file)

        # Ask for the target channel ID where messages should be forwarded
        target_channel_msg = await message.reply_text("Enter the target channel ID where you want to forward the messages:")
        response = await client.ask(target_channel_msg.chat.id, "Provide the target channel ID:")
        target_channel_id = int(response.text.strip())

        # Determine which bot to use based on the modulo operation
        bot_index = 0
        for msg in messages:
            current_bot = clients[bot_index]
            await forward_messages(current_bot, [msg], target_channel_id)
            bot_index = (bot_index + 1) % len(clients)

        await message.reply_text("Done ✅")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# Start all clients
async def start_clients():
    for client in clients:
        await client.start()

# Run the clients
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(start_clients())
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        for client in clients:
            asyncio.get_event_loop().run_until_complete(client.stop())
