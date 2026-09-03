import os

file_path = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\story_generator\generate_narrative.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shatterlands_simulator", "world_state.db")'
replacement = 'DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core_engine", "world_state.db")'

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("generate_narrative.py successfully modified.")
else:
    print("Could not find target in generate_narrative.py.")
