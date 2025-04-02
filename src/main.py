# Iris 1.1.0-alpha
# developed by turtledevv

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import asyncio
import requests
import re
import urllib.parse
import json
import logging
from openai import OpenAI
from setup import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)

client = OpenAI(
    api_key="your-api-key",
    base_url=API_URL
)



def load_models() -> list:
    logging.info("Loading models")
    models = client.models.list()
    return models

def get_gif_link(query: str) -> str:
    logging.info(f"Searching Giphy for: {query}")
    api_key = GIPHY_KEY
    endpoint = "https://api.giphy.com/v1/gifs/search"
    params = {"api_key": api_key,"q": query,"limit": 1,"offset": 0,"lang": "en"}   
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            gif_url = data['data'][0]['images']['original']['url']
            return gif_url
        else:
            return "No results found."
    else:
        return f"Error: {response.status_code}"
    
def has_admin_permissions(interaction):
    return interaction.user.guild_permissions.administrator or (interaction.user.name == "turtledevv" and DEV_MODE)

def replace_gif_tags(input_string: str) -> str:
    def replace_function(match):
        keyword = match.group(1)
        gif_link = asyncio.run(get_gif_link(keyword))
        return gif_link
    return GIF_TAG_PATTERN.sub(replace_function, input_string)

def save_info():
    logging.info("Saving info data")
    for guild_id, channels in default_channels.items():
        info_file = f'server/info/{guild_id}.json'
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                info = json.load(f)
            info['default_channels'] = channels
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=4)
        else:
            info = {
                'server_id': guild_id,
                'default_channels': channels,
                'default_prompt': START_MSG
            }
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=4)

def extract_and_remove_think_tags(model_response):
    if "<think>" in model_response and "</think>" in model_response:
        start_idx = model_response.find("<think>") + len("<think>")
        end_idx = model_response.find("</think>")
        think_content = model_response[start_idx:end_idx].strip()
        cleaned_response = model_response[:start_idx - len("<think>")] + model_response[end_idx + len("</think>"):]
        cleaned_response = cleaned_response.strip()
        return think_content, cleaned_response
    return None, model_response

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

async def get_user_presence(username, guild_id):
    guild = bot.get_guild(guild_id)
    logging.info(f"Grabbing presence for {username} in guild {guild.name}")
    if guild:
        member = guild.get_member_named(username)
        if member:
            status = str(member.status)
            activities = str(member.activities)
            return f"Presence for {member.name}\n: STATUS: {status}\n ACTIVITIES: {activities}"
    return None

async def google_search(query):
    logging.info(f"Searching Google for: {query}")
    search_url = f"https://www.googleapis.com/customsearch/v1?q={urllib.parse.quote(query)}&key={GOOGLE_KEY}&cx={CX_ID}"
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            search_results = await response.json()
            return search_results

async def chat_with_model(query, guild_id):
    if guild_id == "all":
        for guild in bot.guilds:
            await chat_with_model(query, guild.id)
        return
    url = 'https://chat.teatree.chat/api/chat/completions'
    headers = {
        'Authorization': f'Bearer {TEATREE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    if guild_id not in conversation_histories:
        conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
    conversation_histories[guild_id].append({'role': 'user', 'content': query})
    try:
        think_link = ""
        response = client.chat.completions.create(
            model=the_model,
            messages=conversation_histories[guild_id],
            max_tokens=1200,
            temperature=0.7
        )
        model_response = response.choices[0].message.content
        model_response = replace_gif_tags(model_response)
        guild_thing = bot.get_guild(guild_id)
        print(f'\033[90m({guild_thing}) \033[35mIris:\033[0m {model_response}')
        model_response = model_response.replace("@everyone", "*@*everyone").replace("@here", "*@*here")
        
        if "~search[" in model_response:
            start_idx = model_response.find("~search[") + len("~search[")
            end_idx = model_response.find("]", start_idx)
            search_query = model_response[start_idx:end_idx].strip()
            model_response = model_response[:start_idx - len("~search[")] + model_response[end_idx + 1:]
            model_response = model_response.strip()
            
            search_results = await google_search(search_query)
            if 'items' in search_results:
                search_response = "\n".join([f"{item['title']}: {item['link']}" for item in search_results['items'][:3]])
            else:
                search_response = "No results found."
            
            conversation_histories[guild_id].append({'role': 'system', 'content': f"Search Results:\n{search_response}"})
            response = client.chat.completions.create(
                model=the_model,
                messages=conversation_histories[guild_id],
                max_tokens=1200,
                temperature=0.7
            )
            model_response = response.choices[0].message.content
            model_response = model_response.replace("@everyone", "*@*everyone").replace("@here", "*@*here")
            think_content, model_response = extract_and_remove_think_tags(model_response)
            if think_content:
                encoded_text = urllib.parse.quote(think_content)
                think_link = f"https://web-iris.vercel.app/v.html?text={encoded_text}"
            
        think_content, model_response = extract_and_remove_think_tags(model_response)
        if think_content:
            encoded_text = urllib.parse.quote(think_content)
            think_link = f"https://web-iris.vercel.app/v.html?text={encoded_text}"
        
        conversation_histories[guild_id].append({'role': 'assistant', 'content': model_response})
        return model_response, think_link
    except Exception as e:
        logging.error(f"Error: {str(e)} (Using model: {the_model})")
        return None
    
async def update_presence():
    while True:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='with AI'))
        await asyncio.sleep(15)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='your requests'))
        await asyncio.sleep(15)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='your conversations'))
        await asyncio.sleep(15)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logging.error(f"Error syncing commands: {e}")

    bot.loop.create_task(update_presence())

@bot.event
async def on_message(message):
    if not message.author.bot:
        guild_id = str(message.guild.id)
        
        if guild_id not in conversation_histories:
            conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
            save_conversation_histories()
        
        if (guild_id in default_channels and message.channel.id in default_channels[guild_id]) or f"<@{bot.user.id}>" in message.content:
            if not message.content.startswith("//"):
                themessage = message.content.replace(f"<@{bot.user.id}>", f"@{bot.user.name}")
                user_id = message.author.id
                username = message.author.name
                if user_id in anonymous_users and anonymous_users[user_id]:
                    username = "Anonymous"
                print(f'\033[90m({message.guild.name}) \033[92m{username}:\033[0m {themessage}')
                async with message.channel.typing():
                    response, think_link = await chat_with_model(f"({message.guild.name}) {username}: {themessage}", guild_id)
                view = discord.ui.View()
                if think_link != "":
                    button = discord.ui.Button(
                        style = discord.ButtonStyle.link,
                        url = think_link,
                        label = "View Thinking",
                        emoji = "🧠"
                    )
                    view.add_item(button)
                    
                if not DEV_MODE:
                    if response:
                        if response == "None":
                            response = "***An error occurred. Please try again, or contact turtledevv.***"
                        else:
                            if think_link != "":
                                await message.reply(view=view)
                            await send_message_in_chunks(message.channel, response)
                    else:
                        await message.reply("***An error occurred. Please try again, or contact turtledevv.***")
                else:
                    if think_link != "":
                        await message.reply(view=view)

                    await send_message_in_chunks(message.channel, response) # type: ignore
        else:
            await bot.process_commands(message)

async def send_message_in_chunks(channel, text):
    chunk_size = 2000
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    for chunk in chunks:
        await channel.send(chunk)

models = load_models()
MODEL_CHOICES = []
model_data = []
for model in models.data:
    MODEL_CHOICES.append(discord.app_commands.Choice(name=f"{model.id} - {model.owned_by.capitalize()}", value=model.id))

@bot.tree.command(name="model", description="Change the model to use.")
@app_commands.describe(model = "The model to use.")
@app_commands.choices(model=MODEL_CHOICES)
async def change_model(interaction: discord.Interaction, model: str):
    logging.debug(f"/change_model invoked by {interaction.user.name}")
    global the_model
    
    the_model = model
        
    guild_id = interaction.guild.id
    if guild_id not in conversation_histories:
        conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
    conversation_histories[guild_id].append({'role': 'system', 'content': f"({interaction.user.name} changed the model to {model})"})
    model_img = ""
    if the_model == "gpt-4o" or the_model == "gpt-4o-mini" or the_model == "o3-mini":
        model_img = "https://img.logo.dev/chatgpt.com"
        model_color = discord.Color.from_rgb(152, 255, 152)
    if the_model == "deepseek-r1":
        model_img = "https://img.logo.dev/deepseek.com"
        model_color = discord.Color.blue()
    if the_model == "grok-2":
        model_img = "https://www.google.com/s2/favicons?sz=256&domain_url=https%3A%2F%2Fgrok.com%2F"
        model_color = discord.Color.from_rgb(0,0,0)
    embed = discord.Embed(title=the_model)
    embed.set_author(name="Model changed")
    embed.set_thumbnail(url=model_img)
    embed.set_footer(text=interaction.user.name, icon_url=interaction.user.avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="hideusername", description="Be an anonymous user.")
async def hide_username(interaction: discord.Interaction):
    logging.debug(f"/hideusername invoked by {interaction.user.name}")
    user_id = interaction.user.id
    anonymous_users[user_id] = not anonymous_users.get(user_id, False)
    status = "anonymous" if anonymous_users[user_id] else "visible"
    await interaction.response.send_message(f"Your status is now {status}.")

@bot.tree.command(name="clear_memory", description="Clear the bot's conversation history.")
async def clear_memory(interaction: discord.Interaction):
    logging.debug(f"/clear_memory invoked by {interaction.user.name}")
    if has_admin_permissions(interaction):
        guild_id = interaction.guild.id
        conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
        await interaction.response.send_message("Conversation history has been cleared.")
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="bot_invite", description="Get the invite link for the bot.")
async def bot_invite(interaction: discord.Interaction):
    logging.debug(f"/bot_invite invoked by {interaction.user.name}")
    await interaction.response.send_message("https://discord.com/oauth2/authorize?client_id=1340580911892271185&scope=bot&permissions=8")

@bot.tree.command(name="change_prompt", description="Change the initial prompt for the current server.")
@app_commands.describe(prompt="The new initial prompt.")
async def change_prompt(interaction: discord.Interaction, prompt: str):
    logging.debug(f"/change_prompt invoked by {interaction.user.name}")
    global START_MSG
    if has_admin_permissions(interaction):
        guild_id = str(interaction.guild.id)
        info_file = f'server/info/{guild_id}.json'
        
        if prompt.lower() == "default":
            new_prompt = START_MSG
        else:
            new_prompt = f"{START_MSG} {prompt}"
        
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                info = json.load(f)
            info['default_prompt'] = new_prompt
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=4)
        else:
            info = {
                'server_name': interaction.guild.name,
                'server_id': guild_id,
                'default_channels': default_channels.get(guild_id, []),
                'default_prompt': new_prompt
            }
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=4)
        
        START_MSG = new_prompt
        if guild_id in conversation_histories:
            conversation_histories[guild_id][0]['content'] = START_MSG
        else:
            conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
        save_conversation_histories()
        
        await interaction.response.send_message("Initial prompt has been changed. It works best with /clear_memory.")
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="add_default_channel", description="Add a default channel for the bot to respond in.")
async def add_default_channel(interaction: discord.Interaction):
    logging.debug(f"/add_default_channel invoked by {interaction.user.name}")
    if has_admin_permissions(interaction):
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        if guild_id not in default_channels:
            default_channels[guild_id] = []
        if isinstance(default_channels[guild_id], list) and channel_id not in default_channels[guild_id]:
            default_channels[guild_id].append(channel_id)
            save_default_channels()
            await interaction.response.send_message(f"Added {interaction.channel.name} as a default channel.")
        else:
            await interaction.response.send_message(f"{interaction.channel.name} is already a default channel.")
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="remove_default_channel", description="Remove a default channel for the bot to respond in.")
async def remove_default_channel(interaction: discord.Interaction):
    logging.debug(f"/remove_default_channel invoked by {interaction.user.name}")
    if has_admin_permissions(interaction):
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        if guild_id in default_channels and isinstance(default_channels[guild_id], list) and channel_id in default_channels[guild_id]:
            default_channels[guild_id].remove(channel_id)
            save_default_channels()
            await interaction.response.send_message(f"Removed {interaction.channel.name} from default channels.")
        else:
            await interaction.response.send_message(f"{interaction.channel.name} is not a default channel.")
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

def bye():
    logging.info("Shutting down bot...")
    save_conversation_histories()
    save_default_channels()
    save_info()
    logging.info("Goodbye!")

import atexit
atexit.register(bye)

bot.run(DISCORD_TOKEN)