# scheduler.py
import os
import sys
import random

# Ensure stdout handles Unicode emojis cleanly on Windows PowerShell
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Ensure modules directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

from sqlalchemy import create_engine
from calendar_manager import CalendarManager
from magistar_plugin import calculate_reality_spike
from weather_system import calculate_weather
from rules_engine import (
    get_town_details, calculate_tech_level, 
    get_unlocked_transport, get_unlocked_buildings,
    process_well_being_tick, process_living_world_tick
)

engine = create_engine('postgresql://user:password@localhost:5432/ostraka_world')

# Global Prison state for background scheduler
SCHEDULER_PRISONS = {
    "Tiraton": 1.0,
    "Stagus": 1.0,
    "Metrion": 1.0,
    "Aurgenas": 1.0,
    "Vecelo": 1.0,
    "Lophex": 1.0,
    "Tyrustis": 1.0,
    "Opecten": 1.0,
    "Carulkem": 1.0,
    "Termhill": 1.0,
    "Virantor": 1.0,
    "Gavusrix": 1.0,
    "warden_population": 1500.0,
    "warden_recruits_accumulated": 0.0
}

# Dummy functions to make it runnable and testable
def get_day_from_db():
    return 150

class DummyMacroGroup:
    def __init__(self, group_id, name, populations, stats, buildings_count, magistar_id="Tiraton", distance_to_chaos=0.5, distance_to_conv=0.6):
        self.id = group_id
        self.name = name
        self.settlement_populations = populations
        self.population = sum(populations)
        self.chaos_level = 0.5
        self.pressure = 0.5
        self.magistar_id = magistar_id
        self.is_active = True
        self.geom = "dummy_geom"
        self.distance_to_chaos_structure = distance_to_chaos
        self.distance_to_convergence = distance_to_conv
        
        # Initial well-being stats
        self.physical_well_being = stats.get("physical", 0.8)
        self.mental_well_being = stats.get("mental", 0.8)
        self.crime_level = stats.get("crime", 0.2)
        self.discontent = stats.get("discontent", 0.1)
        
        # Active building configurations
        self.camps_count = buildings_count.get("camps", 0)
        self.mines_count = buildings_count.get("mines", 0)
        self.docks_count = buildings_count.get("docks", 0)
        self.farms_count = buildings_count.get("farms", 0)
        self.watchtowers_count = buildings_count.get("watchtowers", 0)
        self.walls_count = buildings_count.get("walls", 0)
        self.barracks_count = buildings_count.get("barracks", 0)

        # Infiltration level & Cult population
        self.cult_infiltration = 0.05
        self.cult_population = self.population * self.cult_infiltration
        self.cult_devoted = self.cult_population * 0.20

        # Ecology values
        self.flora_ghost_flower = 100.0
        self.flora_stone_root = 100.0
        self.fauna_sky_grazer = 50.0
        self.fauna_timber_wolf = 10.0

        # Domestic facilities
        self.domestic_greenhouses = 0
        self.domestic_orchards = 0
        self.domestic_pens = 0
        self.domestic_kennels = 0

        # Happiness & Syndicate/Illicit structures
        self.churches_count = 0
        self.theatres_count = 0
        self.arenas_count = 0
        self.gambling_dens_count = 0
        self.black_markets_count = 0

        # Leader / Paragon
        self.paragon = None

        # Initialize inventory
        self.inventory = {
            "Lumber": 50.0,
            "Stone": 50.0,
            "Iron Ore": 10.0,
            "Copper Ore": 5.0,
            "Coal": 10.0,
            "Grain": 30.0,
            "Leather": 10.0,
            "Dragonstone": 2.0,
            "Voltaic Fleece": 0.0,
            "Ozone-Milk": 0.0,
            "Ghost Flower": 0.0,
            "Night-Nectar": 0.0,
            "Flour": 0.0,
            "Peak-Cheese": 0.0,
            "Smelted Steel": 0.0,
            "Copper Wire": 0.0,
            "Refined Aether Battery": 0.0,
            "Tanned Strips": 0.0,
            "Ostrakan Hardtack": 5.0,
            "Caldera Spark-Bread": 0.0,
            "Basic Weapons": 0.0,
            "Aether-Wright PPE": 0.0,
            "Silk-Steel Cables": 0.0,
            "Leather Armor": 0.0,
            "Rope": 0.0
        }

def get_all_macro_groups():
    # Only the 17 Primary Factions with varying distances to chaos structures & convergence
    return [
        DummyMacroGroup(1, "Ursine Hegemony", [4000, 900, 100], {"physical": 0.85, "mental": 0.80, "crime": 0.10, "discontent": 0.05}, {"camps": 2, "mines": 1, "docks": 1, "farms": 2, "watchtowers": 3, "walls": 2, "barracks": 2}, "Stagus", distance_to_chaos=0.7, distance_to_conv=0.8),
        DummyMacroGroup(2, "River Folk", [6000, 1500, 500], {"physical": 0.80, "mental": 0.85, "crime": 0.15, "discontent": 0.10}, {"camps": 1, "mines": 1, "docks": 3, "farms": 3, "watchtowers": 1, "walls": 0, "barracks": 1}, "Tiraton", distance_to_chaos=0.2, distance_to_conv=0.5),
        DummyMacroGroup(3, "Sump-Kin", [5000, 1000, 200], {"physical": 0.55, "mental": 0.50, "crime": 0.40, "discontent": 0.30}, {"camps": 2, "mines": 3, "docks": 2, "farms": 0, "watchtowers": 1, "walls": 0, "barracks": 2}, "Gavusrix", distance_to_chaos=0.1, distance_to_conv=0.3),
        DummyMacroGroup(4, "Iron Caladrea", [7000, 1500, 500], {"physical": 0.75, "mental": 0.70, "crime": 0.20, "discontent": 0.15}, {"camps": 1, "mines": 4, "docks": 0, "farms": 1, "watchtowers": 2, "walls": 3, "barracks": 3}, "Aurgenas", distance_to_chaos=0.4, distance_to_conv=0.6),
        DummyMacroGroup(5, "Vaneer Concord", [9000, 500, 300], {"physical": 0.88, "mental": 0.75, "crime": 0.12, "discontent": 0.10}, {"camps": 2, "mines": 4, "docks": 1, "farms": 3, "watchtowers": 2, "walls": 3, "barracks": 4}, "Lophex", distance_to_chaos=0.6, distance_to_conv=0.6),
        DummyMacroGroup(6, "Hive Collective", [12000, 2000, 1000], {"physical": 0.90, "mental": 0.90, "crime": 0.05, "discontent": 0.05}, {"camps": 3, "mines": 2, "docks": 0, "farms": 6, "watchtowers": 2, "walls": 4, "barracks": 3}, "Tyrustis", distance_to_chaos=0.8, distance_to_conv=0.6),
        DummyMacroGroup(7, "Avians", [8000, 400, 100], {"physical": 0.92, "mental": 0.85, "crime": 0.08, "discontent": 0.08}, {"camps": 1, "mines": 1, "docks": 2, "farms": 2, "watchtowers": 4, "walls": 1, "barracks": 2}, "Opecten", distance_to_chaos=0.3, distance_to_conv=0.5),
        DummyMacroGroup(8, "Flower Valwey", [3000, 1000, 500], {"physical": 0.85, "mental": 0.88, "crime": 0.10, "discontent": 0.05}, {"camps": 2, "mines": 1, "docks": 1, "farms": 4, "watchtowers": 1, "walls": 1, "barracks": 1}, "Vecelo", distance_to_chaos=0.9, distance_to_conv=0.9),
        DummyMacroGroup(9, "Sylvian", [6000, 1000, 200], {"physical": 0.82, "mental": 0.80, "crime": 0.15, "discontent": 0.10}, {"camps": 3, "mines": 1, "docks": 0, "farms": 4, "watchtowers": 2, "walls": 1, "barracks": 2}, "Termhill", distance_to_chaos=0.5, distance_to_conv=0.7),
        DummyMacroGroup(10, "Sciute", [4000, 1000, 500], {"physical": 0.80, "mental": 0.78, "crime": 0.12, "discontent": 0.08}, {"camps": 1, "mines": 2, "docks": 1, "farms": 2, "watchtowers": 2, "walls": 3, "barracks": 1}, "Carulkem", distance_to_chaos=0.5, distance_to_conv=0.7),
        DummyMacroGroup(11, "Meridian Chain", [8000, 500], {"physical": 0.88, "mental": 0.82, "crime": 0.18, "discontent": 0.12}, {"camps": 2, "mines": 1, "docks": 4, "farms": 1, "watchtowers": 1, "walls": 1, "barracks": 3}, "Virantor", distance_to_chaos=0.3, distance_to_conv=0.6),
        DummyMacroGroup(12, "Prism Lizards", [5000, 1500, 300], {"physical": 0.84, "mental": 0.80, "crime": 0.16, "discontent": 0.14}, {"camps": 1, "mines": 2, "docks": 1, "farms": 1, "watchtowers": 2, "walls": 2, "barracks": 2}, "Metrion", distance_to_chaos=0.2, distance_to_conv=0.5),
        DummyMacroGroup(13, "Canopy Clans", [3000, 400], {"physical": 0.70, "mental": 0.65, "crime": 0.35, "discontent": 0.25}, {"camps": 5, "mines": 1, "docks": 0, "farms": 2, "watchtowers": 2, "walls": 0, "barracks": 1}, "Metrion", distance_to_chaos=0.2, distance_to_conv=0.5),
        DummyMacroGroup(14, "East Hounds", [3000, 1000, 200], {"physical": 0.65, "mental": 0.70, "crime": 0.28, "discontent": 0.20}, {"camps": 3, "mines": 0, "docks": 0, "farms": 2, "watchtowers": 2, "walls": 0, "barracks": 2}, "Termhill", distance_to_chaos=0.5, distance_to_conv=0.7),
        DummyMacroGroup(15, "Guirrilla Clans", [1500, 800, 200], {"physical": 0.58, "mental": 0.62, "crime": 0.38, "discontent": 0.28}, {"camps": 4, "mines": 1, "docks": 0, "farms": 1, "watchtowers": 1, "walls": 0, "barracks": 1}, "Tiraton", distance_to_chaos=0.1, distance_to_conv=0.4),
        DummyMacroGroup(16, "Theocracy", [6000, 1500, 300], {"physical": 0.72, "mental": 0.68, "crime": 0.22, "discontent": 0.18}, {"camps": 1, "mines": 1, "docks": 3, "farms": 2, "watchtowers": 2, "walls": 1, "barracks": 2}, "Virantor", distance_to_chaos=0.3, distance_to_conv=0.6),
        DummyMacroGroup(17, "The Reliance", [3000], {"physical": 0.95, "mental": 0.90, "crime": 0.05, "discontent": 0.02}, {"camps": 1, "mines": 2, "docks": 0, "farms": 1, "watchtowers": 1, "walls": 1, "barracks": 1}, "Gavusrix", distance_to_chaos=0.9, distance_to_conv=0.4)
    ]

def get_all_fringe_groups():
    return [
        "Obsidian Cartel and Sister Org",
        "Freesky Barons",
        "Ghost Wind Raiders",
        "Gilded Compass",
        "Crimson Coursairs",
        "Silent Current",
        "The Black Label",
        "The Otter Syndicate",
        "The Spring Ghosts"
    ]

def calculate_torque(geom):
    return 10.0

def update_group_state(group_id, name, population, weather, tech_level, transports, buildings, stats_results):
    print(f"Updated group {group_id} ({name}): population={population:.2f}, weather={weather}")
    print(f"  Calculated Tech Level: {tech_level}")
    print(f"  Active Interaction Tags: {', '.join(stats_results.get('active_tags', []))}")
    print(f"  Unlocked Transports: {', '.join(transports)}")
    print(f"  Unlocked Buildings: {', '.join(buildings)}")
    print(f"  --- Social Stats & Threat ---")
    print(f"    Food Supply Rating: {stats_results['food_supply']:.2f}")
    print(f"    Safety Rating: {stats_results['safety_rating']:.2f}")
    print(f"    Security Rating: {stats_results['security_rating']:.2f}")
    print(f"    Physical Well-Being: {stats_results['physical_well_being']:.2f}")
    print(f"    Mental Well-Being: {stats_results['mental_well_being']:.2f}")
    print(f"    Discontent: {stats_results['discontent']:.2f}")
    print(f"    Crime Level: {stats_results['crime_level']:.2f}")
    print(f"    Warden Chaos Patrols: {stats_results.get('allocated_patrols', 0.0):.0f} Sentinels | Hunters: {stats_results.get('allocated_hunters', 0.0):.0f} Rangers")
    print(f"    Cult: Infiltration={stats_results.get('cult_infiltration', 0.05)*100:.1f}% | Devoted Priests={stats_results.get('cult_devoted', 0.0):.0f} | Network={stats_results.get('cult_population', 0.0) - stats_results.get('cult_devoted', 0.0):.0f}")
    print(f"    Demographics: Nulls={stats_results.get('null_population', population * 0.5):.0f} | Sparkborn={stats_results.get('sparkborn_population', population * 0.5):.0f} (Sens={stats_results.get('sparkborn_sensitive', 0.0):.0f}, Attu={stats_results.get('sparkborn_attuned', 0.0):.0f}, Adep={stats_results.get('sparkborn_adept', 0.0):.0f}, Wiel={stats_results.get('sparkborn_wielder', 0.0):.0f}, Mast={stats_results.get('sparkborn_master', 0.0):.0f}, Epic={stats_results.get('sparkborn_epic', 0.0):.0f})")
    print(f"    Happiness Buildings: Churches={stats_results.get('churches_count', 0)} | Theatres={stats_results.get('theatres_count', 0)} | Arenas={stats_results.get('arenas_count', 0)}")
    print(f"    Syndicate Structures: Gambling Dens={stats_results.get('gambling_dens_count', 0)} | Black Markets={stats_results.get('black_markets_count', 0)}")
    
    p = stats_results.get("paragon")
    if p:
        print(f"    👑 Paragon Leader: {p['name']} ({p['role']}) | Culture={p['culture']} | Alignment={p.get('alignment', 'Pragmatic')} | Magic={p.get('magic_affinity', 'Null')}")
        print(f"      Traits: {', '.join(p['traits'])}")
        print(f"      Stats: Might={p['stats']['Might']} Endur={p['stats']['Endurance']} Reflex={p['stats']['Reflex']} Vital={p['stats']['Vitality']} Fort={p['stats']['Fortitude']}")
        print(f"             Knowl={p['stats']['Knowledge']} Logic={p['stats']['Logic']} Aware={p['stats']['Awareness']} Intu={p['stats']['Intuition']} Charm={p['stats']['Charm']} Will={p['stats']['Willpower']}")
        if p.get("recent_decisions"):
            print(f"      Recent Decision: {p['recent_decisions'][-1]}")
            
    print(f"    State / Active Events: {stats_results['event']}")
    print(f"    Trader Status: {stats_results['trader_status']}")
    print(f"  --- Ecology & Wildlife ---")
    print(f"    Ghost Flower Flora: {stats_results.get('flora_ghost_flower', 0.0):.1f} | Stone-Root Flora: {stats_results.get('flora_stone_root', 0.0):.1f}")
    print(f"    Sky-Grazer Fauna: {stats_results.get('fauna_sky_grazer', 0.0):.1f} | Timber Wolf Fauna: {stats_results.get('fauna_timber_wolf', 0.0):.1f}")
    print(f"    Domestication: Greenhouses={stats_results.get('domestic_greenhouses', 0)} | Orchards={stats_results.get('domestic_orchards', 0)} | Pens={stats_results.get('domestic_pens', 0)} | Kennels (Wolves Trained)={stats_results.get('domestic_kennels', 0)}")

def log_saga_event(title, description):
    print(f"Saga Event [{title}]: {description}")

def run_simulation_tick(delta_time_hours):
    """ The Master Loop """
    global SCHEDULER_PRISONS
    cal = CalendarManager()
    current_day = get_day_from_db()
    groups = get_all_macro_groups()

    # 1. Physics & Chaos Processing
    for group in groups:
        season_mod = cal.apply_seasonal_modifier("Forest", current_day)
        reality_mod = calculate_reality_spike(group.magistar_id, group.is_active)
        weather = calculate_weather(group.chaos_level, group.pressure, group.magistar_id)

        torque = calculate_torque(group.geom)

        # Prepare dictionary for process_living_world_tick
        g_dict = {
            "name": group.name,
            "population": group.population,
            "chaos_level": group.chaos_level,
            "pressure": group.pressure,
            "magistar_id": group.magistar_id,
            "is_active": group.is_active,
            "physical_well_being": group.physical_well_being,
            "mental_well_being": group.mental_well_being,
            "crime_level": group.crime_level,
            "discontent": group.discontent,
            "camps_count": group.camps_count,
            "mines_count": group.mines_count,
            "docks_count": group.docks_count,
            "farms_count": group.farms_count,
            "watchtowers_count": group.watchtowers_count,
            "walls_count": group.walls_count,
            "barracks_count": group.barracks_count,
            "cult_infiltration": group.cult_infiltration,
            "cult_population": group.cult_population,
            "cult_devoted": group.cult_devoted,
            "distance_to_chaos_structure": group.distance_to_chaos_structure,
            "distance_to_convergence": group.distance_to_convergence,
            "flora_ghost_flower": group.flora_ghost_flower,
            "flora_stone_root": group.flora_stone_root,
            "fauna_sky_grazer": group.fauna_sky_grazer,
            "fauna_timber_wolf": group.fauna_timber_wolf,
            "domestic_greenhouses": group.domestic_greenhouses,
            "domestic_orchards": group.domestic_orchards,
            "domestic_pens": group.domestic_pens,
            "domestic_kennels": group.domestic_kennels,
            "churches_count": group.churches_count,
            "theatres_count": group.theatres_count,
            "arenas_count": group.arenas_count,
            "gambling_dens_count": group.gambling_dens_count,
            "black_markets_count": group.black_markets_count,
            "paragon": group.paragon
        }

        tick_result = process_living_world_tick(
            g_dict, 
            group.inventory, 
            current_day, 
            season_mod, 
            reality_mod, 
            weather, # pass full weather dictionary
            prisons=SCHEDULER_PRISONS
        )

        # Update the DummyMacroGroup object
        group.population = tick_result["population"]
        group.physical_well_being = tick_result["physical_well_being"]
        group.mental_well_being = tick_result["mental_well_being"]
        group.crime_level = tick_result["crime_level"]
        group.discontent = tick_result["discontent"]
        group.inventory = tick_result["inventory"]
        group.cult_infiltration = tick_result["cult_infiltration"]
        group.cult_population = tick_result["cult_population"]
        group.cult_devoted = tick_result["cult_devoted"]
        group.farms_count = g_dict["farms_count"]
        group.watchtowers_count = g_dict["watchtowers_count"]
        group.barracks_count = g_dict["barracks_count"]
        group.mines_count = g_dict["mines_count"]
        group.walls_count = g_dict["walls_count"]
        group.camps_count = g_dict["camps_count"]
        group.docks_count = g_dict["docks_count"]
        group.churches_count = tick_result["churches_count"]
        group.theatres_count = tick_result["theatres_count"]
        group.arenas_count = tick_result["arenas_count"]
        group.gambling_dens_count = tick_result["gambling_dens_count"]
        group.black_markets_count = tick_result["black_markets_count"]
        
        # Leader / Paragon update back
        group.paragon = tick_result.get("paragon")
        
        # Update ecology variables back
        group.flora_ghost_flower = tick_result["flora_ghost_flower"]
        group.flora_stone_root = tick_result["flora_stone_root"]
        group.fauna_sky_grazer = tick_result["fauna_sky_grazer"]
        group.fauna_timber_wolf = tick_result["fauna_timber_wolf"]

        # Update domestic facilities back
        group.domestic_greenhouses = tick_result["domestic_greenhouses"]
        group.domestic_orchards = tick_result["domestic_orchards"]
        group.domestic_pens = tick_result["domestic_pens"]
        group.domestic_kennels = tick_result["domestic_kennels"]
        
        SCHEDULER_PRISONS = tick_result["prisons"]

        if weather.get("is_chaos_charged"):
            log_saga_event("⚡ CHAOS CHARGE", f"A storm cell became charged with chaos in {group.name}, converging on {weather.get('destination_prison')} Prison!")

        # Handle Secret Cult Network spread to adjacent factions
        if tick_result.get("spread_target"):
            target_name, amount = tick_result["spread_target"]
            for target_g in groups:
                if target_g.name == target_name:
                    target_g.cult_population = min(target_g.population, target_g.cult_population + amount)
                    target_g.cult_infiltration = target_g.cult_population / max(1.0, target_g.population)
                    log_saga_event("🕸️ CULT SPREAD", f"Secret cult network branched from {group.name} into {target_name}, seeding {amount} cultists.")

        # Scale individual settlement populations
        scale_ratio = group.population / max(1.0, sum(group.settlement_populations))
        group.settlement_populations = [pop * scale_ratio for pop in group.settlement_populations]

        tech_level = calculate_tech_level(group.settlement_populations)
        unlocked_transports = get_unlocked_transport(tech_level)
        unlocked_buildings = get_unlocked_buildings(tech_level)

        # 3. Update Database / Log
        update_group_state(
            group.id, 
            name=group.name,
            population=group.population, 
            weather=weather['type'],
            tech_level=tech_level,
            transports=unlocked_transports,
            buildings=unlocked_buildings,
            stats_results=tick_result
        )

        for log_msg in tick_result["logs"]:
            log_saga_event("SAGA DETAIL", f"{group.name}: {log_msg}")

    # Simulate Fringe Group Operations
    fringe_names = get_all_fringe_groups()
    for fg_name in fringe_names:
        host = random.choice(groups)
        if fg_name == "Obsidian Cartel and Sister Org":
            host.crime_level = min(1.0, host.crime_level + 0.02)
            host.inventory["Lumber"] = max(0.0, host.inventory["Lumber"] - 3.0)
            host.inventory["Smelted Steel"] = host.inventory.get("Smelted Steel", 0.0) + 1.0
            log_saga_event("UNDERWORLD", f"Obsidian Cartel smuggled in {host.name}: traded Lumber for Smelted Steel, crime rising.")
        elif fg_name == "Freesky Barons":
            host.inventory["Dragonstone"] = host.inventory.get("Dragonstone", 0.0) + 1.0
            log_saga_event("SKY-TRADE", f"Freesky Barons sold 1 Dragonstone crystal to {host.name}.")
        elif fg_name == "Gilded Compass":
            host.discontent = max(0.0, host.discontent - 0.03)
            host.inventory["Stone"] = max(0.0, host.inventory["Stone"] - 4.0)
            log_saga_event("BANKING", f"Gilded Compass audited {host.name}'s ledgers, stabilizing discontent.")

    # Global Convergence void drain of shattered moon leakage
    avg_seal = sum(SCHEDULER_PRISONS[name] for name in [
        "Tiraton", "Stagus", "Metrion", "Aurgenas", "Vecelo", "Lophex", 
        "Tyrustis", "Opecten", "Carulkem", "Termhill", "Virantor", "Gavusrix"
    ]) / 12.0
    if avg_seal < 0.75:
        for group in groups:
            proximity_mult = 1.0 - group.distance_to_chaos_structure
            group.chaos_level = min(1.0, group.chaos_level + 0.04 * proximity_mult)
            group.pressure = min(1.0, group.pressure + 0.04 * proximity_mult)
        log_saga_event("CONVERGENCE SURGE", f"Convergence average prison seal integrity at {avg_seal * 100:.0f}%. Chaos surging globally!")
    else:
        log_saga_event("CONVERGENCE", f"Void drain draining shattered moon leakage efficiently at {avg_seal * 100:.0f}% capacity.")

    # Warden natural selection decay & recruitment step
    warden_recruits = SCHEDULER_PRISONS.get("warden_recruits_accumulated", 0.0)
    warden_decay = SCHEDULER_PRISONS.get("warden_population", 1500.0) * 0.08
    SCHEDULER_PRISONS["warden_population"] = max(0.0, SCHEDULER_PRISONS.get("warden_population", 1500.0) - warden_decay + warden_recruits)
    # Reset accumulator
    SCHEDULER_PRISONS["warden_recruits_accumulated"] = 0.0
    
    log_saga_event("WARDEN TELEMETRY", f"🛡️ Grey Warden Population: {SCHEDULER_PRISONS['warden_population']:.2f} (-{warden_decay:.2f} decay, +{warden_recruits:.2f} recruits)")

    # 4. Finalize
    log_saga_event("Tick Complete", f"World rotated and pressure adjusted for day {current_day}")

def debug_test_run():
    run_simulation_tick(1)

if __name__ == "__main__":
    debug_test_run()
