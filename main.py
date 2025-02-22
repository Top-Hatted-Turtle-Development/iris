import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import configparser
import os
import asyncio
import requests
import re
import urllib.parse
import json

# wow, look! it's logging.
def log_info(message):
    print(f"\033[90m[INFO] \033[37m{message}\033[0m")

def log_warning(message):
    print(f"\033[33m[WARN] \033[37m{message}\033[0m")

def log_error(message):
    print(f"\033[91m[ERROR] \033[37m{message}\033[0m")

the_model = "gpt-4o"

CONFIG_FILE = 'config.ini'
CHANNEL_ID = 1340580647483346975
API_URL = 'https://teatree.chat/api/chat/completions'
START_MSG = "You are Iris. You are an AI discord bot. You can chat with all members. You are made by Top Hatted Turtle Development, and you use Tea Tree (website: https://teatree.chat, discord: https://discord.gg/2N2HFMeVup)'s API to function. You are in multiple servers, however your memory does not transfer between them. User's messages will be in a format of (server name) username: message. Do not send messages this way. You only recieve them that way. If you want to search something on google, type ~search[query] AND NOTHING ELSE. The system will reply and you can respond to the original message with the information you found."

# config shit
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', config.get('SECRETS', 'discord_token'))
TEATREE_API_TOKEN = os.getenv('TEATREE_API_TOKEN', config.get('SECRETS', 'teatree_api_token'))
BOT_ACTIVITY = config.get('SETTINGS', 'activity')
DEV_MODE = config.getboolean('SETTINGS', 'developer_mode')
GOOGLE_KEY = config.get('SECRETS', 'google_key')
CX_ID = config.get('SECRETS','cx_id')

# Ensure the server directory and its subdirectories exist
if not os.path.exists('server'):
    os.makedirs('server')
if not os.path.exists('server/convo'):
    os.makedirs('server/convo')
if not os.path.exists('server/info'):
    os.makedirs('server/info')

def load_conversation_histories():
    log_info("Loading conversation histories")
    conversation_histories = {}
    for filename in os.listdir('server/convo'):
        if filename.endswith('.json'):
            guild_id = filename[:-5]
            try:
                with open(f'server/convo/{filename}', 'r') as f:
                    content = f.read()
                    if not content.strip():
                        log_warning(f"Conversation history file for guild {guild_id} is empty")
                        conversation_histories[guild_id] = []
                    else:
                        conversation_histories[guild_id] = json.loads(content)
            except (FileNotFoundError, json.JSONDecodeError):
                log_error(f"Error loading conversation history for guild {guild_id}")
                conversation_histories[guild_id] = []
    return conversation_histories

def save_conversation_histories():
    log_info("Saving conversation histories")
    for guild_id, history in conversation_histories.items():
        with open(f'server/convo/{guild_id}.json', 'w') as f:
            json.dump(history, f, indent=4)

def load_default_channels():
    log_info("Loading default channels")
    default_channels = {}
    for filename in os.listdir('server/info'):
        if filename.endswith('.json'):
            try:
                with open(f'server/info/{filename}', 'r') as f:
                    info = json.load(f)
                    default_channels[info['server_id']] = info['default_channels']
            except (FileNotFoundError, json.JSONDecodeError):
                log_error(f"Error loading default channels for {filename}")
    return default_channels

def load_models():
    log_info("Loading models")
    models_file = 'server/models.json'
    if os.path.exists(models_file):
        with open(models_file, 'r') as f:
            return json.load(f)
    return None

def save_models(models):
    log_info("Saving models")
    models_file = 'server/models.json'
    with open(models_file, 'w') as f:
        json.dump(models, f, indent=4)

def has_admin_permissions(interaction):
    return interaction.user.guild_permissions.administrator or (interaction.user.name == "turtledevv" and DEV_MODE)

def save_default_channels():
    log_info("Saving default channels")
    for guild_id, channels in default_channels.items():
        info_file = f'server/info/{guild_id}.json'
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                info = json.load(f)
            info['default_channels'] = channels
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=4)
        else:
            log_warning(f"Info file for guild {guild_id} does not exist")

def save_info():
    log_info("Saving info data")
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

# Load conversation histories and default channels before starting the bot
conversation_histories = load_conversation_histories()
print(conversation_histories)
default_channels = load_default_channels()
print(default_channels)

anonymous_users = {}

# set up the bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

async def get_user_presence(username, guild_id):
    # Get guild from guild ID
    guild = bot.get_guild(guild_id)
    log_info(f"Grabbing presence for {username} in guild {guild.name}")
    if guild:
        member = guild.get_member_named(username)
        if member:
            status = str(member.status)
            activities = str(member.activities)
            return f"Presence for {member.name}\n: STATUS: {status}\n ACTIVITIES: {activities}"
    return None

async def google_search(query):
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
    url = 'https://teatree.chat/api/chat/completions'
    headers = {
        'Authorization': f'Bearer {TEATREE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    if guild_id not in conversation_histories:
        conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
    conversation_histories[guild_id].append({'role': 'user', 'content': query})
    payload = {
        'model': the_model,
        'messages': conversation_histories[guild_id]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response_data = await response.json()
                model_response = response_data['choices'][0]['message']['content']
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
                    
                    # Send the search results back to the AI model for further processing
                    conversation_histories[guild_id].append({'role': 'system', 'content': f"Search Results:\n{search_response}"})
                    payload = {
                        'model': the_model,
                        'messages': conversation_histories[guild_id]
                    }
                    async with session.post(url, headers=headers, json=payload) as response:
                        response_data = await response.json()
                        model_response = response_data['choices'][0]['message']['content']
                        model_response = model_response.replace("@everyone", "*@*everyone").replace("@here", "*@*here")
                        # This is fucking terrible coding practice. PLEASE, PLEASE, for the love of god and anything that is holy, replace this in a future update.
                        if "<think>" in model_response and "</think>" in model_response:
                            start_idx = model_response.find("<think>") + len("<think>")
                            end_idx = model_response.find("</think>")
                            think_content = model_response[start_idx:end_idx].strip()
                            
                            encoded_text = urllib.parse.quote(think_content)
                            think_link = f"https://web-iris.vercel.app/view_thinking.html?text={encoded_text}"
                            
                            # Remove <think>...</think> from the message
                            model_response = model_response[:start_idx - len("<think>")] + model_response[end_idx + len("</think>"):]
                            model_response = model_response.strip()
                            
                            # Append the View Thinking link at the top
                            model_response = f"-# *[View Thinking]({think_link})*\n{model_response}"
                    
                if "<think>" in model_response and "</think>" in model_response:
                    start_idx = model_response.find("<think>") + len("<think>")
                    end_idx = model_response.find("</think>")
                    think_content = model_response[start_idx:end_idx].strip()
                    
                    encoded_text = urllib.parse.quote(think_content)
                    think_link = f"https://web-iris.vercel.app/view_thinking.html?text={encoded_text}"
                    
                    # Remove <think>...</think> from the message
                    model_response = model_response[:start_idx - len("<think>")] + model_response[end_idx + len("</think>"):]
                    model_response = model_response.strip()
                    
                    # Append the View Thinking link at the top
                    model_response = f"-# *[View Thinking]({think_link})*\n{model_response}"
                
                conversation_histories[guild_id].append({'role': 'assistant', 'content': model_response})
                return model_response
    except Exception as e:
        log_error(f"Error: {str(e)} (Using model: {the_model})")
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
    log_info(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        log_info(f"Synced {len(synced)} commands")
    except Exception as e:
        log_error(f"Error syncing commands: {e}")

    bot.loop.create_task(update_presence())

@bot.event
async def on_message(message):
    if not message.author.bot:
        guild_id = str(message.guild.id)  # Convert guild_id to string
        log_info(f"Received message from guild {guild_id}")
        
        # Reload conversation histories if guild_id is not found
        if guild_id not in conversation_histories:
            conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
            save_conversation_histories()
        else:
            log_info(f"Guild {guild_id} found in conversation_histories")
        
        if (guild_id in default_channels and message.channel.id in default_channels[guild_id]) or f"<@{bot.user.id}>" in message.content:
            if not message.content.startswith("//"):
                themessage = message.content.replace(f"<@{bot.user.id}>", f"@{bot.user.name}")
                user_id = message.author.id
                username = message.author.name
                if user_id in anonymous_users and anonymous_users[user_id]:
                    username = "Anonymous"
                print(f'\033[90m({message.guild.name}) \033[92m{username}:\033[0m {themessage}')
                async with message.channel.typing():
                    response = await chat_with_model(f"({message.guild.name}) {username}: {themessage}", guild_id)
                if not DEV_MODE:
                    if response:
                        if response == "None":
                            response = "***An error occurred. Please try again, or contact turtledevv.***"
                        else:
                            await message.reply(response)
                    else:
                        await message.reply("***An error occurred. Please try again, or contact turtledevv.***")
                else:
                    await message.reply(response)
                print(f'\033[90m({message.guild.name}) \033[35mIris:\033[0m {response}')
        else:
            await bot.process_commands(message)

def get_model_choices(obj):
    if isinstance(obj, dict) and 'data' in obj:
        return [
            discord.app_commands.Choice(name=item['id'], value=item['id']) 
            for item in obj['data']
        ]
    return []

models = load_models()
if models is None:
    headers = {
        "Authorization": f"Bearer {TEATREE_API_TOKEN}"
    }
    response = requests.get("https://teatree.chat/api/models", headers=headers)
    models = response.json()
    save_models(models)

MODEL_CHOICES = get_model_choices(models)

@bot.tree.command(name="model", description="Change the model to use.")
@app_commands.describe(model = "The model to use.")
@app_commands.choices(model=MODEL_CHOICES)
async def change_model(interaction: discord.Interaction, model: str):
    global the_model
    guild_id = interaction.guild.id
    if guild_id not in conversation_histories:
        conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
    conversation_histories[guild_id].append({'role': 'user', 'content': f"({interaction.user.name} changed the model to {model})"})
    print(f"{interaction.user.name} changed the model to {model}")
    await interaction.response.send_message(f"## Selected model: {model}\n-# Changed by {interaction.user.name}")
    the_model = model

@bot.tree.command(name="hideusername", description="Be an anonymous user.")
async def hide_username(interaction: discord.Interaction):
    user_id = interaction.user.id
    anonymous_users[user_id] = not anonymous_users.get(user_id, False)
    status = "anonymous" if anonymous_users[user_id] else "visible"
    await interaction.response.send_message(f"Your status is now {status}.")

@bot.tree.command(name="clear_memory", description="Clear the bot's conversation history.")
async def clear_memory(interaction: discord.Interaction):
    if has_admin_permissions(interaction):
        guild_id = interaction.guild.id
        conversation_histories[guild_id] = [{'role': 'user', 'content': START_MSG}]
        await interaction.response.send_message("Conversation history has been cleared.")
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

@bot.tree.command(name="bot_invite", description="Get the invite link for the bot.")
async def bot_invite(interaction: discord.Interaction):
    await interaction.response.send_message("https://discord.com/oauth2/authorize?client_id=1340580911892271185&scope=bot&permissions=8")

@bot.tree.command(name="change_prompt", description="Change the initial prompt for the current server.")
@app_commands.describe(prompt="The new initial prompt.")
async def change_prompt(interaction: discord.Interaction, prompt: str):
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

# Save conversation histories on exit
import atexit
atexit.register(save_conversation_histories)
atexit.register(save_default_channels)
atexit.register(save_info)

bot.run(DISCORD_TOKEN)
