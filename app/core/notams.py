import httpx
import re

def clean_html(raw_text):
    """
    Removes HTML tags and cleans up spacing.
    """
    if not raw_text:
        return ""
    
    # 1. Replace <br> variants with a newline
    text = re.sub(r'<br\s*/?>', '\n', raw_text, flags=re.IGNORECASE)
    
    # 2. Remove all other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # 3. Collapse multiple newlines into one
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # 4. Collapse multiple spaces into one
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

async def get_notams(icao_code):
    """
    Async version of the NOTAM fetcher.
    """
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
        "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
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
                return [f"FAA Portal Error (Status {response.status_code})."]
        except Exception as e:
            return [f"Connection Error: {e}"]