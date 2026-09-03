import os

start_dir = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator'
best_db = None
best_size = 0

for root, dirs, files in os.walk(start_dir):
    for f in files:
        if f == 'world_state.db':
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            if size > best_size:
                best_size = size
                best_db = path

print(f"Largest DB: {best_db} ({best_size} bytes)")
