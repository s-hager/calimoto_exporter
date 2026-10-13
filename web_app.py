import argparse
import asyncio
import io
import os
import secrets
import time
import zipfile
from pathlib import Path
from typing import Dict, Optional

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from calimoto_client import CalimotoClient

STATIC_DIR = Path(__file__).resolve().parent / "static"
SESSION_COOKIE_NAME = "calimoto_session"
SESSION_TTL_SECONDS = 86400  # 24 hours


class UserSession:
    """Encapsulates an authenticated session for a single user."""

    def __init__(self, client: CalimotoClient):
        self.client = client
        self.cached_items: Dict[str, Dict[str, dict]] = {
            "routes": {},
            "tracks": {},
        }
        self.last_active = time.time()

    def touch(self):
        self.last_active = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TTL_SECONDS


# In-memory session store (isolated per user)
sessions: Dict[str, UserSession] = {}


def cleanup_expired_sessions():
    """Removes sessions that have exceeded the TTL."""
    expired = [token for token, session in sessions.items() if session.is_expired()]
    for token in expired:
        sessions.pop(token, None)


async def get_current_session(
    calimoto_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> UserSession:
    """Dependency that extracts and validates the active session."""
    cleanup_expired_sessions()
    if not calimoto_session or calimoto_session not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )
    session = sessions[calimoto_session]
    session.touch()
    return session


class LoginRequest(BaseModel):
    email: str
    password: str


app = FastAPI(title="Calimoto Exporter Web UI")


ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@app.get("/", response_class=FileResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web UI not found")
    return FileResponse(index_file)


@app.get("/icon.png", response_class=FileResponse)
async def serve_icon():
    icon_file = ASSETS_DIR / "icon.png"
    if icon_file.exists():
        return FileResponse(icon_file)
    raise HTTPException(status_code=404, detail="Icon not found")


@app.get("/flutter_service_worker.js")
async def handle_stale_flutter_worker():
    """Silently handles stale Flutter service worker checks from previous Flet web runs."""
    return Response(content="", media_type="application/javascript", status_code=200)


@app.post("/api/login")
async def login(req: LoginRequest, response: Response):
    """Authenticates against Calimoto and creates an isolated session."""
    client = CalimotoClient()
    client.set_credentials(req.email.strip(), req.password)

    try:
        success = await client.login()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {exc}",
        )

    # Issue session token
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = UserSession(client)

    # Secure HTTP-only cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )

    return {"success": True, "user_id": client.user_id}


@app.get("/api/me")
async def get_current_user(session: UserSession = Depends(get_current_session)):
    """Verifies whether the current user has a valid active session."""
    return {"logged_in": True, "user_id": session.client.user_id}


@app.post("/api/logout")
async def logout(
    response: Response,
    calimoto_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
):
    """Destroys the session and clears the cookie."""
    if calimoto_session in sessions:
        sessions.pop(calimoto_session, None)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"success": True}


@app.get("/api/items")
async def get_items(
    mode: str = "routes",
    session: UserSession = Depends(get_current_session),
):
    """Fetches routes or tracks for the logged-in user."""
    if mode not in ["routes", "tracks"]:
        raise HTTPException(status_code=400, detail="Mode must be 'routes' or 'tracks'")

    try:
        items = await session.client.get_items(mode)
        # Cache items for single download lookups
        session.cached_items[mode] = {it.get("objectId"): it for it in items if "objectId" in it}
        return items
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch {mode}: {exc}")


@app.get("/api/download")
async def download_gpx(
    id: str,
    mode: str = "routes",
    session: UserSession = Depends(get_current_session),
):
    """Generates and streams a single GPX file directly to the browser."""
    if mode not in ["routes", "tracks"]:
        raise HTTPException(status_code=400, detail="Mode must be 'routes' or 'tracks'")

    item = session.cached_items[mode].get(id)
    if not item:
        # Re-fetch items in case cache is empty
        items = await session.client.get_items(mode)
        session.cached_items[mode] = {it.get("objectId"): it for it in items if "objectId" in it}
        item = session.cached_items[mode].get(id)

    if not item:
        raise HTTPException(status_code=404, detail=f"{mode[:-1].capitalize()} not found")

    try:
        gpx_content = await session.client.get_gpx_content(item, mode)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generating GPX: {exc}")

    name = item.get("name", "Unnamed")
    safe_name = session.client.sanitize_filename(name)
    filename = f"{safe_name}_{mode[:-1]}.gpx"

    return Response(
        content=gpx_content,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/export-all")
async def export_all(
    session: UserSession = Depends(get_current_session),
):
    """Packages all routes and tracks into an in-memory ZIP archive and streams it."""
    try:
        routes = await session.client.get_items("routes")
        tracks = await session.client.get_items("tracks")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error loading items: {exc}")

    # Bounded concurrency to avoid overwhelming Calimoto rate limits
    semaphore = asyncio.Semaphore(5)

    async def fetch_item_gpx(item, mode):
        async with semaphore:
            try:
                content = await session.client.get_gpx_content(item, mode)
                return item, mode, content
            except Exception:
                return item, mode, None

    tasks = [fetch_item_gpx(r, "routes") for r in routes] + [
        fetch_item_gpx(t, "tracks") for t in tracks
    ]
    results = await asyncio.gather(*tasks)

    # Build ZIP archive in memory
    zip_buffer = io.BytesIO()
    seen_names = {"routes": set(), "tracks": set()}

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item, mode, gpx_content in results:
            if not gpx_content:
                continue

            raw_name = item.get("name", "Unnamed")
            safe_name = session.client.sanitize_filename(raw_name)
            filename = f"{safe_name}.gpx"
            count = 1
            while filename in seen_names[mode]:
                count += 1
                filename = f"{safe_name}_{count}.gpx"
            seen_names[mode].add(filename)

            zip_file.writestr(f"{mode}/{filename}", gpx_content)

    zip_bytes = zip_buffer.getvalue()
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="calimoto_export.zip"'},
    )


def main():
    parser = argparse.ArgumentParser(description="Calimoto Exporter Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
