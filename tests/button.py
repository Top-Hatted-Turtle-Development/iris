import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the bot token from the .env file
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents are required for the bot to function properly
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def button(ctx):
    # Create a button
    button = Button(label="Click Me!", style=discord.ButtonStyle.primary)

    # Define what happens when the button is clicked
    async def button_callback(interaction):
        await interaction.response.send_message("Button clicked!")

    button.callback = button_callback

    # Create a view and add the button to it
    view = View()
    view.add_item(button)

    # Send a message with the button
    await ctx.send("Here is a button for you!", view=view)

# Run the bot using the token from the .env file
bot.run(TOKEN)