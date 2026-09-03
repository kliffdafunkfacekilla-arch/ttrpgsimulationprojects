import subprocess
import time
import requests
import sys

def main():
    # Start uvicorn
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8056"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for startup
    time.sleep(5)
    
    url = "http://localhost:8056/api/campaign/start"
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
        
    proc.terminate()
    stdout, stderr = proc.communicate()
    print("STDOUT:")
    print(stdout)
    print("STDERR:")
    print(stderr)

if __name__ == "__main__":
    main()
