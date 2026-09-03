import random

# ── Tuning constants ─────────────────────────────────────────────────────────
CULTIST_POP_GROWTH        = 1      
CULTIST_DESTROY_CHANCE    = 0.05   
CULTIST_MONSTER_CHANCE    = 0.6    
CHAOS_POWER_BASE_GROWTH   = 5      
CULTIST_ABSORPTION_RATE   = 0.06   
CULTIST_DANGER_RATE       = 0.008  
CHAOS_PATH_DIVISOR        = 25     
DRAGON_RELEASE_THRESHOLD  = 250    
DRAGON_RELEASE_RADIUS = 20
DRAGON_ENTITY_DURATION = 500

def process_prison_tick(engine_tick, s_id, name, domain, hidden, prison_pop, p_eco, g_hex_id, g_q, g_r,
                         global_rank3_cleanse, conn, cursor, log_event, unpack_ecology, pack_ecology):
    p1, p2, p3, res = unpack_ecology(p_eco)
    g_updates = []
    w_ended = False

    if global_rank3_cleanse > 0:
        cleansed_chaos = min(p1, global_rank3_cleanse * 10)
        p1 -= cleansed_chaos
        cleansed_cultists = min(hidden, global_rank3_cleanse * 2)
        hidden = max(0, hidden - cleansed_cultists)
        if cleansed_chaos > 0 or cleansed_cultists > 0:
            log_event("Warden", f"Rank 3 Wardens cleansed {int(cleansed_chaos)} chaos power and {int(cleansed_cultists)} cultists from {name}!", conn)

    p1 = min(255, p1 + CHAOS_POWER_BASE_GROWTH)
    hidden = min(255, hidden + CULTIST_POP_GROWTH)

    if hidden >= 30 and random.random() < 0.10:
        hidden = max(0, hidden - 15)
        cursor.execute(
            "INSERT INTO world_entities (type, global_hex_id, radius, duration, alignment) VALUES ('Cult Monster', ?, 2, 80, ?)",
            (g_hex_id, domain)
        )
        log_event("Chaos", f"A warband of Cultists erupted from {name} and marches upon the world!", conn)

    if p1 >= DRAGON_RELEASE_THRESHOLD:
        _trigger_dragon_release(engine_tick, domain, name, g_hex_id, g_q, g_r, cursor, log_event, conn)
        p1 = 0
        hidden = 0
        w_ended = True

    p_eco = pack_ecology(p1, p2, p3, res)
    g_updates.append((p_eco, g_hex_id))

    return hidden, prison_pop, p_eco, g_updates, w_ended

def _trigger_dragon_release(engine_tick, domain, prison_name, g_hex_id, g_q, g_r, cursor, log_event, conn):
    log_event("CATACLYSM", f"THE DRAGON OF {domain.upper()} HAS SHATTERED ITS PRISON AT {prison_name}! Reality tears — the Shattered World convulses!", conn)

    cursor.execute("SELECT id, name, population, wealth, global_hex_id FROM settlements")
    all_settlements = cursor.fetchall()

    cursor.execute("SELECT q, r FROM global_hexes WHERE id=?", (g_hex_id,))
    origin = cursor.fetchone()
    if not origin: return
    o_q, o_r = origin

    devastated = 0
    for a_sid, a_name, a_pop, a_wealth, a_g_id in all_settlements:
        cursor.execute("SELECT q, r FROM global_hexes WHERE id=?", (a_g_id,))
        a_hex = cursor.fetchone()
        if not a_hex: continue
        a_q, a_r = a_hex
        hex_dist = (abs(a_q - o_q) + abs(a_r - o_r) + abs(-a_q - a_r - (-o_q - o_r))) // 2
        if hex_dist <= DRAGON_RELEASE_RADIUS:
            new_pop = max(0, int(a_pop * 0.50))
            new_wealth = max(0.0, a_wealth * 0.20)
            cursor.execute("UPDATE settlements SET population=?, wealth=? WHERE id=?", (new_pop, new_wealth, a_sid))
            devastated += 1

    cursor.execute("INSERT INTO world_entities (type, global_hex_id, radius, duration, alignment) VALUES ('Chaos Creature', ?, ?, ?, ?)", (g_hex_id, 15, DRAGON_ENTITY_DURATION, domain))
    log_event("CATACLYSM", f"The Dragon of {domain} ravages the world! {devastated} settlements devastated.", conn)
