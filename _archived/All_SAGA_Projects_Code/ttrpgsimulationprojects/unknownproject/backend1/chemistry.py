import random
from sqlalchemy.orm.attributes import flag_modified

# =============================================================================
# Phase 10: Systemic Chemistry Engine (Tag-Based Interactions Matrix)
# =============================================================================

# The matrix defines how an active catalyst tag interacts with a passive target tag,
# producing a result tag on the target and triggering a procedural systemic effect.
TAG_MATRIX = {
    "IGNITE": {
        "reacts_with": "FLAMMABLE",
        "result_tag": "BURNED",
        "effect": "DESTROY_STOCKPILE"
    },
    "CORRUPT": {
        "reacts_with": "ORGANIC",
        "result_tag": "MUTATED",
        "effect": "SANITY_DAMAGE"
    },
    "FREEZE": {
        "reacts_with": "LIQUID",
        "result_tag": "FROZEN",
        "effect": "HALT_PRODUCTION"
    }
}

def get_default_tags(resource_name: str) -> list[str]:
    """
    Returns deterministic default passive tags for stockpiled resources
    to populate missing tags dynamically without database migration.
    """
    name_lower = resource_name.lower()
    if "timber" in name_lower or "wood" in name_lower:
        return ["FLAMMABLE", "STRUCTURAL"]
    elif "grain" in name_lower or "food" in name_lower:
        return ["FLAMMABLE", "ORGANIC", "CONSUMABLE"]
    elif "dragonstone" in name_lower:
        return ["AETHERIC", "VOLATILE"]
    elif "weapon" in name_lower:
        return ["STRUCTURAL", "KINETIC"]
    elif "steel" in name_lower or "iron" in name_lower:
        return ["STRUCTURAL", "LIQUID_VULNERABLE"]
    return ["FLAMMABLE"]

def get_stock(stockpiles: dict, resource_name: str) -> int:
    """
    Safely retrieves the integer amount of a stockpile, regardless of whether 
    it is stored as a raw integer or a structured dictionary with tags.
    """
    val = stockpiles.get(resource_name, 0)
    if isinstance(val, dict):
        return val.get("amount", 0)
    return val

def set_stock(stockpiles: dict, resource_name: str, amount: int, default_tags: list[str] = None) -> None:
    """
    Sets the value of a stockpile, automatically upgrading simple integers 
    to structured tag dictionaries in-place for backward-compatibility.
    """
    val = stockpiles.get(resource_name, 0)
    target_amount = max(0, int(amount))
    
    if isinstance(val, dict):
        val["amount"] = target_amount
        if default_tags and "tags" not in val:
            val["tags"] = default_tags
        stockpiles[resource_name] = val
    else:
        # Upgrade integer value to tag structure
        tags = default_tags or get_default_tags(resource_name)
        stockpiles[resource_name] = {
            "amount": target_amount,
            "tags": tags
        }

def upgrade_all_stockpiles(hex_record) -> None:
    """
    Loops through all keys in hex_record.stockpiles and ensures they are fully 
    represented in the dictionary structure supporting tags.
    """
    if not isinstance(hex_record.stockpiles, dict):
        hex_record.stockpiles = {}
    
    for k, v in list(hex_record.stockpiles.items()):
        if not isinstance(v, dict):
            set_stock(hex_record.stockpiles, k, v)

def resolve_interactions(active_tags: list[str], hex_record) -> None:
    """
    Scans the hex record's stockpiles, local_entities, and urban_meters.
    Checks for chemical reactions where active catalyst tags interact 
    with passive targets, applying structural and physical consequences.
    """
    if not active_tags:
        return

    # Ensure local_scars is initialized
    if not isinstance(hex_record.local_scars, dict):
        hex_record.local_scars = {}

    # 1. Resolve Stockpile Chemistry Interactions
    upgrade_all_stockpiles(hex_record)
    
    for resource_name, stock_dict in hex_record.stockpiles.items():
        if not isinstance(stock_dict, dict):
            continue
        
        tags = stock_dict.setdefault("tags", get_default_tags(resource_name))
        
        for catalyst in active_tags:
            reaction = TAG_MATRIX.get(catalyst)
            if not reaction:
                continue
            
            target_vulnerable = reaction["reacts_with"]
            result_tag = reaction["result_tag"]
            effect = reaction["effect"]
            
            if target_vulnerable in tags:
                # Target matches reaction vulnerability! Apply effect
                if effect == "DESTROY_STOCKPILE":
                    stock_dict["amount"] = 0
                    
                    # Log permanent environmental scar via Delta Override Pattern
                    hex_record.local_scars["terrain_damage"] = "burned"
                    hex_record.local_scars.setdefault("ruins", [])
                    
                    if resource_name == "grain" and "silo" not in hex_record.local_scars["ruins"]:
                        hex_record.local_scars["ruins"].append("silo")
                    elif resource_name == "timber" and "lumber_mill" not in hex_record.local_scars["ruins"]:
                        hex_record.local_scars["ruins"].append("lumber_mill")
                    elif resource_name == "steel" and "barracks" not in hex_record.local_scars["ruins"]:
                        hex_record.local_scars["ruins"].append("barracks")
                        
                elif effect == "HALT_PRODUCTION":
                    # Add HALTED tag to stockpile to suspend economic growth
                    if "HALTED" not in tags:
                        tags.append("HALTED")
                
                # Append result tag to target tags list
                if result_tag not in tags:
                    tags.append(result_tag)

    # 2. Resolve Entity Chemistry Interactions (Level 1)
    if isinstance(hex_record.local_entities, list):
        for ent in hex_record.local_entities:
            if not isinstance(ent, dict):
                continue
            
            # Entities get passive ORGANIC and SENTIENT tags
            tags = ent.setdefault("tags", ["ORGANIC", "SENTIENT"])
            metabolic = ent.setdefault("metabolic_state", {"hunger_level": 0, "sanity_score": 1.0, "health": 100})
            
            for catalyst in active_tags:
                reaction = TAG_MATRIX.get(catalyst)
                if not reaction:
                    continue
                
                target_vulnerable = reaction["reacts_with"]
                result_tag = reaction["result_tag"]
                effect = reaction["effect"]
                
                if target_vulnerable in tags:
                    if effect == "SANITY_DAMAGE":
                        # Inflict 0.30 sanity depletion due to corruption
                        current_sanity = metabolic.get("sanity_score", 1.0)
                        metabolic["sanity_score"] = round(max(0.0, min(1.0, current_sanity - 0.30)), 2)
                    elif effect == "DESTROY_STOCKPILE":
                        # If ignite catalyst hits organic sentients, deal health damage!
                        current_health = metabolic.get("health", 100)
                        metabolic["health"] = max(0, current_health - 30)
                    
                    if result_tag not in tags:
                        tags.append(result_tag)

    # 3. Resolve Urban Meters Chemistry Interactions (Level 2)
    if isinstance(hex_record.urban_meters, dict):
        # Map logical default tags for simple float urban meters
        # happy_meter is LIQUID (flowing state of community happiness)
        # crime_rating is VOLATILE (unstable and reactive)
        # spiritual_alignment is ORGANIC (faith and internal belief)
        
        for catalyst in active_tags:
            reaction = TAG_MATRIX.get(catalyst)
            if not reaction:
                continue
            
            target_vulnerable = reaction["reacts_with"]
            
            if target_vulnerable == "LIQUID":
                # FREEZE freezes happy meter (halves or lowers)
                if "happy_meter" in hex_record.urban_meters:
                    curr = hex_record.urban_meters["happy_meter"]
                    hex_record.urban_meters["happy_meter"] = round(max(0.0, curr - 0.20), 2)
                    
            elif target_vulnerable == "ORGANIC":
                # CORRUPT degrades local community spirit
                if "spiritual_alignment" in hex_record.urban_meters:
                    curr = hex_record.urban_meters["spiritual_alignment"]
                    hex_record.urban_meters["spiritual_alignment"] = round(max(0.0, curr - 0.25), 2)
                if "happy_meter" in hex_record.urban_meters:
                    curr = hex_record.urban_meters["happy_meter"]
                    hex_record.urban_meters["happy_meter"] = round(max(0.0, curr - 0.15), 2)
                if "crime_rating" in hex_record.urban_meters:
                    curr = hex_record.urban_meters["crime_rating"]
                    hex_record.urban_meters["crime_rating"] = round(min(1.0, curr + 0.10), 2)
