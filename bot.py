import discord
from discord.ext import tasks, commands
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))  # Ensure this is an integer
CHANNEL_ID_TO_POST_UPDATES = int(os.getenv('CHANNEL_ID_TO_POST_UPDATES'))  # Ensure this is an integer

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.message_content = True  # Ensure this is included if you want to read message content

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('Connected to the following guilds:')
    for guild in bot.guilds:
        print(f'{guild.name} (ID: {guild.id})')
        channels = await guild.fetch_channels()
        for channel in channels:
            print(f"Channel: {channel.name} (ID: {channel.id})") 
    update_threads_list.start()

@tasks.loop(minutes=1)
async def update_threads_list():
    guild = await bot.fetch_guild(GUILD_ID)
    if not guild:
        print(f"Guild with ID {GUILD_ID} not found.")
        return

    try:
        update_channel = await guild.fetch_channel(CHANNEL_ID_TO_POST_UPDATES)
    except discord.NotFound:
        print(f"Channel with ID {CHANNEL_ID_TO_POST_UPDATES} not found (NotFound).")
        return
    except discord.HTTPException as e:
        print(f"An HTTPException occurred: {e}")
        return

    print(f"Found channel: {update_channel.name} (ID: {update_channel.id})")

    message_content = "### Current Channels and Threads:\n"
    channels = await guild.fetch_channels()
    print(f"Channels: {[channel.name for channel in channels]}")

    for channel in channels:
        if isinstance(channel, discord.TextChannel):
            print(f"Fetching threads for channel: {channel.name} (ID: {channel.id})")
            try:
                threads = [thread async for thread in channel.archived_threads()]  # Collect threads from async generator
                print(f"Fetched {len(threads)} threads from channel: {channel.name}")
                
                if threads:
                    message_content += f"\n**{channel.name}**:\n"
                    
                    for thread in threads:
                        message_content += f"- {thread.name}\n"
                
            except discord.HTTPException as e:
                print(f"An HTTPException occurred while fetching threads: {e}")
                continue

    async for message in update_channel.history(limit=10):
        if message.author == bot.user:
            if message.content != message_content:
                await message.edit(content=message_content)
                print(f"Updated message in {update_channel.name}")
            return
    
    await update_channel.send(content=message_content)
    print(f"Sent new message in {update_channel.name}")
    
@update_threads_list.before_loop
async def before_update_threads_list():
    await bot.wait_until_ready()

bot.run(TOKEN)