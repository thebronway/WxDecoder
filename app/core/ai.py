import os
import json
import re
from openai import AsyncOpenAI
from dotenv import load_dotenv
from app.core.settings import settings

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_json_string(s):
    if not s: return "{}"
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', s, re.DOTALL)
    if match:
        s = match.group(1)
    return s.strip()

async def analyze_risk(icao_code, weather_data, notams, plane_size="small", reporting_station=None, reporting_station_name=None, airport_tz="UTC", external_airspace_warnings=[]):
    
    profiles = {
        "small": "Cessna 172/Piper Archer (Max X-Wind: 15kts, IFR: No Radar)",
        "medium": "Baron/Cirrus SR22 (Max X-Wind: 20kts, IFR: Capable)",
        "large": "TBM/Citation (Max X-Wind: 30kts, High Altitude Capable)"
    }
    selected_profile = profiles.get(plane_size, profiles["small"])

    station_context = ""
    weather_source_name = reporting_station_name or reporting_station or icao_code
    target_name = icao_code

    if reporting_station and reporting_station != icao_code:
        station_context = f"""
        NOTE: Weather is from {weather_source_name} ({reporting_station}).
        NOTE: Target Airport is {target_name}.
        """

    airspace_alert_text = """
    NOTE: No intersection with Permanent Prohibited/Restricted zones (P-40, DC SFRA, etc.) detected.
    CRITICAL: This tool DOES NOT check dynamic TFRs (VIPs, Stadiums, Fire). 
    Pilot MUST verify TFRs at: https://tfr.faa.gov/
    """
    
    if external_airspace_warnings:
        bullet_list = "\n".join([f"- {w}" for w in external_airspace_warnings])
        airspace_alert_text = f"""
        [MANDATORY INCLUSION]
        The following PERMANENT AIRSPACE RESTRICTIONS were detected near the TARGET ({target_name}):
        {bullet_list}
        CRITICAL: Also verify dynamic TFRs at https://tfr.faa.gov/
        """

    system_prompt = f"""
    You are a Chief Pilot acting as a Go/No-Go decision aid.
    AIRCRAFT PROFILE: {selected_profile}
    TARGET TIMEZONE: {airport_tz}
    
    YOUR TASKS:
    1. RUNWAY SELECTION: Identify best runway and calculate Crosswind Component based on weather at {weather_source_name}.
    2. RISK ASSESSMENT: Compare X-Wind vs Profile Max. >= Limit -> "HIGH". Within 5kts -> "MODERATE". Else "LOW".
    3. NOTAMS: Scan for MAJOR hazards (Closures, Lighting) specifically for the TARGET.
    4. SUMMARY: Single cohesive paragraph. 
       - CRITICAL: Always include the ICAO code in parentheses when naming an airport (e.g. "General Edward Lawrence Logan International Airport (KBOS)").
       - START with "Weather at [Weather Source Name] ([Code])..." describing wind/clouds.
       - IF the target airport is DIFFERENT from the weather source, switch context using the phrase: "At [Target Name] ([Code])..." to discuss its Airspace and NOTAMs.
       - IF they are the same, NEVER repeat the airport name. Simply continue with "The airspace..." or "NOTAMs include..."
    5. TIMELINE: Analyze the TAF.
       - CHECK FIRST: If TAF contains "No TAF" or is missing, set "time_label" to "TAF Not Available" and "summary" to "-" for BOTH t_06 and t_12.
       - OTHERWISE: Ignore lines ('FM', 'BECMG') starting < 1 hour from now. Find the NEXT 2 relevant forecast periods.
       - LABEL FORMAT: Convert the TAF time code (e.g. FM1800) into a human readable local time string using the timezone {airport_tz} (e.g. "From 2:00 PM EST").
    6. BUBBLES: Short text for UI (e.g., "North at 10kts").
    
    OUTPUT JSON FORMAT ONLY:
    {{
        "flight_category": "VFR" | "MVFR" | "IFR" | "LIFR",
        "wind_risk": "LOW" | "MODERATE" | "HIGH",
        "executive_summary": "...",
        "timeline": {{ 
            "t_06": {{ "time_label": "e.g. From 2:00 PM EST", "summary": "..." }}, 
            "t_12": {{ "time_label": "...", "summary": "..." }}
        }},
        "bubbles": {{ 
            "wind": "...", 
            "visibility": "...", 
            "ceiling": "...", 
            "temp": "..." 
        }},
        "airspace_warnings": ["..."],
        "critical_notams": ["..."]
    }}
    """

    user_content = f"""
    TARGET AIRPORT: {target_name}
    WEATHER SOURCE: {weather_source_name} ({reporting_station or icao_code})
    {station_context}
    
    AIRSPACE STATUS:
    {airspace_alert_text}
    
    METAR: {weather_data['metar']}
    TAF: {weather_data['taf']}
    NOTAMS: {str(notams[:50])} 
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
        
        result['_meta'] = {
            "tokens": tokens,
            "model": model_used
        }
        
        return result

    except Exception as e:
        print(f"AI ERROR: {e}")
        return {
            "flight_category": "UNK",
            "wind_risk": "LOW",
            "executive_summary": f"AI Parsing Error: {str(e)}",
            "timeline": {
                "t_06": {"time_label": "--", "summary": "Forecast unavailable"}, 
                "t_12": {"time_label": "--", "summary": "--"}
            },
            "bubbles": {"wind": "--", "visibility": "--", "ceiling": "--", "temp": "--"},
            "airspace_warnings": [],
            "critical_notams": []
        }