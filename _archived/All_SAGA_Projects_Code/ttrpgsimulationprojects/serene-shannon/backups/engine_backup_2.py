import sqlite3
import random
import os
import json
import math
from core_engine.codec import unpack_micro_cluster, pack_micro_cluster
from core_engine.fractal_core import process_cluster_fidelity

# Import modular phases
import core_engine.chaos as chaos
import core_engine.combat as combat
import core_engine.politics as politics
import core_engine.metabolism as metabolism
from core_engine.db_setup import apply_migrations

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world_state.db")

def unpack_ecology(pack_val):
    p1 = pack_val & 0xFF
    p2 = (pack_val >> 8) & 0xFF
    p3 = (pack_val >> 16) & 0xFF
    res = (pack_val >> 24) & 0xFFFF
    return p1, p2, p3, res

def pack_ecology(p1, p2, p3, res):
    p1 = max(0, min(255, int(p1)))
    p2 = max(0, min(255, int(p2)))
    p3 = max(0, min(255, int(p3)))
    res = max(0, min(65535, int(res)))
    return p1 | (p2 << 8) | (p3 << 16) | (res << 24)

def get_calendar_info(tick):
    total_days = tick
    year = 1650 + (total_days // 539)
    day_of_year = (total_days % 539) + 1

    months = [("Nexar", 35), ("Massis", 28), ("Motom", 21), ("Fluxen", 42), ("Vitan", 49), ("Lexis", 28), ("Ration", 28), ("Ordis", 28), ("Luxen", 49), ("Omin", 63), ("Aurum", 35), ("Anum", 42), ("Maelen", 84), ("Shadowfall", 7)]
    current_month = ""
    day_of_month = day_of_year
    for m_name, m_days in months:
        if day_of_month <= m_days:
            current_month = m_name
            break
        day_of_month -= m_days

    seasons = [("Shadowburn", 84), ("Dryspell", 42), ("Frostin", 49), ("GreenSpan", 84), ("Highreach", 112), ("Spurium", 77), ("Dimfreeze", 84), ("Shadowfall", 7)]
    current_season = ""
    day_in_season = day_of_year
    for s_name, s_days in seasons:
        if day_in_season <= s_days:
            current_season = s_name
            break
        day_in_season -= s_days

    return year, current_month, day_of_month, current_season

def spend_modular_cost(inventory, group, amount):
    if group not in inventory: return False, {}
    total_available = sum(inventory[group].values())
    if total_available < amount: return False, {}

    used = {}
    remaining = amount
    for res_name, res_amount in list(inventory[group].items()):
        if remaining <= 0: break
        take = min(res_amount, remaining)
        inventory[group][res_name] -= take
        remaining -= take
        used[res_name] = take
    return True, used

def get_total(inventory, group):
    if group not in inventory: return 0
    return sum(inventory[group].values())

def get_neighbors(q, r):
    return [(q, r-1), (q+1, r-1), (q+1, r), (q, r+1), (q-1, r+1), (q-1, r)]

def step_towards_origin(q, r):
    if q == 0 and r == 0: return (0, 0)
    best = (q, r)
    min_dist = abs(q) + abs(r) + abs(-q-r)
    for nq, nr in get_neighbors(q, r):
        dist = abs(nq) + abs(nr) + abs(-nq-nr)
        if dist < min_dist:
            min_dist = dist
            best = (nq, nr)
    return best

def wrap_hex(q, r, L=25):
    triangles = {}
    for i in range(5):
        triangles[i*4] = ('UP', (i+1)*L + i, -L)
        triangles[i*4 + 1] = ('DN', i*L + i + 1, L-1)
        triangles[i*4 + 2] = ('UP', i*L + i + 1 + L, 0)
        triangles[i*4 + 3] = ('DN', i*L + i + 1, 2*L - 1)

    connections = {}
    for i in range(5):
        t_top, t_mid_dn, t_mid_up, t_bot_dn = i*4, i*4+1, i*4+2, i*4+3
        connections[(t_top, 'B')] = (t_mid_dn, 'T')
        connections[(t_mid_dn, 'T')] = (t_top, 'B')
        connections[(t_mid_dn, 'R')] = (t_mid_up, 'L')
        connections[(t_mid_up, 'L')] = (t_mid_dn, 'R')
        connections[(t_mid_up, 'B')] = (t_bot_dn, 'T')
        connections[(t_bot_dn, 'T')] = (t_mid_up, 'B')

        prev_up = ((i-1)%5)*4+2
        connections[(t_mid_dn, 'L')] = (prev_up, 'R')
        connections[(prev_up, 'R')] = (t_mid_dn, 'L')

        prev_top, next_top = ((i-1)%5)*4, ((i+1)%5)*4
        connections[(t_top, 'L')] = (prev_top, 'R')
        connections[(t_top, 'R')] = (next_top, 'L')

        prev_bot, next_bot = ((i-1)%5)*4+3, ((i+1)%5)*4+3
        connections[(t_bot_dn, 'L')] = (prev_bot, 'R')
        connections[(t_bot_dn, 'R')] = (next_bot, 'L')

    best_t = -1
    best_dist = 999999
    best_b = None
    for t_id, (t_type, q0, r0) in triangles.items():
        if t_type == 'UP':
            b0, b1, b2 = r0 + L - 1 - r, q + r - (q0 + r0), q0 - q
        else:
            b0, b1, b2 = r - (r0 - L + 1), q - q0, q0 + r0 - (q + r)

        dist = 0
        if b0 < 0: dist -= b0
        if b1 < 0: dist -= b1
        if b2 < 0: dist -= b2
        if dist == 0: return q, r

        if dist < best_dist:
            best_dist, best_t, best_b = dist, t_id, (b0, b1, b2)

    if best_dist > 5: return q, r

    t_type = triangles[best_t][0]
    b0, b1, b2 = best_b
    edge = 'B' if t_type == 'UP' and b0 < 0 else 'T' if t_type == 'DN' and b0 < 0 else 'L' if b1 < 0 else 'R'

    conn = connections.get((best_t, edge))
    if not conn: return q, r
    nt_id, n_edge = conn
    nt_type, nq0, nr0 = triangles[nt_id]

    nb0, nb1, nb2 = b0, b1, b2
    if edge in ['L', 'R'] and n_edge in ['L', 'R']:
        nb0, nb1, nb2 = b0, b2, b1

    if nt_type == 'UP':
        return nq0 - nb2, nr0 + L - 1 - nb0
    else:
        return nq0 + nb1, nr0 - L + 1 + nb0

def step_towards(q, r, t_q, t_r):
    if q == t_q and r == t_r: return (q, r)
    best = (q, r)
    min_dist = abs(q - t_q) + abs(r - t_r) + abs(-q-r - (-t_q-t_r))
    for nq, nr in get_neighbors(q, r):
        dist = abs(nq - t_q) + abs(nr - t_r) + abs(-nq-nr - (-t_q-t_r))
        if dist < min_dist:
            min_dist = dist
            best = (nq, nr)
    return best

class GlobalEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.tick = 0
        conn = sqlite3.connect(self.db_path)
        
        # Run active migrations ONCE during engine initialization
        apply_migrations(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT value FROM metadata WHERE key='current_tick'")
        row = cursor.fetchone()
        if row: self.tick = int(row[0])
        else:
            cursor.execute("INSERT INTO metadata (key, value) VALUES ('current_tick', '0')")
            conn.commit()

        cursor.execute("SELECT value FROM metadata WHERE key='cartel_inventory'")
        c_row = cursor.fetchone()
        if c_row:
            self.cartel_inventory = json.loads(c_row[0])
        else:
            self.cartel_inventory = {"Raw": {}, "BlackMarket": {}}
            cursor.execute("INSERT INTO metadata (key, value) VALUES ('cartel_inventory', ?)", (json.dumps(self.cartel_inventory),))
            conn.commit()

        self.year, self.month, self.day, self.season = get_calendar_info(self.tick)
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_year', ?)", (str(self.year),))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_month', ?)", (self.month,))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_day', ?)", (str(self.day),))
        cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('current_season', ?)", (self.season,))
        conn.commit()
        conn.close()

    def save_metadata(self, conn):
        conn.execute("UPDATE metadata SET value=? WHERE key='current_tick'", (str(self.tick),))
        conn.execute("UPDATE metadata SET value=? WHERE key='cartel_inventory'", (json.dumps(self.cartel_inventory),))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_year'", (str(self.year),))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_month'", (self.month,))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_day'", (str(self.day),))
        conn.execute("UPDATE metadata SET value=? WHERE key='current_season'", (self.season,))

    def log_event(self, category, msg, conn, q=None, r=None):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO event_log (tick, category, message, global_q, global_r) VALUES (?, ?, ?, ?, ?)", (self.tick, category, msg, q, r))

    def trigger_tick(self):
        self.tick += 1
        self.year, self.month, self.day, self.season = get_calendar_info(self.tick)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if the world has already ended — refuse to run further ticks
        cursor.execute("SELECT value FROM metadata WHERE key='world_ended'")
        we_row = cursor.fetchone()
        if we_row and we_row[0] == '1':
            cursor.execute("SELECT value FROM metadata WHERE key='world_end_cause'")
            cause_row = cursor.fetchone()
            cause = cause_row[0] if cause_row else "Unknown cataclysm"
            print(f"[WORLD_END] The simulation has ended. Cause: {cause}")
            print("[WORLD_END] No further ticks are possible. The world is unmade.")
            conn.close()
            return

        # Phase 1: Environment & Chaos (Global Pass)
        # Spawn Rare Deposits (Mithril / Star-Herb) every 30 ticks
        if self.tick % 30 == 0:
            cursor.execute("SELECT id, q, r FROM global_hexes ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            if row:
                g_id, g_q, g_r = row
                res_type = random.choice(["Mithril", "Star-Herb"])
                cursor.execute("SELECT pack_ecology FROM global_hexes WHERE id=?", (g_id,))
                eco = cursor.fetchone()[0]
                p1, p2, p3, res = unpack_ecology(eco)
                cursor.execute("SELECT micro_data_json FROM global_hexes WHERE id=?", (g_id,))
                m_json = cursor.fetchone()[0]
                try:
                    micro_hexes = unpack_micro_cluster(g_q, g_r, 0, 0, eco, m_json)
                except:
                    micro_hexes = {}
                if micro_hexes:
                    center_hx = micro_hexes.get((0,0))
                    if center_hx:
                        center_hx.res = 1000
                        try:
                            m_data = json.loads(m_json) if m_json else {}
                        except:
                            m_data = {}
                        if isinstance(m_data, list):
                            m_data = {"hexes": m_data}
                        m_data.setdefault("rule_overrides", {})["rare_resource"] = res_type
                        cursor.execute("UPDATE global_hexes SET micro_data_json=?, pack_ecology=? WHERE id=?", (json.dumps(m_data), pack_ecology(p1, p2, p3, 1000), g_id))
                        self.log_event("Resources", f"A rare deposit of {res_type} has been discovered at ({g_q}, {g_r})!", conn)

        chaos.process_global_chaos_flow(cursor, self.season)
        chaos.manage_weather(cursor, conn, self.tick, self.season, self.log_event)

        # Build chaos nodes mapping for paths check
        chaos_nodes = []
        random.seed(12345)
        for i in range(12):
            lat = math.asin(2 * random.random() - 1)
            lon = 2 * math.pi * random.random()
            chaos_nodes.append({"lon": lon, "lat": lat})
        random.seed()

        cursor.execute("SELECT q, r, chaos_domain FROM global_hexes WHERE chaos_domain IS NOT NULL")
        prison_coords = {row[2]: (row[0], row[1]) for row in cursor.fetchall()}

        is_hex_in_chaos_flow_fn = lambda q, r, nodes, t: chaos.is_hex_in_chaos_flow(q, r, nodes, t)
        active_entities = combat.process_world_entities(cursor, conn, self.tick, prison_coords, self.log_event, is_hex_in_chaos_flow_fn, chaos_nodes)

        # Phase 2: Upkeep & Infrastructure (Defense Pass) - Part of process_cluster_fidelity metabolic passes
        # Phase 3: Production & Trade (Logistics Pass)
        cursor.execute("""
            SELECT s.id, s.faction_id, s.global_hex_id, s.name, s.settlement_level, s.population, s.spark_born_population, s.wealth, s.security_points, s.inventory_json, s.hidden_cultists, s.magic_loadout,
                   g.q, g.r, g.pack_geo, g.pack_meso, g.pack_ecology, g.micro_data_json, g.river_volume, g.is_lake, g.chaos_domain,
                   f.special_rule, s.micro_q, s.micro_r
            FROM settlements s
            JOIN global_hexes g ON s.global_hex_id = g.id
            JOIN factions f ON s.faction_id = f.id
        """)
        settlements = cursor.fetchall()

        if self.tick % 10 == 0:
            politics.process_diplomacy(cursor, conn, settlements, self.log_event)
            politics.process_trade_routes(cursor, conn)
            politics.process_paragons(cursor, conn, settlements, self.log_event)

        # Phase 4: Consumption & Demographics (Life Pass)
        metabolism.process_crimes(cursor)

        normal_settlements = [row for row in settlements if not row[3].startswith("Prison") and row[3] != "The Warden Spire"]
        normal_settlements.sort(key=lambda x: x[6])
        clockwork_buffs = {s[0]: 50.0 for s in normal_settlements[:max(1, len(normal_settlements)//10)]}
        clockwork_debuffs = {s[0]: 50.0 for s in normal_settlements[-max(1, len(normal_settlements)//10):]}

        prisons = {}
        warden_spire = None
        for row in settlements:
            if row[3].startswith("Prison of "): prisons[row[20]] = (row[0], row[5])
            if row[3] == "The Warden Spire": warden_spire = row

        s_updates = []
        g_updates = []

        weather_farm_mod = 1.0
        weather_consume_mod = 1.0

        if self.season in ["Shadowburn", "Highreach"]: weather_farm_mod = 1.5
        elif self.season in ["Frostin", "Dimfreeze"]:
            weather_farm_mod = 0.5
            weather_consume_mod = 1.5
        elif self.season == "GreenSpan": weather_farm_mod = 2.0
        elif self.season == "Shadowfall": weather_farm_mod = 0.0

        global_rank2_cleanse = 0
        global_rank3_cleanse = 0

        if warden_spire:
            s_id, f_id, g_hex_id, name, s_level, pop, spark_pop, wealth, sec, inv_str, hidden, loadout_str, q, r, p_geo, p_meso, p_eco, micro, rvol, islake, domain, f_rule, m_q, m_r = warden_spire
            inventory = json.loads(inv_str)
            ranks = inventory.get("Warden Ranks", {"Rank 1": 0, "Rank 2": 0, "Rank 3": 0, "Rank 4": 0})

            inventory["Warden Ranks"]["Rank 1"] = ranks.get("Rank 1", 0) + 1
            pop += 1
            if random.random() < 0.5: spark_pop += 1

            if random.random() < 0.10 and ranks["Rank 1"] > 0:
                ranks["Rank 1"] -= 1; ranks["Rank 2"] += 1
            if random.random() < 0.05 and ranks["Rank 2"] > 0:
                ranks["Rank 2"] -= 1; ranks["Rank 3"] += 1
            if random.random() < 0.01 and ranks["Rank 3"] > 0:
                ranks["Rank 3"] -= 1; ranks["Rank 4"] += 1

            if ranks["Rank 1"] > 0:
                inventory.setdefault("Building", {})["Stone"] = inventory.get("Building", {}).get("Stone", 0) + ranks["Rank 1"]
            global_rank2_cleanse = ranks["Rank 2"]
            global_rank3_cleanse = ranks["Rank 3"]

            if ranks["Rank 4"] > 0:
                cursor.execute("SELECT id, pack_ecology, chaos_domain FROM global_hexes WHERE chaos_domain IS NOT NULL")
                prison_hexes = cursor.fetchall()
                highest_hex = None
                highest_p1 = 0
                for ph_id, ph_eco, ph_dom in prison_hexes:
                    ph_p1 = unpack_ecology(ph_eco)[0]
                    if ph_p1 > highest_p1:
                        highest_p1 = ph_p1
                        highest_hex = ph_id

                if highest_p1 >= 200:
                    ranks["Rank 4"] -= 1
                    pop -= 1
                    cursor.execute("UPDATE global_hexes SET pack_ecology=pack_ecology & 0xFFFFFF00 WHERE id=?", (highest_hex,))
                    self.log_event("Kamikaze", f"A Rank 4 Warden sacrificed themselves to seal a Prison!", conn)

            inventory["Warden Ranks"] = ranks
            sec = max(0.0, min(100.0, sec))
            s_updates.append((s_level, pop, spark_pop, wealth, sec, json.dumps(inventory), hidden, s_id))

        for row in settlements:
            s_id, f_id, g_hex_id, name, s_level, pop, spark_pop, wealth, sec, inv_str, hidden, loadout_str, q, r, p_geo, p_meso, p_eco, micro_json, river_vol, is_lake, domain, f_rule, m_q, m_r = row
            if name == "The Warden Spire": continue

            try: loadout = json.loads(loadout_str)
            except: loadout = ["Mass", "Mass", "Mass"]
            primary_dragon = loadout[0] if loadout else "Mass"

            if not name.startswith("Prison"):
                sec += (pop * 0.001)
                wealth += (pop * 0.005)

                if f_rule == "Ursine_Hegemony":
                    sec += (pop * 0.002)
                    local_weather_farm = 1.2
                elif f_rule == "Heartland_Alliance":
                    if (p_geo & 0xF) == 4: local_weather_farm = 3.0
                    sec += 20.0
                elif f_rule == "Iron_Caldera":
                    if (p_geo & 0xF) in [7, 3]: wealth += 50.0
                elif f_rule == "Sylvan_Empire":
                    if (p_geo & 0xF) == 1: sec += 50.0
                elif f_rule == "Canopy_Clans":
                    if (p_geo & 0xF) == 0: local_weather_farm = 2.0
                elif f_rule == "Eastern_Hounds":
                    hidden = 0
                elif f_rule == "Flower_Valley":
                    sec += 100.0
                elif f_rule == "Hive_Commonwealth":
                    wealth += 20.0
                elif f_rule == "Coastal_Theocracy" and (river_vol > 0 or is_lake or (p_geo & 0xF) >= 9):
                    sec += (pop * 0.001)

                if s_id in clockwork_buffs: wealth += clockwork_buffs[s_id]
                if s_id in clockwork_debuffs: wealth = max(0, wealth - clockwork_debuffs[s_id])

            try: inventory = json.loads(inv_str)
            except: inventory = {"Survival": {}, "Building": {}, "Materials": {}, "Reagents": {}, "Magic": {}, "Equipment": {}, "Consumables": {}, "Vehicles": {}}
            for group in ["Survival", "Building", "Materials", "Reagents", "Magic", "Equipment", "Consumables", "Vehicles"]:
                if group not in inventory: inventory[group] = {}

            cell_tags = []
            rule_overrides = {}
            if micro_json:
                try:
                    micro_data = json.loads(micro_json)
                    if isinstance(micro_data, dict):
                        cell_tags = micro_data.get("tags", [])
                        rule_overrides = micro_data.get("rule_overrides", {})
                except json.JSONDecodeError:
                    pass

            pop_growth_mod = rule_overrides.get("population_growth_modifier", 1.0)
            res_tick_mod = rule_overrides.get("resource_tick_multiplier", 1.0)

            local_weather_farm = 1.0 * res_tick_mod
            local_consume = 1.0

            is_flammable = "FLAMMABLE" in cell_tags

            for w_id, w_type, w_g_id, w_rad, wq, wr, w_align in active_entities:
                if w_g_id == g_hex_id:
                    dist = (abs(m_q - wq) + abs(m_r - wr) + abs(-m_q-m_r - (-wq-wr))) // 2
                    if dist <= w_rad:
                        command_tags = []
                        if w_align:
                            command_tags = [tag.strip() for tag in w_align.split(',')]

                        if "FIRE" in command_tags and is_flammable:
                            self.log_event("Chaos", f"A FIRE storm mutated a FLAMMABLE cell at {name} into CHARRED ruins!", conn)
                            if "CHARRED" not in cell_tags:
                                cell_tags.append("CHARRED")
                            if "FLAMMABLE" in cell_tags:
                                cell_tags.remove("FLAMMABLE")
                            is_flammable = False
                            sec -= 10.0
                            pop = max(0, pop - int(pop * 0.1))
                            try:
                                md = json.loads(micro_json) if micro_json else {}
                                if isinstance(md, dict):
                                    md["tags"] = cell_tags
                                    micro_json = json.dumps(md)
                                    cursor.execute("UPDATE global_hexes SET micro_data_json=? WHERE id=?", (micro_json, g_hex_id))
                            except json.JSONDecodeError:
                                pass

                        if w_type == "Hurricane": local_weather_farm *= 0.5
                        elif w_type == "Tornado": sec -= 5.0
                        elif w_type == "Overcast": local_weather_farm *= 1.2
                        elif w_type in ["Chaos Storm", "Cult Monster"]:
                            if f_rule == "Reliance":
                                pass
                            elif f_rule == "Prism_Scale" and w_align == "Lux":
                                pass
                            else:
                                pop, sec, inventory, d_farm, d_con, p_geo = chaos.apply_chaos_event(w_align, name, pop, sec, inventory, q, r, p_geo, cursor, conn, self.log_event)
                                local_weather_farm *= d_farm
                                local_consume *= d_con

                                if f_rule == "Sylvan_Empire" and w_align == "Nexus":
                                    sec -= 50.0

                                if "Inverted Physics" not in inventory.get("Tags", []) and f_rule != "Eastern_Hounds":
                                    if random.random() < 0.5: hidden += 1

                        elif w_type == "Chaos Creature":
                            sec -= 20.0
                            pop = max(0, pop - int(pop * 0.05))
                        elif w_type == "Null Zealots":
                            if name.startswith("Prison of "):
                                global_rank3_cleanse += 5
                            else:
                                sec -= 10.0
                                killed = min(spark_pop, max(1, int(spark_pop * 0.20)))
                                spark_pop = max(0, spark_pop - killed)
                                pop = max(0, pop - killed)
                                self.log_event("Mandate", f"Null Zealots raided {name}! Pop reduced.", conn)

                                # Drain Sparkborn power to nearest prison
                                if prison_coords:
                                    closest_prison_domain = None
                                    min_dist = 999999
                                    for dom, (pq, pr) in prison_coords.items():
                                        dist_p = (abs(q - pq) + abs(r - pr) + abs(-q-r - (-pq-pr))) // 2
                                        if dist_p < min_dist:
                                            min_dist = dist_p
                                            closest_prison_domain = dom
                                    if closest_prison_domain:
                                        cursor.execute("UPDATE global_hexes SET pack_ecology = (pack_ecology & 0xFFFFFF00) | MIN(255, (pack_ecology & 0xFF) + ?) WHERE chaos_domain=?", (killed * 5, closest_prison_domain))
                                        self.log_event("Mandate", f"Null Zealots drained {killed} Sparkborn from {name}, strengthening the Prison of {closest_prison_domain}!", conn)

            if river_vol > 0 or is_lake:
                local_weather_farm *= 1.5

            farm_mult = weather_farm_mod * local_weather_farm * max(0.1, 1.0 - (hidden * 0.05))

            if self.tick % 10 == 0 and pop > 0:
                pop += int(max(1, pop * 0.01 * pop_growth_mod))

            if global_rank2_cleanse > 0 and hidden > 0:
                cleansed = min(hidden, global_rank2_cleanse)
                hidden -= cleansed
                global_rank2_cleanse -= cleansed

            if hidden >= 10:
                hidden -= 1
                pop = max(0, pop - 1)
                if prisons:
                    target_domain = random.choice(list(prisons.keys()))
                    p_s_id, _ = prisons[target_domain]
                    cursor.execute("UPDATE settlements SET population = population + 1 WHERE id=?", (p_s_id,))

            # Prison tick logic (chaos accumulation, cultist growth, dragon release)
            # is handled entirely in fractal_core.py -> prison.py.
            # The engine only manages Warden Rank-level cleanse and world-entity
            # spawning for the global pass. Skip the engine-level s_update for prisons.
            if name.startswith("Prison of "):
                continue

            sec = max(0.0, min(100.0, sec))
            s_updates.append((s_level, pop, spark_pop, wealth, sec, json.dumps(inventory), hidden, s_id))

        cursor.executemany("UPDATE settlements SET settlement_level=?, population=?, spark_born_population=?, wealth=?, security_points=?, inventory_json=?, hidden_cultists=? WHERE id=?", s_updates)
        if g_updates:
            cursor.executemany("UPDATE global_hexes SET pack_ecology=? WHERE id=?", g_updates)

        # Phase 5: State Commit & Logging (Transaction Pass)
        cursor.execute("SELECT DISTINCT global_hex_id FROM settlements")
        active_clusters = cursor.fetchall()
        for (c_id,) in active_clusters:
            cluster_world_ended = process_cluster_fidelity(self.tick, c_id, conn)
            if cluster_world_ended:
                self.save_metadata(conn)
                conn.commit()
                conn.close()
                print("[WORLD_END] Dragon released. World unmade. Simulation halted.")
                return

        self.save_metadata(conn)
        conn.commit()
        conn.close()
