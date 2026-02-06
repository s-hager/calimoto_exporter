import asyncio
import json
import re
import os
import uuid
import aiohttp
from datetime import datetime, timedelta

# Configuration
CREDENTIALS_FILE = '.credentials'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

class CalimotoClient:
    def __init__(self, log_callback=None):
        self.email = None
        self.password = None
        self.app_id = None
        self.js_key = None
        self.session_token = None
        self.user_id = None
        self.installation_id = None
        self.session = None
        self.log_callback = log_callback

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    async def __aenter__(self):
        await self.initialize()
        return self

    async def initialize(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers={'User-Agent': USER_AGENT})
        self._load_credentials()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _load_credentials(self):
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
                self.log(f"Warning: Could not read credentials file: {e}")
        
        # We don't raise here, to allow the UI to handle missing credentials if needed
        # but the original script raised. Let's keep it lenient for the class.
        if not self.email or not self.password:
             self.log("Warning: Credentials missing in environment or file.")

    async def _extract_keys(self):
        self.log("Extracting Parse keys from scripts...")
        base_url = "https://calimoto.com"
        start_url = f"{base_url}/en/motorcycle-trip-planner"
        
        try:
            async with self.session.get(start_url) as response:
                if response.status != 200:
                    self.log(f"Failed to load homepage: {response.status}")
                    return False
                html = await response.text()
                
            script_urls = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
            target_scripts = [s for s in script_urls if s.startswith('/') or s.startswith(base_url)]
            target_scripts = [s if s.startswith('http') else base_url + s for s in target_scripts]
            target_scripts = list(set(target_scripts))
            
            found = False
            
            async def scan_script(url):
                nonlocal found
                if found: return
                try:
                    async with self.session.get(url) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            regex = r"appId\s*:\s*['\"]([^'\"]+)['\"]\s*,\s*key\s*:\s*['\"]([^'\"]+)['\"]"
                            match = re.search(regex, text)
                            if match:
                                self.app_id = match.group(1)
                                self.js_key = match.group(2)
                                found = True
                except Exception:
                    pass

            tasks = [scan_script(url) for url in target_scripts]
            await asyncio.gather(*tasks)
            return bool(self.app_id and self.js_key)

        except Exception as e:
            self.log(f"Error extracting keys: {e}")
            return False

    async def login(self, email=None, password=None):
        if email: self.email = email
        if password: self.password = password

        if not self.email or not self.password:
            self.log("Error: No credentials provided.")
            return False

        if not await self._extract_keys():
            self.log("Critical Error: Could not extract Parse keys.")
            return False

        if not self.installation_id:
            self.installation_id = str(uuid.uuid4())

        self.log(f"Logging in directly via API as {self.email}...")
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
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.user_id = data.get('objectId')
                    self.session_token = data.get('sessionToken')
                    self.log(f"Login successful! User ID: {self.user_id}")
                    return True
                else:
                    self.log(f"Login Error {response.status}: {await response.text()}")
                    return False
        except Exception as e:
            self.log(f"Login request failed: {e}")
            return False

    async def _handle_auth_error(self):
        self.log("Session expired or invalid (Error 209/401). Retrying login...")
        self.session_token = None
        return await self.login()

    async def get_items(self, mode="routes", retry=True):
        if not self.user_id or not self.session_token:
            self.log("Not logged in.")
            return []

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

        self.log(f"Fetching {mode} for user {self.user_id}...")
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    return data.get("results", [])
                elif response.status in [400, 401, 403]:
                    text = await response.text()
                    if "209" in text or "invalid session" in text.lower():
                        if retry and await self._handle_auth_error():
                            return await self.get_items(mode, retry=False)
                    self.log(f"API Error {response.status}: {text}")
                    return []
                else:
                    self.log(f"API Error {response.status}: {await response.text()}")
                    return []
        except Exception as e:
            self.log(f"Request failed: {e}")
            return []

    async def download_gpx(self, item, mode="routes", output_file=None):
        name = item.get('name', 'Unnamed')
        points_url = item.get('points', {}).get('url')
        
        if not points_url:
            self.log("No points URL found.")
            return None

        try:
            self.log(f"Fetching points from {points_url}...")
            # Fetch points
            async with self.session.get(points_url) as r:
                points_data = await r.json(content_type=None)
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
                    except Exception as e:
                        self.log(f"Warning: Could not parse start date: {e}")

                if alt_url:
                    self.log(f"Fetching altitudes from {alt_url}...")
                    async with self.session.get(alt_url) as r:
                        alt_data = await r.json(content_type=None)
                        altitudes = alt_data.get("altitudes", [])
                
                if date_url:
                    self.log(f"Fetching dates from {date_url}...")
                    async with self.session.get(date_url) as r:
                        date_data = await r.json(content_type=None)
                        timestamps = date_data.get("dates", [])
                        
                if speed_url:
                    self.log(f"Fetching speeds from {speed_url}...")
                    async with self.session.get(speed_url) as r:
                        speed_data = await r.json(content_type=None)
                        speeds = speed_data.get("speeds", [])

            if points:
                gpx_content = self._convert_to_gpx(points, name, altitudes, timestamps, speeds, start_date)
                
                if output_file:
                    with open(output_file, "w", encoding='utf-8') as f:
                        f.write(gpx_content)
                    self.log(f"SUCCESS: GPX file saved to {os.path.abspath(output_file)}")
                    return output_file
                else:
                    return gpx_content
            else:
                self.log("Invalid points data format received.")
                return None

        except Exception as e:
            self.log(f"Error fetching/saving GPX: {e}")
            return None

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
