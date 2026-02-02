import time
import datetime
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.core.weather import get_metar_taf
from app.core.notams import get_notams
from app.core.ai import analyze_risk
from app.core.geography import get_nearest_reporting_stations, check_airspace_zones, airports_icao, airports_lid
from app.core.rate_limit import RateLimiter
from app.core.logger import log_attempt
from app.core.cache import get_cached_report, save_cached_report
from app.core.settings import settings
from app.core.notifications import notifier
from app.core.db import database

router = APIRouter()
limiter = RateLimiter()

class AnalysisRequest(BaseModel):
    icao: str
    plane_size: str

async def prune_old_logs():
    try:
        query = "DELETE FROM logs WHERE timestamp < NOW() - INTERVAL '90 days'"
        await database.execute(query)
    except Exception as e:
        print(f"CLEANUP ERROR: {e}")

@router.post("/analyze")
async def analyze_flight(request: AnalysisRequest, raw_request: Request, background_tasks: BackgroundTasks):
    if settings.get("global_pause") == "true":
        msg = settings.get("global_pause_message", "System is under maintenance.")
        raise HTTPException(status_code=503, detail=msg)

    # Cleanup runs in background
    background_tasks.add_task(prune_old_logs)

    t_start = time.time()
    
    client_id = raw_request.headers.get("X-Client-ID", "UNKNOWN")
    client_ip = raw_request.headers.get("X-Forwarded-For", raw_request.client.host).split(',')[0].strip()
    
    raw_input = request.icao.upper().strip()
    input_icao = raw_input
    if len(raw_input) == 3 and ("K" + raw_input) in airports_icao:
        input_icao = "K" + raw_input
    
    resolved_icao = input_icao 
    status = "FAIL" 
    error_msg = None
    model_used = None
    tokens_used = 0

    t_weather = 0
    t_notams = 0
    t_ai = 0

    try:
        # 1. CACHE CHECK
        cached_result = await get_cached_report(input_icao, request.plane_size)
        if cached_result:
            duration = time.time() - t_start
            status = "CACHE_HIT" 
            await log_attempt(client_id, client_ip, input_icao, resolved_icao, request.plane_size, duration, "CACHE_HIT")
            return cached_result

        # 2. RATE LIMIT CHECK
        await limiter(raw_request)

        # 3. FETCH DATA
        airport_data = airports_icao.get(input_icao) or airports_lid.get(input_icao)
        airport_name = airport_data['name'] if airport_data else input_icao
        if airport_data: resolved_icao = airport_data.get('icao', input_icao)

        airspace_warnings = []
        if airport_data:
            try:
                lat, lon = float(airport_data['lat']), float(airport_data['lon'])
                airspace_warnings = check_airspace_zones(input_icao, lat, lon)
            except: pass

        t0 = time.time()
        weather_icao = input_icao
        weather_data = await get_metar_taf(input_icao)
        if not weather_data:
            candidates = await get_nearest_reporting_stations(input_icao)
            for station in candidates:
                data = await get_metar_taf(station)
                if data:
                    weather_icao = station
                    weather_data = data
                    break
        t_weather = time.time() - t0
        
        if not weather_data:
            return {"error": "No airport or weather data found."}

        t0 = time.time()
        notams = await get_notams(input_icao)
        t_notams = time.time() - t0

        t0 = time.time()
        analysis = await analyze_risk(
            icao_code=input_icao,
            weather_data=weather_data,
            notams=notams,
            plane_size=request.plane_size,
            reporting_station=weather_icao,
            external_airspace_warnings=airspace_warnings
        )
        t_ai = time.time() - t0

        if '_meta' in analysis:
            tokens_used = analysis['_meta'].get('tokens', 0)
            model_used = analysis['_meta'].get('model', 'unknown')
            del analysis['_meta']

        response_data = {
            "airport_name": airport_name,
            "analysis": analysis,
            "raw_data": {
                "metar": weather_data['metar'],
                "taf": weather_data['taf'],
                "notams": notams,
                "weather_source": weather_icao
            }
        }

        await save_cached_report(input_icao, request.plane_size, response_data)
        status = "SUCCESS"
        return response_data

    except HTTPException as e:
        if e.status_code == 429:
            status = "RATE_LIMIT"
            # FIX: Send Alert IMMEDIATELY (awaited) to ensure it fires before 429 return
            print(f"DEBUG: Triggering Rate Limit Alert for {client_ip}...")
            try:
                await notifier.send_alert(
                    "rate_limit", 
                    f"Rate Limit Hit: {input_icao}", 
                    f"User {client_id} (IP: {client_ip}) exceeded limits."
                )
            except Exception as mail_err:
                print(f"DEBUG: Alert System Failed: {mail_err}")
        else:
            status = "ERROR"
        
        error_msg = e.detail
        raise e
        
    except Exception as e:
        status = "ERROR"
        error_msg = str(e)
        # For 500 errors, we still use background tasks to avoid hanging
        background_tasks.add_task(notifier.send_alert, "error", "System Error", str(e))
        raise e
        
    finally:
        if status != "CACHE_HIT":
            duration = time.time() - t_start
            print(f"⏱️  PERFORMANCE: {input_icao} | Total: {duration:.2f}s | Wx: {t_weather:.2f}s | NOTAMs: {t_notams:.2f}s | AI: {t_ai:.2f}s")
            await log_attempt(client_id, client_ip, input_icao, resolved_icao, request.plane_size, duration, status, error_msg, model_used, tokens_used)