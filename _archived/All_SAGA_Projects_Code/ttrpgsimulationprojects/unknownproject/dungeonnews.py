import hashlib
import random
from PIL import Image, ImageDraw, ImageOps

# --- 1. SETTINGS & MOCK DATA ---
# In your real app, these would come from NewsAPI, NASA, etc.
headlines = [
    "NASA: Massive Solar Flare Spotted",
    "Robots: AI Model Learns to Paint",
    "Cats: Rare Forest Cat Discovered",
    "Dogs: Hero Lab Saves Family",
    "News: Global Trade Agreement Signed",
    "History: Lost City Found in Jungle",
    "Science: Liquid Water on Mars"
]

def get_seed(text):
    """Turns headline text into a reproducible number."""
    return int(hashlib.md5(text.encode()).hexdigest(), 16)

# --- 2. THE GENERATOR ---
slice_w, slice_h = 400, 600
canvas = Image.new('RGB', (slice_w * 7, slice_h), (0, 0, 0))
draw = ImageDraw.Draw(canvas)

print("--- GENERATING DUNGEON DATA ---")
path_points = []

for i, headline in enumerate(headlines):
    seed = get_seed(headline)
    random.seed(seed) # Use the headline as the random seed
    
    # Create a "Biometric Slice" with random noise (Simulating an API image)
    # We use random colors based on the headline's 'vibe'
    r, g, b = random.randint(20, 100), random.randint(20, 100), random.randint(20, 100)
    slice_img = Image.new('RGB', (slice_w, slice_h), (r, g, b))
    
    # Add some "dungeon noise" (White blobs where rooms might be)
    slice_draw = ImageDraw.Draw(slice_img)
    for _ in range(3):
        x, y = random.randint(50, 300), random.randint(50, 500)
        rad = random.randint(40, 80)
        slice_draw.ellipse([x-rad, y-rad, x+rad, y+rad], fill=(200, 200, 200))
    
    # Paste slice into master canvas
    canvas.paste(slice_img, (i * slice_w, 0))
    
    # Calculate hallway anchor point (X is center of slice, Y is based on seed)
    y_pos = (seed % (slice_h - 200)) + 100
    path_points.append((i * slice_w + (slice_w // 2), y_pos))
    
    print(f"Room {i+1} Seed: {seed % 20 + 1} | Keyword: {headline.split()[-1]}")

# --- 3. DRAW THE CONNECTING HALLWAY ---
# We draw a thick, slightly "shaky" hallway to connect the seeds
draw.line(path_points, fill=(255, 255, 255), width=30, joint="curve")

# --- 4. APPLY THE "D&D TEMPLATE" FILTERS ---
# 1. Grayscale
final = canvas.convert("L")
# 2. High Contrast (Thresholding) to make it look like a map
final = final.point(lambda x: 255 if x > 140 else 0)
# 3. Invert so it looks like black ink on white paper
final = ImageOps.invert(final)

# --- 5. SAVE & FINISH ---
final.save("dungeon_template.png")
print("\nSuccess! 'dungeon_template.png' has been created in your folder.")