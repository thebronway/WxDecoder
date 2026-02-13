import json
import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.db import database
from app.core.weather import get_metar_taf
from app.api.endpoints.admin import get_admin_key

router = APIRouter()

# --- PUBLIC KIOSK ENDPOINTS ---

@router.get("/config/{slug}")
async def get_kiosk_config(slug: str):
    """
    Fetches Kiosk Profile by Slug.
    """
    slug_key = slug.lower().strip()
    query = "SELECT * FROM kiosk_profiles WHERE slug = :slug AND is_active = 1"
    row = await database.fetch_one(query, values={"slug": slug_key})
    
    if not row:
        raise HTTPException(status_code=404, detail="Kiosk Profile Not Found")
        
    return {
        "slug": row['slug'],
        "target_icao": row['target_icao'],
        "weather_override_icao": row['weather_override_icao'],
        "title_override": row['title_override'],
        "default_profile": row['default_profile'],
        "subscriber_name": row['subscriber_name'],
        "config": json.loads(row['config_options'] or '{}')
    }

@router.get("/peek/{icao}")
async def peek_weather(icao: str, source: str = None):
    """
    Lightweight poller. 
    If 'source' is provided (Weather Override), checks that. 
    Otherwise checks target icao.
    """
    target = source.upper().strip() if source else icao.upper().strip()
    
    data = await get_metar_taf(target)
    
    if not data or not data['metar']:
        return {"status": "unavailable", "raw_metar": None}
        
    return {
        "status": "success",
        "raw_metar": data['metar']
    }

# --- ADMIN MANAGEMENT ENDPOINTS ---

class KioskProfileRequest(BaseModel):
    slug: str
    target_icao: str
    weather_override_icao: Optional[str] = None
    title_override: Optional[str] = None
    default_profile: str = "small"
    subscriber_name: str

@router.get("/list", dependencies=[Depends(get_admin_key)])
async def list_kiosks():
    query = "SELECT * FROM kiosk_profiles ORDER BY created_at DESC"
    rows = await database.fetch_all(query)
    return [dict(r) for r in rows]

@router.post("/add", dependencies=[Depends(get_admin_key)])
async def add_kiosk(data: KioskProfileRequest):
    slug_key = data.slug.lower().strip().replace(" ", "-")
    
    query = """
        INSERT INTO kiosk_profiles (slug, target_icao, weather_override_icao, title_override, default_profile, subscriber_name, is_active)
        VALUES (:slug, :target, :wx_src, :title, :def, :sub, 1)
        ON CONFLICT (slug) DO UPDATE SET
        target_icao = :target,
        weather_override_icao = :wx_src,
        title_override = :title,
        default_profile = :def,
        subscriber_name = :sub,
        is_active = 1
    """
    values = {
        "slug": slug_key,
        "target": data.target_icao.upper(),
        "wx_src": data.weather_override_icao.upper() if data.weather_override_icao else None,
        "title": data.title_override,
        "def": data.default_profile,
        "sub": data.subscriber_name
    }
    await database.execute(query, values)
    return {"status": "success"}

@router.delete("/remove/{slug}", dependencies=[Depends(get_admin_key)])
async def remove_kiosk(slug: str):
    query = "DELETE FROM kiosk_profiles WHERE slug = :slug"
    await database.execute(query, values={"slug": slug.lower().strip()})
    return {"status": "success"}