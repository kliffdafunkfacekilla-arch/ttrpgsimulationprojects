import requests

url = "http://localhost:8060/api/campaign/start"
payload = {
    "player_id": "test_player",
    "starting_hex_id": 200500,
    "world_id": "W_001",
    "party_size": "SOLO",
    "difficulty": "STANDARD",
    "style": "GRITTY_SURVIVAL",
    "length": "SAGA",
    "no_fly_list": []
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Failed to connect: {e}")
