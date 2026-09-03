import os

file_path = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\core_engine\engine.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''            sec = max(0.0, min(100.0, sec))
            s_updates.append((s_level, pop, spark_pop, wealth, sec, json.dumps(inventory), hidden, s_id))'''

replacement = '''            sec = max(0.0, min(100.0, sec))
            
            conflict_signal = None
            if sec < 20:
                conflict_signal = 'Anarchy'
            elif wealth < 10 and pop > 100:
                conflict_signal = 'Starvation'
                
            if conflict_signal:
                cursor.execute("UPDATE active_stages SET conflict_signal=?, last_updated_tick=? WHERE settlement_id=?", (conflict_signal, self.tick, s_id))

            s_updates.append((s_level, pop, spark_pop, wealth, sec, json.dumps(inventory), hidden, s_id))'''

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("engine.py successfully modified.")
else:
    print("Could not find target in engine.py.")
