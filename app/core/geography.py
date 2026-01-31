import airportsdata
import math
import requests

# Load Databases
print("DEBUG: Loading airport databases...")
airports_icao = airportsdata.load('ICAO')
airports_lid = airportsdata.load('LID')
print(f"DEBUG: Loaded {len(airports_icao)} ICAO and {len(airports_lid)} LID airports.")

# --- DEFINED AIRSPACE ZONES ---
RESTRICTED_ZONES = {
    "DC_SFRA": {
        "name": "Washington DC SFRA",
        "lat": 38.8512, "lon": -77.0377, # DCA VOR
        "radius": 30, # Nautical Miles
        "type": "RESTRICTED"
    },
    "DC_FRZ": {
        "name": "Washington DC Flight Restricted Zone (FRZ)",
        "lat": 38.8512, "lon": -77.0377, 
        "radius": 13, 
        "type": "PROHIBITED" 
    }
}

def get_coords_from_awc(icao):
    """Fallback: Ask FAA API."""
    try:
        url = f"https://aviationweather.gov/api/data/station?ids={icao}&format=json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return {
                    "lat": float(data[0]["lat"]), 
                    "lon": float(data[0]["lon"]),
                    "name": data[0].get("site", icao)
                }
    except Exception as e:
        print(f"DEBUG: API Lookup Error: {e}")
    return None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c * 0.539957  # Convert to NM

# UPDATED FUNCTION: Now accepts target_code
def check_airspace_zones(target_code, target_lat, target_lon):
    """
    Checks if coordinates fall inside or near known restricted zones.
    Returns a list of warning strings using the target_code.
    """
    warnings = []
    
    for zone_id, zone in RESTRICTED_ZONES.items():
        dist = calculate_distance(target_lat, target_lon, zone['lat'], zone['lon'])
        
        # 1. DIRECT HIT
        if dist <= zone['radius']:
            if zone['type'] == "PROHIBITED":
                # EXACT PHRASING REQUESTED (Corrected typo "Airportis" -> "is")
                warnings.append(f"CRITICAL: {target_code} is located within the {zone['name']} ({dist:.1f}nm from center). Flight strictly restricted; special procedures required.")
            else:
                warnings.append(f"WARNING: {target_code} is located within the {zone['name']}. Special procedures required.")
        
        # 2. PROXIMITY WARNING (5nm Buffer)
        elif dist <= (zone['radius'] + 5):
             # EXACT PHRASING REQUESTED
             warnings.append(f"ADVISORY: {target_code} is just outside ({dist:.1f}nm from the center) of the {zone['name']}. Exercise caution near boundary.")

    return warnings

def get_nearest_reporting_stations(target_code, limit=10):
    """
    Returns a LIST of nearest airport codes.
    PRIORITIZES Large/Medium airports to ensure we find a valid weather station quickly.
    """
    target_code = target_code.upper().strip()
    
    target = airports_icao.get(target_code) or airports_lid.get(target_code)
    
    if not target:
        target = get_coords_from_awc(target_code)

    if not target:
        return []

    target_lat = float(target['lat'])
    target_lon = float(target['lon'])

    # Separate lists for prioritization
    primary_candidates = []   # Large/Medium (Likely to have METAR)
    secondary_candidates = [] # Small (Unlikely to have METAR)
    
    for code, data in airports_icao.items():
        if code == target_code: 
            continue
        try:
            lat = float(data['lat'])
            lon = float(data['lon'])
            dist = calculate_distance(target_lat, target_lon, lat, lon)
            
            if dist < 50: 
                # CLASSIFY THE AIRPORT
                apt_type = data.get('type', 'small_airport')
                
                if apt_type in ['large_airport', 'medium_airport']:
                    primary_candidates.append((code, dist))
                else:
                    secondary_candidates.append((code, dist))
        except:
            continue

    # Sort both lists by distance
    primary_candidates.sort(key=lambda x: x[1])
    secondary_candidates.sort(key=lambda x: x[1])
    
    # Merge: Priority first, then secondary
    final_list = [x[0] for x in primary_candidates] + [x[0] for x in secondary_candidates]
    
    return final_list[:limit]