import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up the bot with the necessary intents
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print("\nServers:")
    count = 0
    for guild in bot.guilds:
        print(f"- ({guild.id}) {guild.name}")
        count += 1
    print(f"Total servers: {count}\n")
    await bot.close()

# Run the bot
bot.run(TOKEN)
