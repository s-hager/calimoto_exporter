import asyncio
import json
import re
import os
import uuid
import httpx
from datetime import datetime, timedelta

# Configuration
CREDENTIALS_FILE = '.credentials'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

class CalimotoClient:
    def __init__(self):
        self.email = None
        self.password = None
        self.app_id = None
        self.js_key = None
        self.session_token = None
        self.user_id = None
        self.installation_id = None
        self.client = httpx.AsyncClient(headers={'User-Agent': USER_AGENT}, follow_redirects=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def load_credentials_from_env_or_file(self):
        """Loads credentials, returning True if found, False otherwise."""
        self.email = os.environ.get('CALIMOTO_USERNAME')
        self.password = os.environ.get('CALIMOTO_PASSWORD')

        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    if os.path.getsize(CREDENTIALS_FILE) > 0:
                        data = json.load(f)
                        self.email = data.get('email', self.email)
                        self.password = data.get('password', self.password)
            except Exception as e:
                pass # Silent fail, let the caller handle missing creds if needed

        return bool(self.email and self.password)

    def set_credentials(self, email, password):
        self.email = email
        self.password = password

    async def initialize(self):
        return await self._extract_keys()

    async def _extract_keys(self):
        if self.app_id and self.js_key:
            return True

        base_url = "https://calimoto.com"
        start_url = f"{base_url}/en/motorcycle-trip-planner"
        
        try:
            response = await self.client.get(start_url)
            if response.status_code != 200:
                raise Exception(f"Failed to load homepage: {response.status_code}")
            html = response.text
                
            script_urls = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
            target_scripts = [s for s in script_urls if s.startswith('/') or s.startswith(base_url)]
            target_scripts = [s if s.startswith('http') else base_url + s for s in target_scripts]
            target_scripts = list(set(target_scripts))
            
            found = False
            
            async def scan_script(url):
                nonlocal found
                if found: return
                try:
                    resp = await self.client.get(url)
                    if resp.status_code == 200:
                        text = resp.text
                        regex = r"appId\s*:\s*['\"]([^'\"]+)['\"]\s*,\s*key\s*:\s*['\"]([^'\"]+)['\"]"
                        match = re.search(regex, text)
                        if match:
                            self.app_id = match.group(1)
                            self.js_key = match.group(2)
                            found = True
                except Exception:
                    pass

            # httpx is async but we need to run these concurrently
            # standard asyncio.gather works with coroutines
            tasks = [scan_script(url) for url in target_scripts]
            await asyncio.gather(*tasks)
            return bool(self.app_id and self.js_key)

        except Exception as e:
            raise Exception(f"Error extracting keys: {e}")

    async def login(self):
        if not self.email or not self.password:
             raise ValueError("Credentials not set.")

        if not await self.initialize():
            raise Exception("Could not extract Parse keys from calimoto.com")

        if not self.installation_id:
            self.installation_id = str(uuid.uuid4())

        url = "https://parse-server.prod.calimoto.com/parse/login"
        headers = {
            'Content-Type': 'text/plain',
            'Origin': 'https://calimoto.com',
            'Referer': 'https://calimoto.com/',
        }
        payload = {
            "username": self.email,
            "password": self.password,
            "_ApplicationId": self.app_id,
            "_JavaScriptKey": self.js_key,
            "_ClientVersion": "js5.3.0",
            "_InstallationId": self.installation_id
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get('objectId')
                self.session_token = data.get('sessionToken')
                return True
            else:
                raise Exception(f"Login Error {response.status_code}: {response.text}")
        except Exception as e:
            raise e

    async def _handle_auth_error(self):
        self.session_token = None
        return await self.login()

    async def get_items(self, mode="routes", retry=True):
        """Returns a list of items (routes or tracks)."""
        class_name = "tblRoutes" if mode == "routes" else "tblTracks"
        url = f"https://parse-server.prod.calimoto.com/parse/classes/{class_name}"
        headers = {'Content-Type': 'text/plain'}
        payload = {
            "where": {"userId": self.user_id},
            "include": "pictures",
            "limit": 10000,
            "_method": "GET",
            "_ApplicationId": self.app_id,
            "_JavaScriptKey": self.js_key,
            "_ClientVersion": "js5.3.0",
            "_SessionToken": self.session_token,
            "_InstallationId": self.installation_id
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            elif response.status_code in [400, 401, 403]:
                text = response.text
                if "209" in text or "invalid session" in text.lower():
                    if retry and await self._handle_auth_error():
                        return await self.get_items(mode, retry=False)
                raise Exception(f"API Error {response.status_code}: {text}")
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            raise e

    async def get_gpx_content(self, item, mode="routes"):
        """Fetches data and returns the GPX string content."""
        name = item.get('name', 'Unnamed')
        points_url = item.get('points', {}).get('url')
        
        if not points_url:
            raise ValueError("No points URL found.")

        # Fetch points
        response = await self.client.get(points_url)
        points_data = response.json()
        points = points_data.get("points", [])

        altitudes = []
        timestamps = []
        speeds = []
        start_date = None

        # For tracks, fetch extra data
        if mode == "tracks":
            alt_url = item.get('altitudes', {}).get('url')
            date_url = item.get('dates', {}).get('url')
            speed_url = item.get('speeds', {}).get('url')
            
            # Parse base time
            created_at = item.get('timeCreated', {}).get('iso')
            if created_at:
                try:
                    start_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except Exception:
                    pass

            if alt_url:
                r = await self.client.get(alt_url)
                alt_data = r.json()
                altitudes = alt_data.get("altitudes", [])
            
            if date_url:
                r = await self.client.get(date_url)
                date_data = r.json()
                timestamps = date_data.get("dates", [])
                    
            if speed_url:
                r = await self.client.get(speed_url)
                speed_data = r.json()
                speeds = speed_data.get("speeds", [])

        if points:
            return self._convert_to_gpx(points, name, altitudes, timestamps, speeds, start_date)
        else:
            raise ValueError("Invalid points data format received.")

    @staticmethod
    def sanitize_filename(name):
        # Handle navigation arrows as requested (-> for →, <-> for ⇄)
        name = name.replace('→', '->').replace('⇄', '<->')
        
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        
        # Remove truly unsafe characters for Linux filesystems (mainly / and null)
        # We also replace backslashes just in case
        name = name.replace('/', '_').replace('\\', '_')
        
        # Remove non-printable characters
        safe_name = "".join(c for c in name if c.isprintable())
        
        # Collapse multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        return safe_name.strip('_')

    @staticmethod
    def _convert_to_gpx(points, name, altitudes=None, timestamps=None, speeds=None, start_date=None):
        
        gpx_header = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Calimoto Route Exporter" 
    xmlns="http://www.topografix.com/GPX/1/1"
    xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd
    http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd">
  <trk>
    <name>{name}</name>
    <trkseg>"""
        
        gpx_points = ""
        for i, (lat, lon) in enumerate(points):
            ele = ""
            time = ""
            extensions = ""
            
            if altitudes and i < len(altitudes):
                ele = f"<ele>{altitudes[i]}</ele>"
            
            if timestamps and i < len(timestamps) and start_date:
                # Add milliseconds offset to start_date
                ms_offset = timestamps[i]
                point_time = start_date + timedelta(milliseconds=ms_offset)
                time = f"<time>{point_time.isoformat()}</time>"

            if speeds and i < len(speeds):
                # Speed is already in m/s
                extensions = f"""
        <extensions>
          <gpxtpx:TrackPointExtension>
            <gpxtpx:speed>{speeds[i]}</gpxtpx:speed>
          </gpxtpx:TrackPointExtension>
        </extensions>"""

            gpx_points += f'      <trkpt lat="{lat}" lon="{lon}">{ele}{time}{extensions}\n      </trkpt>\n'
        
        gpx_footer = """    </trkseg>
  </trk>
</gpx>"""
        return gpx_header + "\n" + gpx_points + gpx_footer
