import requests
import configparser

CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

GIPHY_KEY = config.get('SECRETS', 'giphy_api_key')

def get_gif_link(query):
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

# Example usage
query = input("Enter a search query: ")
gif_link = get_gif_link(query)
print(gif_link)