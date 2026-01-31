from fastapi import APIRouter
from pydantic import BaseModel
from app.core.weather import get_metar_taf
from app.core.notams import get_notams
from app.core.ai import analyze_risk
from app.core.geography import get_nearest_reporting_stations, check_airspace_zones, airports_icao, airports_lid

router = APIRouter()

class AnalysisRequest(BaseModel):
    icao: str
    plane_size: str

@router.post("/api/analyze")
async def analyze_flight(request: AnalysisRequest):
    target_icao = request.icao.upper().strip()
    
    # 1. Get Airport Data
    airport_data = None
    if target_icao in airports_icao:
        airport_data = airports_icao[target_icao]
    elif target_icao in airports_lid:
        airport_data = airports_lid[target_icao]
    
    airport_name = airport_data['name'] if airport_data else target_icao
    
    # 2. Check Airspace Zones
    airspace_warnings = []
    if airport_data:
        try:
            lat = float(airport_data['lat'])
            lon = float(airport_data['lon'])
            airspace_warnings = check_airspace_zones(target_icao, lat, lon)
        except Exception as e:
            print(f"DEBUG: Airspace check failed: {e}")

    # 3. Weather Logic (UPDATED TO ASYNC)
    weather_icao = target_icao
    # We use 'await' here so the server can do other things while waiting
    weather_data = await get_metar_taf(target_icao)
    
    if not weather_data:
        # Search nearby stations
        candidates = get_nearest_reporting_stations(target_icao)
        for station in candidates:
            # We use 'await' here as well
            data = await get_metar_taf(station)
            if data:
                weather_icao = station
                weather_data = data
                break
    
    if not weather_data:
        return {"error": f"Could not find weather data for {target_icao} or nearby stations."}

    # 4. NOTAMs
    notams = await get_notams(target_icao)

    # 5. AI Analysis
    analysis = analyze_risk(
        icao_code=target_icao,
        weather_data=weather_data,
        notams=notams,
        plane_size=request.plane_size,
        reporting_station=weather_icao,
        external_airspace_warnings=airspace_warnings
    )

    return {
        "airport_name": airport_name,
        "analysis": analysis,
        "raw_data": {
            "metar": weather_data['metar'],
            "taf": weather_data['taf'],
            "notams": notams,
            "weather_source": weather_icao
        }
    }