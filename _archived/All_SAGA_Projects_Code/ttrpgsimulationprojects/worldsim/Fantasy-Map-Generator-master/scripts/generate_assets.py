import os
import sys
import json
import base64
import requests
from io import BytesIO
from PIL import Image

# Try to import rembg, gracefully fail if not installed
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("Warning: 'rembg' library not found. Backgrounds will not be transparent.")
    print("Run 'pip install rembg' to enable automatic transparency.")

SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
SD_OPTIONS_URL = "http://127.0.0.1:7860/sdapi/v1/options"

# Base prompt elements for all sprites
# Using trigger words for PixNite 1.5: "pixel art"
BASE_PROMPT = "pixel art, 16-bit, video game sprite, clean flat colors, isolated on solid white background, white background"
NEGATIVE_PROMPT = "(worst quality, lowres, realistic, 3d, gradient, blurry, shadows, detailed background)"

# Define the assets we need for the simulation
ASSETS_TO_GENERATE = {
    # Biomes (Terrain)
    "biome_plains": "grassy plains terrain tile",
    "biome_forest": "dense pine forest terrain tile",
    "biome_mountain": "snowy mountain peak terrain tile",
    "biome_desert": "sandy dune desert terrain tile",
    "biome_ocean": "deep blue ocean water terrain tile",
    "biome_coastal": "sandy beach coastal water terrain tile",
    "biome_reef": "colorful underwater coral reef terrain tile",
    
    # Structures
    "struct_farm": "medieval wheat farm plot",
    "struct_watchtower": "stone medieval watchtower",
    "struct_barracks": "military barracks tent and training yard",
    "struct_trade_hub": "bustling merchant trade hub bazaar with gold coins",
    "struct_ruins": "destroyed stone ruins, abandoned",
    "struct_docks": "wooden fishing docks",
    
    # Units
    "unit_patrol": "medieval city guard with spear walking",
    "unit_trade_caravan": "merchant horse drawn wooden cart caravan",
    "unit_cultist": "mysterious hooded cultist walking",
    
    # Logistics / Transports
    "tech_draft_horses": "draft horse animal",
    "tech_naval_travel": "wooden sailing galleon ship",
    "tech_airships": "steampunk hot air balloon airship flying"
}

def generate_image(prompt, output_path):
    print(f"Generating: {prompt}")
    
    payload = {
        "prompt": f"{BASE_PROMPT}, {prompt}",
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 7.0,
        "sampler_name": "Euler a"
    }

    try:
        response = requests.post(SD_API_URL, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"Failed to reach SD API: {response.status_code}")
            return False
            
        r = response.json()
        
        # Grab the first image from the response
        image_data = r['images'][0]
        image_bytes = base64.b64decode(image_data.split(",", 1)[0])
        
        img = Image.open(BytesIO(image_bytes))
        
        # Apply Background Removal if available
        if REMBG_AVAILABLE:
            print("  -> Removing white background...")
            img = remove(img)
            
        img.save(output_path)
        print(f"  -> Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error during generation: {e}")
        return False

def set_model_checkpoint():
    """Tells the SD Web UI to switch to the PixNite 1.5 checkpoint."""
    print("Switching SD Model to PixNite 1.5 - Pure Pixel Art...")
    payload = {
        "sd_model_checkpoint": "pixnite15PurePixel_v10"
    }
    try:
        response = requests.post(SD_OPTIONS_URL, json=payload, timeout=60)
        if response.status_code == 200:
            print("Successfully switched model!")
        else:
            print(f"Failed to switch model: {response.status_code}")
    except Exception as e:
        print(f"Error switching model: {e}")

def main():
    # Target the React frontend's public/assets directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dashboard-ui', 'public', 'assets'))
    os.makedirs(base_dir, exist_ok=True)
    
    print("=== Stable Diffusion Pixel Art Generator ===")
    print(f"Target Directory: {base_dir}")
    print(f"SD Web UI API: {SD_API_URL}")
    print("--------------------------------------------")
    
    # Set the model before generating
    set_model_checkpoint()
    
    success_count = 0
    for filename, specific_prompt in ASSETS_TO_GENERATE.items():
        output_path = os.path.join(base_dir, f"{filename}.png")
        if os.path.exists(output_path):
            print(f"Skipping {filename}.png (Already exists)")
            continue
            
        if generate_image(specific_prompt, output_path):
            success_count += 1
            
    print("--------------------------------------------")
    print(f"Generation Complete! Successfully created {success_count} assets.")

if __name__ == "__main__":
    main()
