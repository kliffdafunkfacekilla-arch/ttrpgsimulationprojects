# systems/weather_ecology.py

def calculate_weather(cell_agent, calendar_ctx: dict):
    """
    Called from CellAgent.stage_environment().
    Mutates the agent's weather and food_supply in place.
    Supports separate calculation paths for above-ground vs. underwater biomes.
    """
    if cell_agent.is_underwater:
        # Underwater weather: driven by tide multiplier from moon phase
        tide = calendar_ctx.get('tide_multiplier', 1.0)
        if cell_agent.chaos_saturation > 0.7:
            cell_agent.weather = 'Abyssal Chaos Surge'
            cell_agent.food_supply *= 0.5  # Kelp fields destroyed
        elif tide > 1.3:
            cell_agent.weather = 'Strong Current'
            cell_agent.food_supply *= 0.85
        else:
            cell_agent.weather = 'Calm Depths'
    else:
        # Surface weather: pressure-driven diffusion
        # chaos_saturation overrides normal weather entirely
        if cell_agent.chaos_saturation > 0.8:
            cell_agent.weather = 'Chaos Storm'
            cell_agent.food_supply = max(0.0, cell_agent.food_supply - 0.3)
            # Flag cell for dangerous variant spawning
            cell_agent.has_mutated_wildlife = True
        else:
            cell_agent.weather = 'Clear'
            cell_agent.has_mutated_wildlife = False
