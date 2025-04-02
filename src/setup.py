import configparser
from dotenv import load_dotenv
import os
import logging
import json

the_model = "gpt-4o"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)

CONFIG_FILE = 'config.ini'
API_URL = 'https://api.teatree.chat/v1'
START_MSG = "You are Iris. You are an AI discord bot. You can chat with all members. You are made by Top Hatted Turtle Development, and you use Tea Tree (website: https://teatree.chat, discord: https://discord.gg/2N2HFMeVup)'s API to function. TEA TREE IS NOT OWNED BY TOP HATTED TURTLE DEVELOPMENT. TEA TREE HAS SPONSERED THIS PROJECT. You are in multiple servers, however your memory does not transfer between them. User's messages will be in a format of (server name) username: message. Do not send messages this way. You only recieve them that way. If you want to search something on google, type ~search[query] AND NOTHING ELSE. The system will reply and you can respond to the original message with the information you found. You can also use ~gif[query] to use gifs. That will be automatically replaced by the image. You can use other text with it, like this: 'Hi, here's a funny gif ~gif[funny dog]'"
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TEATREE_API_TOKEN = os.getenv('TEATREE_API_TOKEN')
GOOGLE_KEY = os.getenv('GOOGLE_KEY')
CX_ID = os.getenv('CX_ID')
GIPHY_KEY = os.getenv('GIPHY_KEY')
DEV_MODE = config.getboolean('SETTINGS', 'developer_mode')


if not os.path.exists('server'):
    os.makedirs('server')
if not os.path.exists('server/convo'):
    os.makedirs('server/convo')
if not os.path.exists('server/info'):
    os.makedirs('server/info')


def load_conversation_histories():
    logging.info("Loading conversation histories")
    conversation_histories = {}
    for filename in os.listdir('server/convo'):
        if filename.endswith('.json'):
            guild_id = filename[:-5]
            try:
                with open(f'server/convo/{filename}', 'r') as f:
                    content = f.read()
                    if not content.strip():
                        logging.warning(f"Conversation history file for guild {guild_id} is empty")
                        conversation_histories[guild_id] = []
                    else:
                        conversation_histories[guild_id] = json.loads(content)
            except (FileNotFoundError, json.JSONDecodeError):
                logging.error(f"Error loading conversation history for guild {guild_id}")
                conversation_histories[guild_id] = []
    return conversation_histories

def save_conversation_histories():
    logging.info("Saving conversation histories")
    for guild_id, history in conversation_histories.items():
        with open(f'server/convo/{guild_id}.json', 'w') as f:
            json.dump(history, f, indent=4)

def load_default_channels():
    logging.info("Loading default channels")
    default_channels = {}
    for filename in os.listdir('server/info'):
        if filename.endswith('.json'):
            try:
                with open(f'server/info/{filename}', 'r') as f:
                    info = json.load(f)
                    default_channels[info['server_id']] = info['default_channels']
            except (FileNotFoundError, json.JSONDecodeError):
                logging.error(f"Error loading default channels for {filename}")
    return default_channels

def save_models(models):
    logging.info("Saving models")
    models_file = 'server/models.json'
    with open(models_file, 'w') as f:
        json.dump(models, f, indent=4)

def save_default_channels():
    logging.info("Saving default channels")
    for guild_id, channels in default_channels.items():
        info_file = f'server/info/{guild_id}.json'
        if os.path.exists(info_file):
            with open(info_file, 'r') as f:
                info = json.load(f)
            info['default_channels'] = channels
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=4)
        else:
            logging.warning(f"Info file for guild {guild_id} does not exist")

