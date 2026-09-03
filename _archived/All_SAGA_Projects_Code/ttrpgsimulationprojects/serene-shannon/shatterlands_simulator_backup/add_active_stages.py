import os

file_path = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\db_setup.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '    conn.commit()'
replacement = '''
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            settlement_id INTEGER NOT NULL,
            global_hex_id INTEGER NOT NULL,
            npcs_json TEXT NOT NULL,
            conflict_signal TEXT,
            last_updated_tick INTEGER NOT NULL
        )
    """)
    conn.commit()'''

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("db_setup.py successfully modified.")
else:
    print("Could not find conn.commit() in db_setup.py.")
