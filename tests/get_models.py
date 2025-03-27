import requests

def get_model_ids(obj):
    if isinstance(obj, dict) and 'data' in obj:
        return {'data': [{'id': item['id']} for item in obj['data']]}
    return obj

# Your API key
api_key = "1340580911892271185"

# Headers
headers = {
    "Authorization": f"Bearer {api_key}"
}

try:
    response = requests.get("https://teatree.chat/api/models", headers=headers)
    
    # Check if request was successful
    if response.status_code == 200:
        try:
            # Attempt to parse the response as JSON
            data = response.json()
            # Get just the model IDs
            ids_only = get_model_ids(data)
            print(ids_only)
        except ValueError:
            print("Response is not in JSON format.")
            print("Response text:", response.text)
    else:
        print(f"Request failed with status code: {response.status_code}")
        print("Response text:", response.text)

except requests.exceptions.RequestException as e:
    print(f"An error occurred during the request: {e}")
