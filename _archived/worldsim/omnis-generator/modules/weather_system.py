# weather_system.py
import random
import json
import os

# Resolve project root (two levels up from this module file)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load_settings():
    """
    Load winds_and_temps settings from JSON files.
    Priority: world_settings.json > default_settings.json > hardcoded defaults.
    """
    # Try world_settings.json first (user-customized)
    world_path = os.path.join(_PROJECT_ROOT, 'world_settings.json')
    if os.path.isfile(world_path):
        try:
            with open(world_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'winds_and_temps' in data:
                return data['winds_and_temps']
        except (json.JSONDecodeError, IOError):
            pass

    # Fall back to default_settings.json
    default_path = os.path.join(_PROJECT_ROOT, 'default_settings.json')
    if os.path.isfile(default_path):
        try:
            with open(default_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'winds_and_temps' in data:
                return data['winds_and_temps']
        except (json.JSONDecodeError, IOError):
            pass

    # Final fallback: hardcoded defaults
    return {
        "precipitation_multiplier": 1.0,
        "zones": [
            {"name": "Polar North", "y_min": 0.0, "y_max": 14.3, "wind_dir": "NE", "wind_speed": 0.6, "temp_min": -30.0, "temp_max": -5.0},
            {"name": "Subpolar North", "y_min": 14.3, "y_max": 28.6, "wind_dir": "W", "wind_speed": 0.7, "temp_min": -10.0, "temp_max": 12.0},
            {"name": "Temperate North", "y_min": 28.6, "y_max": 42.9, "wind_dir": "SW", "wind_speed": 0.4, "temp_min": 5.0, "temp_max": 25.0},
            {"name": "Tropical / Equator", "y_min": 42.9, "y_max": 57.1, "wind_dir": "E", "wind_speed": 0.5, "temp_min": 20.0, "temp_max": 40.0},
            {"name": "Temperate South", "y_min": 57.1, "y_max": 71.4, "wind_dir": "NW", "wind_speed": 0.4, "temp_min": 5.0, "temp_max": 25.0},
            {"name": "Subpolar South", "y_min": 71.4, "y_max": 85.7, "wind_dir": "W", "wind_speed": 0.7, "temp_min": -10.0, "temp_max": 12.0},
            {"name": "Polar South", "y_min": 85.7, "y_max": 100.0, "wind_dir": "SE", "wind_speed": 0.6, "temp_min": -35.0, "temp_max": -10.0}
        ],
        "chaos_nodes": [],
        "convergence_locations": []
    }


def get_zone_for_cell(cell_y, settings=None):
    """
    Given a cell's y-coordinate (0-100 scale), return the matching wind zone dict
    from the loaded zones list. Returns the closest zone if no exact match.
    """
    if settings is None:
        settings = load_settings()

    zones = settings.get('zones', [])
    if not zones:
        return None

    for zone in zones:
        if zone['y_min'] <= cell_y <= zone['y_max']:
            return zone

    # If no exact match found, return the closest zone by midpoint distance
    best_zone = zones[0]
    best_dist = abs(cell_y - (zones[0]['y_min'] + zones[0]['y_max']) / 2.0)
    for zone in zones[1:]:
        mid = (zone['y_min'] + zone['y_max']) / 2.0
        dist = abs(cell_y - mid)
        if dist < best_dist:
            best_dist = dist
            best_zone = zone
    return best_zone


def calculate_weather(chaos_level, tensegrity_pressure, magistar_id=None, is_oceanic=False, cell_y=None, settings=None):
    """
    Models the aetheric weather based on local Chaos and Pressure.
    Returns weather details with modifiers:
      - type: String name
      - travel_cost: float multiplier
      - growth_mult: float multiplier for plant growth
      - degradation_rate: float risk/amount of building degradation
      - description: text explanation of the weather.
      - is_chaos_charged: boolean flag
      - destination_prison: target prison name if charged
      - wind_dir: wind direction from zone (if zone data available)
      - wind_speed: wind speed from zone (if zone data available)
      - temperature: current temperature from zone (if zone data available)
      - zone_name: name of the climate zone (if zone data available)
    """
    # Load settings for precipitation multiplier and zone data
    if settings is None and cell_y is not None:
        settings = load_settings()

    precipitation_multiplier = 1.0
    zone_info = None

    if settings is not None:
        precipitation_multiplier = settings.get('precipitation_multiplier', 1.0)
        if cell_y is not None:
            zone_info = get_zone_for_cell(cell_y, settings)

    # 0.0 to 1.0 scale for both inputs
    weather_info = None

    if chaos_level > 0.7 and tensegrity_pressure < 0.3:
        weather_info = {
            "type": "Abyssal Whirlpool" if is_oceanic else "Reality Storm",
            "travel_cost": 3.0 if is_oceanic else 2.0,
            "growth_mult": 0.5,
            "degradation_rate": 0.20 if is_oceanic else 0.15,
            "description": "Vortices of chaotic water threaten to drag entire fleets down." if is_oceanic else "Past and future echoes overlay the present; storms of raw magic rip through structures."
        }
    elif chaos_level > 0.6 and tensegrity_pressure > 0.6:
        weather_info = {
            "type": "Boiling Tides" if is_oceanic else "Flux Monsoon",
            "travel_cost": 2.0 if is_oceanic else 1.8,
            "growth_mult": 2.5 if is_oceanic else 2.0,
            "degradation_rate": 0.15 if is_oceanic else 0.10,
            "description": "The ocean boils with chaotic energy, hyper-accelerating kelp and coral growth." if is_oceanic else "Swirling torrential rain energized by chaos. Plant growth explodes, but floods damage buildings."
        }
    elif chaos_level < 0.3 and tensegrity_pressure > 0.7:
        weather_info = {
            "type": "Static Drought",
            "travel_cost": 1.2,
            "growth_mult": 0.2,
            "degradation_rate": 0.05,
            "description": "A dry, high-pressure lock that parches the soil and causes stone and lumber to crack."
        }
    elif chaos_level > 0.4:
        weather_info = {
            "type": "Aetheric Mist",
            "travel_cost": 1.5,
            "growth_mult": 1.2,
            "degradation_rate": 0.01,
            "description": "A thick, shimmering mist that obscures paths but feeds magical flora."
        }
    else:
        weather_info = {
            "type": "Stable",
            "travel_cost": 1.0,
            "growth_mult": 1.0,
            "degradation_rate": 0.0,
            "description": "Calm skies and balanced ambient energy."
        }

    # Apply precipitation multiplier from settings to growth
    weather_info["growth_mult"] *= precipitation_multiplier

    # Overlay zone-based temperature and wind context if zone data is available
    if zone_info is not None:
        wind_speed = zone_info.get('wind_speed', 0.5)
        temp_min = zone_info.get('temp_min', 5.0)
        temp_max = zone_info.get('temp_max', 25.0)

        # Calculate a current temperature influenced by chaos randomness
        temp_range = temp_max - temp_min
        temperature = temp_min + temp_range * random.uniform(0.3, 1.0)

        # Wind speed factor: higher wind increases travel cost slightly
        wind_travel_factor = 1.0 + (wind_speed - 0.5) * 0.2
        weather_info["travel_cost"] *= max(0.8, wind_travel_factor)

        # Extreme cold reduces growth, extreme heat can also stress growth
        if temperature < 0.0:
            cold_penalty = max(0.3, 1.0 + temperature / 50.0)
            weather_info["growth_mult"] *= cold_penalty
        elif temperature > 35.0:
            heat_penalty = max(0.5, 1.0 - (temperature - 35.0) / 30.0)
            weather_info["growth_mult"] *= heat_penalty

        weather_info["wind_dir"] = zone_info.get('wind_dir', 'N')
        weather_info["wind_speed"] = wind_speed
        weather_info["temperature"] = round(temperature, 1)
        weather_info["zone_name"] = zone_info.get('name', 'Unknown')

    # Weather behaves normally, but with a chance of storm cells becoming charged with chaos.
    # Chaos charge chance scales with regional chaos_level. Only non-stable weather can be charged.
    is_charged = False
    if weather_info["type"] != "Stable" and random.random() < chaos_level * 0.35:
        is_charged = True

    weather_info["is_chaos_charged"] = is_charged
    weather_info["destination_prison"] = magistar_id if is_charged else None

    return weather_info
