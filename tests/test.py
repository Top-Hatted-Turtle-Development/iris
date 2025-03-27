import requests

def chat_with_model(token, model, query):
    url = 'https://teatree.chat/api/chat/completions'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': query}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # Replace these with your actual values
    API_TOKEN = "sk-e41fb7050b284180afc4bc3fbf5a4c1d"
    MODEL_NAME = "gpt-4o-mini"  # or your preferred model

    print("Welcome to the Chat Interface! (Type 'quit' to exit)")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break

        if user_input.strip() == "":
            continue

        try:
            response = chat_with_model(API_TOKEN, MODEL_NAME, user_input)
            if isinstance(response, dict) and 'choices' in response:
                assistant_message = response['choices'][0]['message']['content']
                print("\nAI:", assistant_message)
            else:
                print("\nAI: Sorry, I couldn't process that request.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()