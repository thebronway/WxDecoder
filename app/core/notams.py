import httpx
import re

def clean_html(raw_text):
    if not raw_text: return ""
    text = re.sub(r'<br\s*/?>', '\n', raw_text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

async def get_notams(icao_code):
    if len(icao_code) == 3:
        icao_code = f"K{icao_code}"
        
    url = "https://notams.aim.faa.gov/notamSearch/search"
    payload = {
        "searchType": 0,
        "designatorsForLocation": icao_code,
        "notamsOnly": False,
        "radius": 0 
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (GoNoGo-AI)"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, data=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                notam_list = []
                if 'notamList' in data:
                    for item in data['notamList']:
                        raw_text = item.get('icaoMessage', 'N/A')
                        if raw_text:
                            clean_text = clean_html(raw_text)
                            if clean_text: 
                                notam_list.append(clean_text)
                
                return notam_list if notam_list else ["No active NOTAMs found."]
            else:
                print(f"FAA API Error: Status {response.status_code}")
                return [f"NOTAMs unavailable (FAA Source Error {response.status_code})."]

    except httpx.TimeoutException:
        print("FAA API Timeout")
        return ["NOTAMs unavailable (Connection Timeout)."]
    except Exception as e:
        print(f"NOTAM Scraping Error: {e}")
        return ["NOTAMs unavailable (System Error)."]