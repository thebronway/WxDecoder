import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from app.core.settings import settings  # <--- NEW IMPORT for Dynamic Model

load_dotenv()

# Initialize Async Client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_risk(icao_code, weather_data, notams, plane_size="small", reporting_station=None, external_airspace_warnings=[]):
    
    profiles = {
        "small": "Cessna 172/Piper Archer (Max X-Wind: 15kts, IFR: No Radar)",
        "medium": "Baron/Cirrus SR22 (Max X-Wind: 20kts, IFR: Capable)",
        "large": "TBM/Citation (Max X-Wind: 30kts, High Altitude Capable)"
    }
    selected_profile = profiles.get(plane_size, profiles["small"])

    station_context = ""
    if reporting_station and reporting_station != icao_code:
        station_context = f"NOTE: Target {icao_code} has no weather. Using {reporting_station} for METAR/TAF."

    # --- AIRSPACE LOGIC ---
    airspace_alert_text = """
    NOTE: No intersection with Permanent Prohibited/Restricted zones (P-40, DC SFRA, etc.) detected.
    
    CRITICAL: This tool DOES NOT check dynamic TFRs (VIPs, Stadiums, Fire). 
    Pilot MUST verify TFRs at: https://tfr.faa.gov/
    """
    
    if external_airspace_warnings:
        bullet_list = "\n".join([f"- {w}" for w in external_airspace_warnings])
        airspace_alert_text = f"""
        [MANDATORY INCLUSION]
        The following PERMANENT AIRSPACE RESTRICTIONS were detected:
        {bullet_list}
        
        CRITICAL: Also verify dynamic TFRs at https://tfr.faa.gov/
        """

    # --- PROMPT LOGIC ---
    system_prompt = f"""
    You are a Chief Pilot acting as a Go/No-Go decision aid.
    AIRCRAFT PROFILE: {selected_profile}
    
    YOUR TASKS:
    1. RUNWAY SELECTION & VECTOR MATH:
       - Identify best runway at {icao_code} based on METAR wind.
       - Calculate Crosswind Component.
       - If runway unknown, assume Worst Case.
    
    2. RISK ASSESSMENT:
       - Compare Calculated X-Wind vs Profile Max X-Wind.
       - >= Limit -> "HIGH"
       - Within 5kts -> "MODERATE"
       - Else -> "LOW"

    3. CRITICAL NOTAMS (PLAIN ENGLISH TRANSLATION):
       - First, scan raw NOTAMs for MAJOR hazards (Runway Closures, Approach Lighting Out, Tower Closed).
       - Select the top 1-3 most critical.
       - TRANSLATE to Plain English.
    
    4. EXECUTIVE SUMMARY (Cohesive Narrative):
       - Write a single, flowing paragraph (DO NOT use labels like "Part 1" or bullet points).
       - Start with the conditions (VFR/IFR, Ceiling, Vis).
       - Move to the favored runway and crosswind calculation.
       - End with Airspace warnings and a summary of the Critical NOTAMs you identified.
       
    5. TIMELINE: 
       - If no TAF, return "NO_TAF".
       - Else, summarize next 6/12/24 hours in plain English.
    
    6. BUBBLES: Return HUMAN READABLE short text.
       - Wind: e.g., "North at 10kts"
    
    OUTPUT JSON FORMAT ONLY:
    {{
        "flight_category": "VFR" | "MVFR" | "IFR" | "LIFR",
        "wind_risk": "LOW" | "MODERATE" | "HIGH",
        "executive_summary": "VFR conditions with clear skies... Favored runway is 33L... Critical NOTAMs include...",
        "timeline": {{ "t_06": "...", "t_12": "...", "t_24": "..." }},
        "bubbles": {{ 
            "wind": "North at 10kts", 
            "visibility": "10 Miles", 
            "ceiling": "Overcast 1,500'", 
            "temp": "24°C" 
        }},
        "airspace_warnings": ["..."],
        "critical_notams": ["(Plain English NOTAM 1)", "(Plain English NOTAM 2)"]
    }}
    """

    user_content = f"""
    TARGET: {icao_code}
    {station_context}
    
    AIRSPACE STATUS:
    {airspace_alert_text}
    
    METAR: {weather_data['metar']}
    TAF: {weather_data['taf']}
    NOTAMS: {str(notams[:50])} 
    """

    try:
        # DYNAMIC MODEL SELECTION
        model_id = settings.get("openai_model", "gpt-4o-mini")

        response = await client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        # EXTRACT USAGE
        usage = response.usage
        tokens = usage.total_tokens if usage else 0
        model_used = response.model

        result = json.loads(response.choices[0].message.content)
        
        # Inject metadata into result so the router can log it
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
            "timeline": {"t_06": "--", "t_12": "--", "t_24": "--"},
            "bubbles": {"wind": "--", "visibility": "--", "ceiling": "--", "temp": "--"},
            "airspace_warnings": [],
            "critical_notams": []
        }