import os

file_path = r'c:\Users\krazy\Desktop\serene-shannon\shatterlands_simulator\ai_director\npc_behavior.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

import_statement = "from ai_director.oracle import ContextOracle\n"
if "ContextOracle" not in content:
    lines = content.split('\n')
    lines.insert(3, import_statement)
    content = '\n'.join(lines)

new_class = '''

class NarrativeStageManager:
    def __init__(self, db_path=DB_PATH, player_pos=(0, 0), radius=2):
        self.db_path = db_path
        self.player_hex = player_pos
        self.radius = radius
        self.oracle = ContextOracle(db_path=self.db_path)

    def update_stage(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Clear NPCs outside of radius
        cursor.execute("""
            SELECT a.id, g.q, g.r 
            FROM active_stages a
            JOIN global_hexes g ON a.global_hex_id = g.id
        """)
        active_coords = cursor.fetchall()
        
        pq, pr = self.player_hex
        for stage_id, gq, gr in active_coords:
            dist = (abs(pq - gq) + abs(pq + pr - gq - gr) + abs(pr - gr)) // 2
            if dist > self.radius:
                cursor.execute("DELETE FROM active_stages WHERE id=?", (stage_id,))
                
        # 2. Query settlements within radius
        cursor.execute("""
            SELECT s.id, g.id, g.q, g.r, s.name, s.wealth, s.security_points
            FROM settlements s
            JOIN global_hexes g ON s.global_hex_id = g.id
        """)
        all_settlements = cursor.fetchall()
        
        for s_id, g_id, gq, gr, s_name, wealth, security in all_settlements:
            dist = (abs(pq - gq) + abs(pq + pr - gq - gr) + abs(pr - gr)) // 2
            if dist <= self.radius:
                # 3. If NPCs don't exist for this hex, generate them
                cursor.execute("SELECT id, npcs_json, conflict_signal FROM active_stages WHERE settlement_id=?", (s_id,))
                stage = cursor.fetchone()
                
                if not stage:
                    # Get Oracle Context
                    context = self.oracle.get_hex_context(gq, gr)
                    
                    # Generate deterministic NPCs based on conditions
                    npcs = []
                    if security < 20:
                        npcs.append({"role": "Crime Leader", "status": "Active"})
                        npcs.append({"role": "Informant", "status": "Scared"})
                    elif wealth > 80:
                        npcs.append({"role": "Merchant Prince", "status": "Greedy"})
                        npcs.append({"role": "Thief", "status": "Plotting"})
                    else:
                        npcs.append({"role": "Local Guard", "status": "Bored"})
                        npcs.append({"role": "Tavern Keeper", "status": "Gossip"})
                        
                    cursor.execute("INSERT INTO active_stages (settlement_id, global_hex_id, npcs_json, last_updated_tick) VALUES (?, ?, ?, ?)", 
                                   (s_id, g_id, json.dumps(npcs), 0))
                else:
                    # 4. Process ConflictSignal if pushed by GlobalEngine
                    stage_id, npcs_json, conflict_signal = stage
                    if conflict_signal:
                        npcs = json.loads(npcs_json)
                        if conflict_signal == 'Anarchy':
                            npcs.append({"role": "Rioter", "status": "Angry"})
                        elif conflict_signal == 'Starvation':
                            npcs.append({"role": "Desperate Beggar", "status": "Dying"})
                            
                        # Clear signal after processing narrative
                        cursor.execute("UPDATE active_stages SET npcs_json=?, conflict_signal=NULL WHERE id=?", (json.dumps(npcs), stage_id))
                        print(f"[Narrative Bubble] Handled {conflict_signal} at {s_name}!")
                        
        conn.commit()
        conn.close()
'''

if "class NarrativeStageManager" not in content:
    content += new_class
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("npc_behavior.py successfully modified.")
else:
    print("NarrativeStageManager already exists in npc_behavior.py.")
