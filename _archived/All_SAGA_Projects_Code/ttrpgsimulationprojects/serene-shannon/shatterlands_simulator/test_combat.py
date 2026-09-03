import requests
import json

url = "http://localhost:8000/action"
payload = {
    "action": "I aggressively attack the royal guards standing by the gate with my broadsword!",
    "model": "qwen2.5:latest"
}

print("Sending attack action to AI Director...")
try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print("\n--- NARRATIVE ---")
        print(data.get("narrative", "No narrative returned."))
        print("\n--- COMBAT ENCOUNTER ---")
        if "combat_encounter" in data:
            print(json.dumps(data["combat_encounter"], indent=2))
        else:
            print("No combat encounter triggered.")
    else:
        print(f"Failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error: {e}")
