import os
import json
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from app.core.settings import settings
from app.core.physics import calculate_crosswind

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_json_string(s):
    if not s: return "{}"
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', s, re.DOTALL)
    if match:
        s = match.group(1)
    return s.strip()

def format_visibility(val: str) -> str:
    """Converts decimal visibility strings to aviation fractions."""
    mappings = {
        "0.125": "1/8",
        "0.25": "1/4",
        "0.375": "3/8",
        "0.5": "1/2",
        "0.625": "5/8",
        "0.75": "3/4",
        "1.25": "1 1/4",
        "1.5": "1 1/2",
        "1.75": "1 3/4"
    }
    
    # Extract the numeric part if 'SM' is attached
    clean_val = val.upper().replace("SM", "").strip()
    
    if clean_val in mappings:
        return f"{mappings[clean_val]} SM"
    
    return val # Return original if no mapping found or already a fraction

async def analyze_risk(icao_code, weather_data, notams, plane_size="small", reporting_station=None, reporting_station_name=None, airport_tz="UTC", external_airspace_warnings=[], dist=0, target_icao=""):
    
    profiles = {
        "small": "Cessna 172/Piper Archer (Max Crosswind: 15kts, IFR: No Radar)",
        "medium": "Baron/Cirrus SR22 (Max Crosswind: 20kts, IFR: Capable)",
        "large": "TBM/Citation (Max Crosswind: 30kts, High Altitude Capable)"
    }
    selected_profile = profiles.get(plane_size, profiles["small"])

    # --- 1. SMART CONTEXT BUILDER (PYTHON SIDE) ---
    weather_source_name = reporting_station_name or reporting_station or icao_code
    
    # Create a nice display name: "General Edward... (KBOS)"
    target_display = f"{icao_code} ({target_icao})" if target_icao else icao_code
    
    has_weather = weather_data.get('metar') is not None
    is_same_airport = (dist < 2.0) or (reporting_station == target_icao)
    
    if not has_weather:
         opening_instruction = f"Start the weather section exactly with: 'No weather data available within 50nm of {target_display}.'"
    elif is_same_airport:
         opening_instruction = f"Start the weather section exactly with: 'Conditions at {target_display} are...'"
    else:
         opening_instruction = f"Start the weather section exactly with: 'Weather reported at {weather_source_name} ({dist:.1f}nm away) indicates...'"

    # --- 2. AIRSPACE LOGIC (PYTHON SIDE) ---
    # We construct the EXACT text we want here so the AI doesn't guess.
    if external_airspace_warnings:
        bullet_list = "\n".join([f"- {w}" for w in external_airspace_warnings])
        airspace_status_content = f"""
        WARNING - RESTRICTIONS DETECTED:
        {bullet_list}
        """
    else:
        airspace_status_content = "No intersection with Permanent Prohibited/Restricted zones (P-40, DC SFRA, etc) detected."

    # Common disclaimer added to both scenarios
    airspace_status_content += "\n(MANDATORY: Pilots must always verify dynamic TFRs at tfr.faa.gov before flight.)"

    system_prompt = f"""
    You are a Weather Analysis Assistant providing data for pilot interpretation.
    AIRCRAFT PROFILE: {selected_profile}
    TARGET TIMEZONE: {airport_tz}
    
    YOUR TASKS:
    1. STRUCTURE: Do NOT return a single text block. You must return FOUR separate summary strings in the JSON output:
       - "summary_weather"
       - "summary_crosswind"
       - "summary_airspace"
       - "summary_notams"
    
    2. WEATHER SUMMARY ("summary_weather"):
       - OPENING: {opening_instruction}
       - CONTENT: Describe wind, visibility, clouds.
       - TRANSLATION RULE: NEVER use raw METAR codes in this text. Translate them (e.g., "Winds are calm").
       - GRAMMAR: Do NOT use the word "The" before an airport name.
       
    3. CROSSWIND DATA EXTRACTION:
       - IDENTIFY: Find the best runway for the current wind.
       - GUST MANDATE: Always use the peak gust for safety calculations.
       - RAW DATA: Provide the raw runway heading (e.g., 220 for 22R) and the peak wind speed.
       - PHRASING: The "summary_crosswind" text should explain the logic (e.g., "Using Runway 22R with an offset of 30 degrees...").

    4. AIRSPACE SUMMARY ("summary_airspace"):
       - CONTENT: Summarize the provided "AIRSPACE STATUS" block.
       - Trust the python context implicitly.

    5. NOTAMS SUMMARY ("summary_notams"):
       - CONTENT: Scan for MAJOR hazards. Translate technical notes to plain English.
       - FORMAT: Provide a single, cohesive paragraph summarizing the key hazards. Do NOT use bullet points in this text section.

    6. BUBBLES (UI DATA):
       - "wind": 
         - **STRICT FORMAT RULE**: If winds are 00000KT, you MUST return exactly "Winds Calm".
         - **STRICT FORMAT RULE**: For all other conditions, use the format "DDD° SSkts" (e.g., "050° 16kts"). DDD must be the 3-digit numeric heading.
         - **GUST RULE**: If gusts are present, append " | Gust SSkts" (e.g., "050° 16kts | Gust 22kts"). Use the pipe symbol as a separator.
         - **VARIABLE WINDS**: If direction is variable (VRB), use "VRB SSkts" (e.g., "VRB 04kts").
       - "x_wind": Return ONLY the raw peak wind speed as an integer (e.g., 22).
       - "rwy_heading": Return ONLY the 3-digit numeric heading of the best runway (e.g., 220).
       - "rwy": The runway name (e.g., "22R")
       - "visibility": CRITICAL: Use standard aviation fractions (e.g., "1 3/4 SM"). NEVER use decimals.
       - "ceiling": 
         - **STRICT LONGFORM RULE**: You MUST spell out full words (e.g., "Broken", "Overcast") and include "FT AGL" for ALL BKN or OVC layers.
         - **STRICT MULTILINE RULE**: If there is more than one layer, you MUST put each layer on a new line. Do not use slashes or spaces between them; use a literal line break.
         - **STRICT EXAMPLES**:
           - METAR BKN020: "Broken 2000 FT AGL"
           - METAR BKN020 OVC038: "Broken 2000 FT AGL\nOvercast 3800 FT AGL"
           - METAR CLR: "Clear"
         - Heights are always AGL (Above Ground Level).

       - **RAW MATH DATA (MANDATORY)**:
         - "rwy_heading_raw": Integer heading of the chosen runway (e.g., 220).
         - "wind_dir_raw": Integer heading of the wind (e.g., 50).
         - "wind_speed_raw": Integer of the PEAK wind or peak gust speed (e.g., 22).
    
    7. JSON ARRAYS:
       - "airspace_warnings": ONLY include actual warnings. If the status is "No intersection...", return an EMPTY LIST [].
       - "critical_notams": List the top 3-5 most critical notams (short summary).

    OUTPUT JSON FORMAT ONLY:
    {{
        "flight_category": "VFR" | "MVFR" | "IFR" | "LIFR" | "UNK",
        "crosswind_status": "WITHIN LIMITS" | "NEAR LIMITS" | "EXCEEDS PROFILE" | "UNK",
        "summary_weather": "...",
        "summary_crosswind": "...",
        "summary_airspace": "...",
        "summary_notams": "...",
        "timeline": {{ 
            "t_06": {{ "time_label": "e.g. From 2:00 PM EST", "summary": "..." }}, 
            "t_12": {{ "time_label": "...", "summary": "..." }}
        }},
        "bubbles": {{ 
            "wind": "...", 
            "x_wind": "...",
            "rwy": "...",
            "rwy_heading_raw": 0,
            "wind_dir_raw": 0,
            "wind_speed_raw": 0,
            "visibility": "...", 
            "ceiling": "...", 
            "temp": "..." 
        }},
        "airspace_warnings": ["..."],
        "critical_notams": ["..."]
    }}
    """

    user_content = f"""
    TARGET AIRPORT: {target_display}
    WEATHER SOURCE: {weather_source_name} ({reporting_station or icao_code})
    DISTANCE TO TARGET: {dist:.1f}nm
    
    AIRSPACE STATUS:
    {airspace_status_content}
    
    METAR: {weather_data.get('metar', 'N/A')}
    TAF: {weather_data.get('taf', 'N/A')}
    NOTAMS: {str(notams)} 
    """

    try:
        model_id = await settings.get("openai_model", "gpt-4o-mini")

        response = await client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        usage = response.usage
        tokens = usage.total_tokens if usage else 0
        model_used = response.model

        raw_content = response.choices[0].message.content
        cleaned_content = clean_json_string(raw_content)
        
        result = json.loads(cleaned_content)

        # Fail-safe cleaning for visibility and PHYSICS OVERRIDE for crosswind
        if "bubbles" in result:
            # 1. Fix Visibility
            if "visibility" in result["bubbles"]:
                result["bubbles"]["visibility"] = format_visibility(result["bubbles"]["visibility"])
            
            # 2. Exact Crosswind Calculation (Override AI's guess)
            # We pull the raw ingredients identified by the AI
            rwy_h = result["bubbles"].get("rwy_heading_raw", 0)
            w_dir = result["bubbles"].get("wind_dir_raw", 0)
            w_spd = result["bubbles"].get("wind_speed_raw", 0)
            
            # Call our Python math engine
            x_wind_value = calculate_crosswind(rwy_h, w_dir, w_spd)
            
            # Update the display bubble with the verified number
            result["bubbles"]["x_wind"] = f"{x_wind_value}kts"
            
            # Cleanup: Remove raw fields so they don't clutter the UI frontend
            result["bubbles"].pop("rwy_heading_raw", None)
            result["bubbles"].pop("wind_dir_raw", None)
            result["bubbles"].pop("wind_speed_raw", None)
        
        result['_meta'] = {
            "tokens": tokens,
            "model": model_used
        }
        
        return result

    except Exception as e:
        print(f"AI ERROR: {e}")
        return {
            "flight_category": "UNK",
            "crosswind_status": "WITHIN LIMITS",
            "summary_weather": f"AI Parsing Error: {str(e)}",
            "summary_crosswind": "--",
            "summary_airspace": "--",
            "summary_notams": "--",
            "timeline": {
                "t_06": {"time_label": "--", "summary": "Forecast unavailable"}, 
                "t_12": {"time_label": "--", "summary": "--"}
            },
            "bubbles": {"wind": "--", "visibility": "--", "ceiling": "--", "temp": "--"},
            "airspace_warnings": [],
            "critical_notams": []
        }