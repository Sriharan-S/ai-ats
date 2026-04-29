import requests

API_KEY = "e3244ff8d3b5b0f2b3449367f53de72ca407c29296bc69f9c1a7679d5ba6a6b5"  # Replace with your valid API key

url = "https://api.together.xyz/v1/chat/completions"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Use a supported free model
data = {
    "model": "mistralai/Mistral-7B-Instruct-v0.1",  # ✅ This model is free
    "messages": [{"role": "user", "content": "what is your name !"}]
}

response = requests.post(url, json=data, headers=headers)

print("Status Code:", response.status_code)
print("Response:", response.text)
