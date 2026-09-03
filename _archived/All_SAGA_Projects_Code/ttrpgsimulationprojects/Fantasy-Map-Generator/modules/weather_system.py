# weather_system.py

def calculate_weather(chaos_level, tensegrity_pressure):
    """
    Models the Aetheric backwash.
    High Chaos + Low Pressure = Reality Storm
    """

    # 0.0 to 1.0 scale for both inputs
    if chaos_level > 0.7 and tensegrity_pressure < 0.3:
        return {
            "type": "Reality Storm",
            "effect": "Temporal Bleed",
            "description": "Past and future echoes overlay the present.",
            "stability_penalty": 0.5 # Entropy damage to city structures
        }

    elif chaos_level > 0.4:
        return {"type": "Aetheric Mist", "travel_cost": 1.5}

    return {"type": "Stable", "travel_cost": 1.0}
