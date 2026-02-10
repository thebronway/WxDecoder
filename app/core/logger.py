import datetime
import logging
from app.core.db import database

logger = logging.getLogger(__name__)

async def log_attempt(client_id, ip, input_icao, resolved_icao, plane, duration, status, error_msg=None, model=None, tokens=0, weather_icao=None, expiration=None, t_wx=0, t_notams=0, t_ai=0, t_alt=0):
    query = """
        INSERT INTO logs (
            timestamp, client_id, ip_address, input_icao, resolved_icao, 
            plane_profile, duration_seconds, status, error_message,
            model_used, tokens_used, weather_icao, expiration_timestamp,
            duration_wx, duration_notams, duration_ai, duration_alt
        ) VALUES (
            :timestamp, :client_id, :ip_address, :input_icao, :resolved_icao, 
            :plane_profile, :duration_seconds, :status, :error_message, 
            :model_used, :tokens_used, :weather_icao, :expiration_timestamp,
            :t_wx, :t_notams, :t_ai, :t_alt
        )
    """
    
    # FIX: Use Naive UTC to match the "TIMESTAMP" column in Postgres (No Timezone)
    now_naive = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    
    # Ensure expiration is also Naive UTC if provided
    exp_naive = None
    if expiration:
        if expiration.tzinfo is not None:
             exp_naive = expiration.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        else:
             exp_naive = expiration

    values = {
        "timestamp": now_naive,
        "client_id": client_id,
        "ip_address": ip,
        "input_icao": input_icao,
        "resolved_icao": resolved_icao,
        "plane_profile": plane,
        "duration_seconds": duration,
        "status": status,
        "error_message": error_msg,
        "model_used": model,
        "tokens_used": tokens,
        "weather_icao": weather_icao,
        "expiration_timestamp": exp_naive,
        "t_wx": t_wx,
        "t_notams": t_notams,
        "t_ai": t_ai,
        "t_alt": t_alt
    }

    try:
        await database.execute(query=query, values=values)
        # Use logger but KEEP the exact emoji format
        logger.info(f"📝 LOGGED: {input_icao} | {status}") 
    except Exception as e:
        logger.error(f"❌ LOGGING FAILURE: {e}")