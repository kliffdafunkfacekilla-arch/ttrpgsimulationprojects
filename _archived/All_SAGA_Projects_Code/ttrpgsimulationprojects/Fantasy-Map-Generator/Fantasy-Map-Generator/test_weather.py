from modules.weather_system import calculate_weather

def test_reality_storm():
    weather = calculate_weather(chaos_level=0.9, tensegrity_pressure=0.1)
    assert weather["type"] == "Reality Storm", f"Expected Reality Storm, got {weather['type']}"
    print("Test passed: calculate_weather(0.9, 0.1) returns Reality Storm")

if __name__ == "__main__":
    test_reality_storm()
