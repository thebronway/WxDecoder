import asyncio
import httpx
from app.core.notifications import notifier
from app.core.ai import client as ai_client
from app.core.db import database

async def check_faa():
    try:
        url = "https://aviationweather.gov/api/data/metar?ids=KJFK"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and "KJFK" in resp.text:
                return True
    except: pass
    return False

async def check_openai():
    try:
        await ai_client.models.list()
        return True
    except: pass
    return False

async def run_probes():
    """
    Runs periodically in background.
    - Health checks every 15 mins.
    - Surgical Cache cleanup and Log pruning once per hour at :51.
    """
    import datetime
    from app.core.cache import clear_expired_cache

    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # 1. SURGICAL CLEANUP
        # Only run at :51 past the hour (after METARs typically update)
        if now.minute == 59:
            await clear_expired_cache()
            # Clean logs older than 90 days
            try:
                await database.execute("DELETE FROM logs WHERE timestamp < NOW() - INTERVAL '90 days'")
            except Exception as e:
                print(f"LOG CLEANUP ERROR: {e}")

        # 2. API HEALTH CHECKS
        # Run every 15 minutes (0, 15, 30, 45)
        if now.minute % 15 == 0:
            if not await check_faa():
                await notifier.send_alert("api_outage", "FAA API Down", "The AviationWeather API is failing to respond.")
            
            if not await check_openai():
                await notifier.send_alert("api_outage", "OpenAI API Down", "Cannot connect to OpenAI API.")

        # Sleep for 60 seconds to check again the next minute
        await asyncio.sleep(60)