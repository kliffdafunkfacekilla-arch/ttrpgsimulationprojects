# systems/calendar_manager.py

TICKS_PER_DAY = 3
DAYS_PER_MONTH = 30
MOON_CYCLE = 28  # days

def get_calendar_context(tick: int) -> dict:
    """
    Translates raw tick count into narrative time.
    Returns a calendar context dict read by other systems.
    """
    day = tick // TICKS_PER_DAY
    month = day // DAYS_PER_MONTH
    moon_phase = (day % MOON_CYCLE) / MOON_CYCLE  # 0.0=new, 0.5=full, 1.0=new

    is_full = 0.45 < moon_phase < 0.55
    tide_multiplier = 1.0 + (moon_phase * 0.5) if is_full else 1.0

    return {
        'tick': tick,
        'day': day,
        'month': month,
        'moon_phase': moon_phase,
        'is_full_moon': is_full,
        # Full moon amplifies underwater weather and magic_density
        'tide_multiplier': tide_multiplier,
    }
