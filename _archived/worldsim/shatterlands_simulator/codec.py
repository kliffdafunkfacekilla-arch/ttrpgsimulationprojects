# codec.py
# Bit-packing and unpacking code for Shatterlands Simulator

# Biome Mappings
BIOMES = {
    0: "Ocean/Water",
    1: "Gravity Spires (Nexus)",
    2: "Unyielding Foundation (Mass)",
    3: "Kinetic Plains (Motus)",
    4: "Shifting Mistlands (Flux)",
    5: "Healing Cradle (Vita)",
    6: "Eternal Sanctuary (Lex)",
    7: "Silver-Leaf Archives (Ratio)",
    8: "Orchards of Sacred Geometry (Ordo)",
    9: "Prism Heights (Lux)",
    10: "Premonition Willows (Omen)",
    11: "Gilded Vales (Aura)",
    12: "Echoing Steppes (Anumis)",
}
BIOME_REV = {v: k for k, v in BIOMES.items()}

# Faction Mappings
FACTIONS = {
    0: "None/Neutral",
    1: "Canopy Clans",
    2: "Vaneer Concord",
    3: "Ursine Hegemony",
    4: "Heartland Alliance",
    5: "Iron Caldera",
    6: "Coastal Theocracy",
    7: "Meridian Chain",
    8: "Scute Confederacy",
    9: "Prism-Scale Collective",
    10: "Dust-Husk Riders",
    11: "Eastern Hounds",
    12: "Guerrilla Clans",
    13: "River Folk",
    14: "Sump-Kin",
    15: "Flower Valley Folk",
}
FACTION_REV = {v: k for k, v in FACTIONS.items()}

# Resource/Metal Mappings (Ouroboros Loop and core materials)
RESOURCES = {
    0: "None",
    1: "Chromium (Lux Conductor)",
    2: "Titanium (Ordo Conductor)",
    3: "Lithium (Lex Conductor)",
    4: "Gold (Flux Conductor)",
    5: "Silicon (Ratio Conductor)",
    6: "Tungsten (Nexus Conductor)",
    7: "Bismuth (Anumis Conductor)",
    8: "Osmium (Mass Conductor)",
    9: "Iridium (Omen Conductor)",
    10: "Silver (Vita Conductor)",
    11: "Phosphorus (Aura Conductor)",
    12: "Lead (Motus Conductor)",
    13: "Iron",
    14: "Timber",
    15: "Food",
}
RESOURCE_REV = {v: k for k, v in RESOURCES.items()}

# Active Overlay Mappings (Chaos Storms & Weather)
OVERLAYS = {
    0: "Clear/None",
    1: "Transmutation Mist (Aurgenas)",
    2: "Gravity Well (Tiraton)",
    3: "Psychic Lightning (Tyrustis)",
    4: "Spirit Fire (Virantor)",
    5: "Clockwork Rot (Opecten)",
    6: "Temporal Rift (Termhill)",
    7: "Aetheric Tension",
    8: "Heavy Rain",
    9: "Freezing Snow",
    10: "Volcanic Heatwave",
}
OVERLAY_REV = {v: k for k, v in OVERLAYS.items()}

def pack_micro_hex(biome: int, faction: int, resource: int, dev_level: int, overlay: int, spark: int) -> int:
    """Pack micro-hex data attributes into a 32-bit integer."""
    packed = 0
    packed |= (biome & 0xF)          # bits 0-3
    packed |= (faction & 0xF) << 4    # bits 4-7
    packed |= (resource & 0xF) << 8   # bits 8-11
    packed |= (dev_level & 0x7) << 12 # bits 12-14
    packed |= (overlay & 0xF) << 15   # bits 15-18
    packed |= (spark & 0x1) << 19     # bit 19
    return packed

def unpack_micro_hex(state_int: int) -> dict:
    """Unpack a 32-bit integer into its micro-hex attributes."""
    biome_id = state_int & 0xF
    faction_id = (state_int >> 4) & 0xF
    resource_id = (state_int >> 8) & 0xF
    dev_level = (state_int >> 12) & 0x7
    overlay_id = (state_int >> 15) & 0xF
    spark = (state_int >> 19) & 0x1

    return {
        "biome_id": biome_id,
        "biome": BIOMES.get(biome_id, "Unknown"),
        "faction_id": faction_id,
        "faction": FACTIONS.get(faction_id, "Unknown"),
        "resource_id": resource_id,
        "resource": RESOURCES.get(resource_id, "Unknown"),
        "dev_level": dev_level,
        "overlay_id": overlay_id,
        "overlay": OVERLAYS.get(overlay_id, "Unknown"),
        "spark": bool(spark)
    }
