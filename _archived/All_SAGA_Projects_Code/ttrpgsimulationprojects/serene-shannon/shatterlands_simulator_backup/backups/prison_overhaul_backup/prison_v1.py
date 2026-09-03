import random

# Chaos power thresholds
CHAOS_POWER_GROWTH_PER_TICK = 5       # p1 increase per tick (Wardens must fight this)
CULTIST_GROWTH_PER_TICK = 3           # hidden_cultists increase per tick
MONSTER_SPAWN_THRESHOLD = 30          # hidden_cultists needed to spawn a Cult Monster
MONSTER_SPAWN_CHANCE = 0.10           # 10% chance per tick once threshold is met
DRAGON_RELEASE_THRESHOLD = 250        # p1 at which the imprisoned dragon breaks free
DRAGON_RELEASE_RADIUS = 20            # global hex radius of catastrophic damage
DRAGON_ENTITY_DURATION = 500          # how many ticks the released dragon rampages


def process_prison_tick(engine_tick, s_id, name, domain, hidden, p_eco, g_hex_id, g_q, g_r,
                         global_rank3_cleanse, conn, cursor, log_event, unpack_ecology, pack_ecology):
    """
    Replaces all normal production, construction, and metabolism for a Cult Prison.
    Prisons are chaos accumulators. They do not gather resources or build infrastructure.
    They accumulate cultists and charge the imprisoned dragon's seals until either
    the Wardens cleanse them or the dragon breaks free in a catastrophic Blowout.

    Returns: (hidden, p_eco, g_updates) where g_updates is a list of (eco, hex_id) tuples.
    """
    p1, p2, p3, res = unpack_ecology(p_eco)
    g_updates = []

    # --- WARDEN CLEANSE (applied before growth so Wardens can actively counter) ---
    if global_rank3_cleanse > 0:
        cleansed_chaos = min(p1, global_rank3_cleanse * 10)
        p1 -= cleansed_chaos
        cleansed_cultists = min(hidden, global_rank3_cleanse * 2)
        hidden = max(0, hidden - cleansed_cultists)
        if cleansed_chaos > 0 or cleansed_cultists > 0:
            log_event("Warden", f"Rank 3 Wardens cleansed {int(cleansed_chaos)} chaos power and {int(cleansed_cultists)} cultists from {name}!", conn)

    # --- CHAOS POWER GROWTH (seals always weaken, even when cleansed) ---
    p1 = min(255, p1 + CHAOS_POWER_GROWTH_PER_TICK)

    # --- CULTIST ACCUMULATION ---
    hidden = min(255, hidden + CULTIST_GROWTH_PER_TICK)

    # --- CULT MONSTER SPAWNING ---
    if hidden >= MONSTER_SPAWN_THRESHOLD and random.random() < MONSTER_SPAWN_CHANCE:
        hidden = max(0, hidden - 15)  # Cultists sent out on raid
        cursor.execute(
            "INSERT INTO world_entities (type, global_hex_id, radius, duration, alignment) VALUES ('Cult Monster', ?, 2, 80, ?)",
            (g_hex_id, domain)
        )
        log_event("Chaos", f"A warband of Cultists erupted from {name} and marches upon the world!", conn)

    # --- DRAGON RELEASE (catastrophic Blowout) ---
    if p1 >= DRAGON_RELEASE_THRESHOLD:
        _trigger_dragon_release(engine_tick, domain, name, g_hex_id, g_q, g_r, cursor, log_event, conn)
        p1 = 0          # Prison is shattered — seals broken
        hidden = 0      # Cultists scattered by the cataclysm

    p_eco = pack_ecology(p1, p2, p3, res)
    g_updates.append((p_eco, g_hex_id))

    return hidden, p_eco, g_updates


def _trigger_dragon_release(engine_tick, domain, prison_name, g_hex_id, g_q, g_r, cursor, log_event, conn):
    """
    The imprisoned dragon of [domain] has broken free. Devastates all settlements
    within DRAGON_RELEASE_RADIUS global hexes. Spawns a long-duration world entity
    representing the rampaging dragon.
    """
    log_event(
        "CATACLYSM",
        f"THE DRAGON OF {domain.upper()} HAS SHATTERED ITS PRISON AT {prison_name}! "
        f"Reality tears — the Shattered World convulses!",
        conn
    )

    # Devastate all settlements within blast radius
    cursor.execute("SELECT id, name, population, wealth, global_hex_id FROM settlements")
    all_settlements = cursor.fetchall()

    cursor.execute("SELECT q, r FROM global_hexes WHERE id=?", (g_hex_id,))
    origin = cursor.fetchone()
    if not origin:
        return
    o_q, o_r = origin

    devastated = 0
    for a_sid, a_name, a_pop, a_wealth, a_g_id in all_settlements:
        cursor.execute("SELECT q, r FROM global_hexes WHERE id=?", (a_g_id,))
        a_hex = cursor.fetchone()
        if not a_hex:
            continue
        a_q, a_r = a_hex
        hex_dist = (abs(a_q - o_q) + abs(a_r - o_r) + abs(-a_q - a_r - (-o_q - o_r))) // 2
        if hex_dist <= DRAGON_RELEASE_RADIUS:
            new_pop = max(0, int(a_pop * 0.50))     # 50% population killed
            new_wealth = max(0.0, a_wealth * 0.20)  # 80% wealth destroyed
            cursor.execute(
                "UPDATE settlements SET population=?, wealth=? WHERE id=?",
                (new_pop, new_wealth, a_sid)
            )
            log_event(
                "CATACLYSM",
                f"{a_name} was devastated by the Dragon of {domain}! "
                f"Pop: {a_pop} -> {new_pop}. Wealth: {a_wealth:.0f} -> {new_wealth:.0f}.",
                conn
            )
            devastated += 1

    # Spawn the dragon as a long-duration, wide-radius world entity
    cursor.execute(
        "INSERT INTO world_entities (type, global_hex_id, radius, duration, alignment) "
        "VALUES ('Chaos Creature', ?, ?, ?, ?)",
        (g_hex_id, 15, DRAGON_ENTITY_DURATION, domain)
    )

    log_event(
        "CATACLYSM",
        f"The Dragon of {domain} ravages the world! {devastated} settlements devastated. "
        f"The Wardens must mount a grand offensive to reseal it!",
        conn
    )
