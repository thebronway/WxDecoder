import json
import datetime
from app.core.db import database

TTL_SECONDS = 30 * 60

def get_plane_category(plane_input: str) -> str:
    p = plane_input.lower().strip()
    if any(x in p for x in ['boeing', 'airbus', '737', '747', 'a320', 'gulfstream', 'global', 'crj', 'erj']):
        return "LARGE"
    if any(x in p for x in ['king air', 'pilatus', 'pc-12', 'citation', 'phenom', 'learjet', 'tbm']):
        return "MEDIUM"
    return "SMALL"

async def get_cached_report(icao: str, plane_input: str):
    category = get_plane_category(plane_input)
    cache_key = f"{icao.upper()}_{category}"
    
    query = "SELECT * FROM flight_cache WHERE key = :key"
    row = await database.fetch_one(query=query, values={"key": cache_key})
    
    if not row:
        return None
        
    stored_time = row['timestamp']
    
    # Handle naive/aware mismatch
    if stored_time.tzinfo is None:
        now = datetime.datetime.utcnow()
    else:
        now = datetime.datetime.now(datetime.timezone.utc)
        
    age = (now - stored_time).total_seconds()
    
    if age > TTL_SECONDS:
        return None 
        
    return json.loads(row['data'])

async def save_cached_report(icao: str, plane_input: str, data: dict):
    category = get_plane_category(plane_input)
    cache_key = f"{icao.upper()}_{category}"
    
    query = """
        INSERT INTO flight_cache (key, icao, category, timestamp, data)
        VALUES (:key, :icao, :category, :ts, :data)
        ON CONFLICT (key) DO UPDATE 
        SET timestamp = :ts, data = :data
    """
    
    values = {
        "key": cache_key,
        "icao": icao.upper(),
        "category": category,
        # FIX: Send naive UTC to match Postgres
        "ts": datetime.datetime.utcnow(),
        "data": json.dumps(data)
    }
    
    await database.execute(query, values)