import math

def calculate_crosswind(runway_heading: int, wind_direction: int, wind_speed: int) -> int:
    if wind_speed == 0: return 0
    diff = abs(runway_heading - wind_direction)
    if diff > 180: diff = 360 - diff
    angle_rad = math.radians(diff)
    return round(wind_speed * math.sin(angle_rad))