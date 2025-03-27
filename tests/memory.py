import requests

api_key = "sk-e41fb7050b284180afc4bc3fbf5a4c1d"
model = 'gpt-4o'
convo_history = []

def doStuff():
    url = "https://teatree.chat/api/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {'model': model, 'messages': convo_history}
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    model_response = response_data['choices'][0]['message']['content']
    print(f"AI: {model_response}")
    convo_history.append({'role': 'assistant', 'content': model_response})
    
while True:
    prompt = input("You: ")
    convo_history.append({'role': 'user', 'content': prompt})
    doStuff()

