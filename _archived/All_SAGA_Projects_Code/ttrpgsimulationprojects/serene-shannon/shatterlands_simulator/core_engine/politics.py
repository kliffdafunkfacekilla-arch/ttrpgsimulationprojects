import sqlite3
import random

def trust_to_status(trust):
    if trust > 80:   return 'Alliance'
    if trust > 40:   return 'Trading'
    if trust < -50:  return 'War'
    return 'Neutral'

def apply_trust_delta(fa_id, fb_id, delta, cursor):
    cursor.execute(
        "SELECT trust_level FROM faction_relations WHERE faction_a_id=? AND faction_b_id=?",
        (fa_id, fb_id)
    )
    row = cursor.fetchone()
    trust = (row[0] if row else 0) + delta
    trust = max(-100, min(100, trust))
    status = trust_to_status(trust)
    cursor.execute(
        "INSERT OR REPLACE INTO faction_relations (faction_a_id, faction_b_id, status, trust_level) VALUES (?,?,?,?)",
        (fa_id, fb_id, status, trust)
    )
    cursor.execute(
        "INSERT OR REPLACE INTO faction_relations (faction_a_id, faction_b_id, status, trust_level) VALUES (?,?,?,?)",
        (fb_id, fa_id, status, trust)
    )

def process_diplomacy(cursor, conn, settlements, log_event_fn):
    cursor.execute("SELECT id, name, special_rule FROM factions")
    factions = {row[0]: row for row in cursor.fetchall()}

    f_ids = list(factions.keys())
    if len(f_ids) < 2:
        return

    for i in range(len(f_ids)):
        for j in range(i + 1, len(f_ids)):
            fa, fb = f_ids[i], f_ids[j]
            cursor.execute(
                "INSERT OR IGNORE INTO faction_relations (faction_a_id, faction_b_id, status, trust_level) VALUES (?,?,'Neutral',0)",
                (fa, fb)
            )
            cursor.execute(
                "INSERT OR IGNORE INTO faction_relations (faction_a_id, faction_b_id, status, trust_level) VALUES (?,?,'Neutral',0)",
                (fb, fa)
            )

    existing = cursor.execute("SELECT COUNT(*) FROM diplomacy_relations").fetchone()[0]
    if existing == 0:
        settlement_list = [(s[0], s[1]) for s in settlements]
        if len(settlement_list) >= 2:
            pairs_added = 0
            attempts = 0
            while pairs_added < min(6, len(settlement_list)) and attempts < 30:
                attempts += 1
                a, b = random.sample(settlement_list, 2)
                if a[1] != b[1]:
                    cursor.execute(
                        "INSERT OR REPLACE INTO diplomacy_relations (settlement_a_id, settlement_b_id, score) VALUES (?,?,50)",
                        (a[0], b[0])
                    )
                    cursor.execute(
                        "INSERT OR REPLACE INTO diplomacy_relations (settlement_a_id, settlement_b_id, score) VALUES (?,?,50)",
                        (b[0], a[0])
                    )
                    pairs_added += 1

    processed_pairs = set()
    for fa in f_ids:
        for fb in f_ids:
            if fa >= fb:
                continue
            pair_key = (fa, fb)
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)

            ra = factions[fa][2]
            rb = factions[fb][2]

            if ra == "Cult" or rb == "Cult":
                continue

            cursor.execute(
                "SELECT trust_level, status FROM faction_relations WHERE faction_a_id=? AND faction_b_id=?",
                (fa, fb)
            )
            row = cursor.fetchone()
            trust = row[0] if row else 0
            old_status = row[1] if row else 'Neutral'

            if ra == "Vaneer_Concord" or rb == "Vaneer_Concord":
                trust += 2
            if ra == "Prism_Scale" or rb == "Prism_Scale":
                trust += 5
            if ra == "Eastern_Hounds" or rb == "Eastern_Hounds":
                trust = max(trust, 0)

            trust += random.randint(-5, 5)
            trust = max(-100, min(100, trust))

            if trust > 80:
                status = 'Alliance'
            elif trust > 40:
                status = 'Trading'
            elif trust < -50:
                if (ra == "Vaneer_Concord" or rb == "Vaneer_Concord") and trust > -90:
                    status = 'Neutral'
                else:
                    status = 'War'
            else:
                status = 'Neutral'

            cursor.execute(
                "INSERT OR REPLACE INTO faction_relations (faction_a_id, faction_b_id, status, trust_level) VALUES (?,?,?,?)",
                (fa, fb, status, trust)
            )
            cursor.execute(
                "INSERT OR REPLACE INTO faction_relations (faction_a_id, faction_b_id, status, trust_level) VALUES (?,?,?,?)",
                (fb, fa, status, trust)
            )

            if status == 'War':
                s1 = [s for s in settlements if s[1] == fa]
                s2 = [s for s in settlements if s[1] == fb]
                if s1 and s2:
                    s_a = random.choice(s1)
                    s_b = random.choice(s2)
                    cp_a = s_a[8]
                    cp_b = s_b[8]
                    if ra == "Ursine_Hegemony": cp_a *= 3.0
                    if rb == "Ursine_Hegemony": cp_b *= 3.0
                    if rb == "Guerrilla_Clans": cp_b += max(0, 100 - s_b[5]) * 2.0
                    if rb == "Scute_Confederacy": cp_b *= 2.0
                    if cp_a > cp_b * 1.5:
                        log_event_fn("Diplomacy", f"{factions[fa][1]} conquered {s_b[3]} from {factions[fb][1]}! (trust:{trust})", conn)
                        cursor.execute("UPDATE settlements SET faction_id=?, security_points=security_points/2 WHERE id=?", (fa, s_b[0]))
                    else:
                        if old_status != 'War':
                            log_event_fn("Diplomacy", f"{factions[fa][1]} and {factions[fb][1]} entered conflict — skirmish near {s_b[3]}. (trust:{trust})", conn)
                        cursor.execute("UPDATE settlements SET security_points = max(0, security_points - 2) WHERE id=?", (s_a[0],))
                        cursor.execute("UPDATE settlements SET security_points = max(0, security_points - 2) WHERE id=?", (s_b[0],))

            elif status in ('Trading', 'Alliance'):
                if old_status != status:
                    log_event_fn("Diplomacy", f"{factions[fa][1]} and {factions[fb][1]} are now {status}. (trust:{trust})", conn)
                s1 = [s for s in settlements if s[1] == fa]
                s2 = [s for s in settlements if s[1] == fb]
                if s1 and s2:
                    s_a = random.choice(s1)
                    s_b = random.choice(s2)
                    route_type = 'Land'
                    cursor.execute(
                        "INSERT INTO trade_routes (faction_id, settlement_a_id, settlement_b_id, route_type) VALUES (?,?,?,?)",
                        (fa, s_a[0], s_b[0], route_type)
                    )
                    if status == 'Alliance' and ra == "Fulcrum_Academy":
                        cursor.execute(
                            "UPDATE factions SET technology_level = max(technology_level, (SELECT technology_level FROM factions WHERE id=?)) WHERE id=?",
                            (fa, fb)
                        )

            elif status == 'Neutral' and old_status in ('War', 'Alliance', 'Trading'):
                log_event_fn("Diplomacy", f"{factions[fa][1]} and {factions[fb][1]} returned to Neutral. (trust:{trust})", conn)

def process_trade_routes(cursor, conn):
    cursor.execute("""
        SELECT tr.id, tr.faction_id, tr.settlement_a_id, tr.settlement_b_id, tr.route_type,
               sa.wealth, sa.security_points, sb.wealth, sb.security_points,
               sa.global_hex_id, sb.global_hex_id, f.special_rule
        FROM trade_routes tr
        JOIN settlements sa ON tr.settlement_a_id = sa.id
        JOIN settlements sb ON tr.settlement_b_id = sb.id
        JOIN factions f ON tr.faction_id = f.id
    """)
    routes = cursor.fetchall()

    sa_updates = []
    for row in routes:
        tr_id, f_id, sa_id, sb_id, r_type, w_a, sec_a, w_b, sec_b, g_a, g_b, f_rule = row

        yield_val = 15.0

        is_chaos = random.random() < 0.2
        if is_chaos and f_rule != "Sumpkin":
            yield_val = 0.0

        if r_type == 'Land' and f_rule == "Dust_Husk":
            yield_val *= 2.0

        w_a += yield_val
        w_b += yield_val

        if random.random() < 0.3:
            siphon = yield_val * 0.5
            w_a -= siphon
            w_b -= siphon

            cursor.execute("SELECT id, special_rule FROM factions WHERE special_rule IN ('Obsidian_Syndicate', 'Silk_Syndicate', 'Ghost_Flotilla', 'Sky_Baronies', 'Silent_Current', 'Black_Label', 'Spring_Ghosts', 'Crimson_Corsairs') ORDER BY RANDOM() LIMIT 1")
            syndicate = cursor.fetchone()
            if syndicate:
                cursor.execute("UPDATE factions SET treasury = treasury + ? WHERE id=?", (siphon * 2, syndicate[0]))

        sa_updates.append((w_a, sa_id))
        sa_updates.append((w_b, sb_id))

        fa_id = f_id
        cursor.execute("SELECT faction_id FROM settlements WHERE id=?", (sb_id,))
        fb_row = cursor.fetchone()
        if fb_row and fb_row[0] != fa_id:
            apply_trust_delta(fa_id, fb_row[0], 2, cursor)

    cursor.executemany("UPDATE settlements SET wealth=? WHERE id=?", sa_updates)

def process_paragons(cursor, conn, settlements, log_event_fn):
    cursor.execute("""
        SELECT p.id, p.name, p.descriptor, p.settlement_id,
               s.faction_id, s.name as s_name, s.wealth, s.security_points, p.goal
        FROM paragons p
        JOIN settlements s ON p.settlement_id = s.id
    """)
    paragons = cursor.fetchall()
    if not paragons:
        return

    cursor.execute("SELECT faction_a_id, faction_b_id, trust_level, status FROM faction_relations")
    all_relations = cursor.fetchall()
    relation_map = {}
    for fa, fb, trust, status in all_relations:
        relation_map.setdefault(fa, {})[fb] = (trust, status)

    faction_settlements = {}
    for s in settlements:
        faction_settlements.setdefault(s[1], []).append(s)

    for p in paragons:
        p_id, p_name, archetype, s_id, faction_id, s_name, s_wealth, s_sec, goal = p

        my_relations = relation_map.get(faction_id, {})
        if not my_relations:
            continue

        best_f = max(my_relations, key=lambda f: my_relations[f][0], default=None)
        worst_f = min(my_relations, key=lambda f: my_relations[f][0], default=None)
        if best_f is None:
            continue

        best_trust, best_status = my_relations[best_f]
        worst_trust, worst_status = my_relations.get(worst_f, (0, 'Neutral'))

        is_diplomat = (archetype in ['Diplomat', 'The Visionary', 'The Merciful', 'The Zealot'])
        is_warrior  = (archetype in ['Warrior', 'The Iron-Fisted', 'The Ruthless'])
        is_merchant = (archetype in ['Merchant', 'The Builder', 'The Glutton'])

        # Paragon motivation variations based on goals
        if not goal:
            goal = "Survive"

        if goal == "Conquer" and random.random() < 0.1:
            if worst_f and worst_status != 'War':
                cursor.execute("UPDATE faction_relations SET status='War', trust_level=-60 WHERE faction_a_id=? AND faction_b_id=?", (faction_id, worst_f))
                cursor.execute("UPDATE faction_relations SET status='War', trust_level=-60 WHERE faction_a_id=? AND faction_b_id=?", (worst_f, faction_id))
                log_event_fn("Paragon", f"{p_name} motivated by Conquer instigated a holy war between their faction and {worst_f}!", conn)
        elif goal == "Innovate" and random.random() < 0.1:
            cursor.execute("UPDATE factions SET technology_level = technology_level + 1 WHERE id=?", (faction_id,))
            log_event_fn("Paragon", f"{p_name} motivated by Innovate advanced their faction's technology level!", conn)

        if worst_status == 'War' and not is_diplomat:
            enemy_settlements = faction_settlements.get(worst_f, [])
            if enemy_settlements:
                target = random.choice(enemy_settlements)
                sec_dmg = 4 if is_warrior else 2
                cursor.execute(
                    "UPDATE settlements SET security_points = max(0, security_points - ?) WHERE id=?",
                    (sec_dmg, target[0])
                )
                cursor.execute(
                    "INSERT INTO crimes (settlement_id, type, severity) VALUES (?,?,?)",
                    (target[0], 'Raid', 3 if is_warrior else 2)
                )
                log_event_fn(
                    "Paragon",
                    f"{p_name} ({archetype}) of {s_name} raided {target[3]} (sec -{sec_dmg}).",
                    conn
                )
                apply_trust_delta(faction_id, worst_f, -5 if is_warrior else -2, cursor)

        elif best_status in ('Alliance', 'Trading'):
            ally_settlements = faction_settlements.get(best_f, [])
            if ally_settlements:
                target = random.choice(ally_settlements)
                trade_bonus = 30.0 if is_merchant else 15.0
                cursor.execute(
                    "UPDATE settlements SET wealth = wealth + ? WHERE id=?",
                    (trade_bonus, s_id)
                )
                cursor.execute(
                    "UPDATE settlements SET wealth = wealth + ? WHERE id=?",
                    (trade_bonus, target[0])
                )
                trust_bonus = 7 if is_diplomat else 4
                apply_trust_delta(faction_id, best_f, trust_bonus, cursor)
                log_event_fn(
                    "Paragon",
                    f"{p_name} ({archetype}) of {s_name} fostered trade with {target[3]} (+{trust_bonus} trust, +{trade_bonus} wealth each).",
                    conn
                )

        else:
            cursor.execute(
                "UPDATE settlements SET security_points = min(100, security_points + 1) WHERE id=?",
                (s_id,)
            )
