def create_director_graph():
    """
    Simulated AI Director Graph.
    Now supports VTT commands like screen shakes based on tension and weather.
    """
    class StubGraph:
        async def ainvoke(self, state):
            # 1. Generate Narration
            time_str = f"{state.get('weather', 'Clear')} skies overhead."
            if state.get("tension", 0) > 40:
                state["ai_narration"] = f"A heavy silence hangs in the air. {time_str} You feel watched."
                # 2. Add VTT Commands if tension is high
                state["vtt_commands"].append({
                    "type": "CAMERA_SHAKE",
                    "intensity": 0.5,
                    "duration": 500
                })
            else:
                state["ai_narration"] = f"The journey continues. {time_str}"

            state["math_log"] += f"\n[DIRECTOR] Tension: {state.get('tension', 0)} | Pulse complete."
            return state
    
    return StubGraph()
