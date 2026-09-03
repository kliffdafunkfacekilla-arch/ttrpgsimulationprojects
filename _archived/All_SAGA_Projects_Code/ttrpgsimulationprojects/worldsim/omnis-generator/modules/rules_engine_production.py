# rules_engine_production.py
# Handles specialized production yields from faction structures.
# Called by process_living_world_tick in rules_engine.py.

import random

def process_structures_production(g, inventory, mines, barracks, discontent):
    """
    Calculates specialized production yields from a faction's structures.
    
    Args:
        g: dict - the faction/macro group state dict
        inventory: dict - current resource inventory
        mines: int - number of mine structures
        barracks: int - number of barracks structures
        discontent: float (0.0-1.0) - current discontent level
    
    Returns:
        dict of {resource_name: yield_amount} to be added to inventory
    """
    yields = {}

    # High discontent reduces worker efficiency
    efficiency_penalty = max(0.0, 1.0 - (discontent * 0.5))

    # --- Mine Production: Special Ores ---
    if mines > 0:
        # Chance to produce rare earth conductors (the 12 Aetheric elements)
        rare_elements = [
            "Lithium", "Tungsten", "Titanium", "Chromium",
            "Iridium", "Osmium", "Silicon", "Bismuth",
            "Gold", "Silver", "Lead", "Phosphorus", "Nickel"
        ]
        for element in rare_elements:
            # Each mine has a small chance to find traces
            if random.random() < 0.02 * mines:
                amount = round(random.uniform(0.5, 2.0) * efficiency_penalty, 2)
                yields[element] = yields.get(element, 0.0) + amount

        # Copper production from mines
        if random.random() < 0.3 * mines:
            yields["Copper Ore"] = yields.get("Copper Ore", 0.0) + round(mines * 2.0 * efficiency_penalty, 2)

    # --- Barracks Production: Military Supplies ---
    if barracks > 0:
        # Barracks produce Iron Tools from steel and leather
        if inventory.get("Smelted Steel", 0.0) >= barracks and inventory.get("Leather", 0.0) >= barracks:
            yields["Iron Tools"] = yields.get("Iron Tools", 0.0) + float(barracks)

        # Grounding Chains (anti-chaos equipment) if Smelted Steel available
        if inventory.get("Smelted Steel", 0.0) >= barracks * 2:
            if random.random() < 0.15:
                yields["Grounding Chains"] = yields.get("Grounding Chains", 0.0) + float(barracks)

        # Leather Armor from leather
        if inventory.get("Leather", 0.0) >= barracks * 2:
            yields["Leather Armor"] = yields.get("Leather Armor", 0.0) + float(barracks * 2)

    # --- Workshop-based specialized goods ---
    workshops = g.get("workshops_count", 0)
    if workshops > 0:
        # Aether-Wright PPE (Protective gear) from Crystal Chips + Leather
        if inventory.get("Crystal Chips", 0.0) >= 2 and inventory.get("Leather", 0.0) >= 2:
            if random.random() < 0.1 * workshops:
                yields["Aether-Wright PPE"] = yields.get("Aether-Wright PPE", 0.0) + 1.0

        # Jitter-Rig (chaos measurement device) from Crystal Chips + Copper Wire
        if inventory.get("Crystal Chips", 0.0) >= 3 and inventory.get("Copper Wire", 0.0) >= 1:
            if random.random() < 0.05 * workshops:
                yields["Jitter-Rig"] = yields.get("Jitter-Rig", 0.0) + 1.0

        # Silk-Steel Cables from Silk-Steel Thread
        if inventory.get("Silk-Steel Thread", 0.0) >= 3:
            craft_count = min(int(inventory["Silk-Steel Thread"] // 3), workshops * 2)
            if craft_count > 0:
                yields["Silk-Steel Cables"] = yields.get("Silk-Steel Cables", 0.0) + float(craft_count)

        # Rope from Leather
        if inventory.get("Leather", 0.0) >= 2:
            craft_count = min(int(inventory["Leather"] // 2), workshops * 3)
            if craft_count > 0:
                yields["Rope"] = yields.get("Rope", 0.0) + float(craft_count)

        # Copper Wire from Copper Ore
        if inventory.get("Copper Ore", 0.0) >= 2:
            craft_count = min(int(inventory["Copper Ore"] // 2), workshops * 5)
            if craft_count > 0:
                yields["Copper Wire"] = yields.get("Copper Wire", 0.0) + float(craft_count)

    return yields
