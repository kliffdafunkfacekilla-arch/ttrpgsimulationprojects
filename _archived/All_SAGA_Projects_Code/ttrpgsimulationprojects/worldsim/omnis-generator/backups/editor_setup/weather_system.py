# weather_system.py
import random

def calculate_weather(chaos_level, tensegrity_pressure, magistar_id=None, is_oceanic=False):
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
    """
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

    # Weather behaves normally, but with a chance of storm cells becoming charged with chaos.
    # Chaos charge chance scales with regional chaos_level. Only non-stable weather can be charged.
    is_charged = False
    if weather_info["type"] != "Stable" and random.random() < chaos_level * 0.35:
        is_charged = True

    weather_info["is_chaos_charged"] = is_charged
    weather_info["destination_prison"] = magistar_id if is_charged else None

    return weather_info
