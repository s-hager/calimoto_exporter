import flet as ft
import asyncio
import base64
import json
from pathlib import Path

from calimoto_client import CalimotoClient

async def main(page: ft.Page):
    page.title = "Calimoto Exporter"
    page.window_icon = "icon.png"
    # page.theme_mode = ft.ThemeMode.DARK # will be adaptive
    page.padding = 20
    
    # Client instance
    client = CalimotoClient()
    
    class StatusText(ft.Text):
        def show_status(self, message):
            self.value = message
            self.color = None
            if self.page:
                self.update()

        def show_error(self, message, error=None):
            if error:
                self.value = f"{message}: {error}"
            else:
                self.value = message
            self.color = ft.Colors.RED
            if self.page:
                self.update()

        def clear(self):
            self.value = ""
            if self.page:
                self.update()
    
    # State
    current_items = []
    
    # Download state
    class DownloadState:
        content = None
        filename = None
        
    download_state = DownloadState()

    
    # Components
    
    # Function to clear session ( Logout )
    async def logout(e=None):
        # Clear session file
        try:
            session_file = Path.home() / ".calimoto_exporter_session"
            if session_file.exists():
                session_file.unlink()
        except Exception:
            pass
        
        # Clear client session
        client.session_token = None
        client.user_id = None
        
        # Clear UI (will be defined later)
        items_list.controls.clear()
        email_input.value = ""
        password_input.value = ""
        login_error.clear()
        
        # Show login screen (will be called later)
        show_login()

    # Check for stored session
    async def check_session():
        try:
            session_file = Path.home() / ".calimoto_exporter_session"
            if session_file.exists():
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                
                # Restore session data
                if session_data:
                    # Restore cookies if they exist
                    cookies = session_data.get("cookies", session_data)  # Backward compat
                    if cookies:
                        client.client.cookies.update(cookies)
                    
                    # Restore session token and user ID
                    client.session_token = session_data.get("session_token")
                    client.user_id = session_data.get("user_id")
                    client.installation_id = session_data.get("installation_id")
                    
                    # We still need API keys
                    try:
                        await client.initialize()
                        # Validate session by trying to fetch routes
                        await client.get_items("routes") 
                        # Session valid, show dashboard (which will load items and update status)
                        await show_dashboard()
                        return True
                    except Exception as ex:
                        # Session invalid or network error
                        print(f"Session restoration failed: {ex}")
                        await logout()
        except Exception as ex:
             print(f"Storage error: {ex}")
        return False



    # --- Login View ---
    email_input = ft.TextField(label="Email", width=300)
    password_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    login_error = StatusText()

    # Check if credentials exist in env/file to pre-fill
    if client.load_credentials_from_env_or_file():
        email_input.value = client.email
        password_input.value = client.password

    # We defer session check to after route setup
    
    async def handle_login(e):
        login_button.disabled = True
        login_error.show_status("Logging in...")
        page.update()
        
        email = email_input.value
        password = password_input.value
        
        # Set credentials on the client
        client.email = email
        client.password = password
        
        try:
            if await client.login():
                # Save session with all required data
                try:
                    session_data = {
                        "cookies": dict(client.client.cookies),
                        "session_token": client.session_token,
                        "user_id": client.user_id,
                        "installation_id": client.installation_id
                    }
                    session_file = Path.home() / ".calimoto_exporter_session"
                    with open(session_file, "w") as f:
                        json.dump(session_data, f)
                except Exception as ex:
                    print(f"Failed to save session: {ex}")
                
                # Show dashboard (will be defined later)
                await show_dashboard()
            else:
                login_error.show_error("Login failed", "Check credentials")
                login_button.disabled = False
                page.update()
        except Exception as ex:
            login_error.show_error("Login failed", str(ex))
            login_button.disabled = False
            page.update()

    login_button = ft.Button("Login", on_click=handle_login)
    
    login_view = ft.View(
        "/",
        [
            ft.Column(
                [
                    # ft.Text("Calimoto Exporter", size=30, weight=ft.FontWeight.BOLD, color="white"),
                    # ft.Text("Login to your account", size=16, color="white"),
                    ft.Text("Calimoto Exporter", size=30, weight=ft.FontWeight.BOLD),
                    ft.Text("Login to your account", size=16),
                    email_input,
                    password_input,
                    login_button,
                    login_error
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                expand=True
            )
        ],
        # bgcolor="#2196F3"  # Blue background
    )

    # --- Dashboard View ---
    
    items_list = ft.ListView(expand=True, spacing=10)
    status_text = StatusText()
    
    async def load_items(mode):
        status_text.show_status(f"Loading {mode}...")
        items_list.controls.clear()
        page.update()
        
        try:
            items = await client.get_items(mode)
            current_items = items
            
            # Sort by date
            def get_date(r):
                return r.get('createdAt') or r.get('timeCreated', {}).get('iso') or ""
            items.sort(key=get_date, reverse=True)
            
            for item in items:
                name = item.get('name', 'Unnamed')
                date_str = get_date(item)[:10]
                dist_km = round(item.get('distance', 0) / 1000, 1)

                def create_download_handler(item, mode):
                    async def handler(e):
                        await download_item(item, mode)
                    return handler
                
                # Create list tile
                tile = ft.Container(
                    content=ft.Row(
                        [
                            ft.Column([
                                ft.Text(name, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{date_str} • {dist_km} km", size=12, color=ft.Colors.GREY_400)
                            ], expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DOWNLOAD,
                                tooltip="Download GPX",
                                data=item,
                                on_click=create_download_handler(item, mode)
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=10,
                    border=ft.Border.all(1, ft.Colors.GREY_800),
                    border_radius=5,
                )
                items_list.controls.append(tile)
            
            status_text.show_status(f"Found {len(items)} {mode}")
            
        except Exception as ex:
            if "invalid session" in str(ex).lower() or "209" in str(ex):
                 status_text.show_error("Session expired", ex)
                 await asyncio.sleep(2)
                 await logout(None) # Pass None as event
            else:
                status_text.show_error("Error", ex)
        
        page.update()

    async def download_item(item, mode):
        try:
            name = item.get('name', 'Unnamed')
            safe_name = client.sanitize_filename(name)
            filename = f"{safe_name}_{mode[:-1]}.gpx"
            
            status_text.show_status(f"Downloading {filename}...")
            page.update()
            
            gpx_content = await client.get_gpx_content(item, mode)
            
            status_text.show_status(f"Select location to save {filename}...")
            page.update()
            
            # On Linux, this control requires Zenity when running Flet as a desktop app. It is not required when running Flet in a browser.
            path = await ft.FilePicker().save_file(
                file_name=filename, 
                allowed_extensions=["gpx"],
                src_bytes=gpx_content.encode('utf-8')
            )
            
            if path:
                status_text.show_status(f"Saved to {path}")
            else:
                status_text.show_status("Save cancelled")
            
        except Exception as ex:
            status_text.show_error("Download failed", ex)
        page.update()

    async def on_nav_change(e):
        mode = "routes" if e.control.selected_index == 0 else "tracks"
        await load_items(mode)

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=50,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.MAP, 
                selected_icon=ft.Icons.MAP_OUTLINED, 
                label="Routes"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DIRECTIONS_BIKE, 
                selected_icon=ft.Icons.DIRECTIONS_BIKE_OUTLINED, 
                label="Tracks"
            ),
        ],
        on_change=on_nav_change,
    )
     
    # Create dashboard controls
    dashboard_container = ft.Row(
        [
            nav_rail,
            ft.VerticalDivider(width=1),
            ft.Column(
                [
                    ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
                    ft.Button("Logout", on_click=logout, bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE),
                    status_text,
                    items_list
                ],
                expand=True,
                spacing=20
            )
        ],
        expand=True
    )
    
    # Create login controls  
    login_container = ft.Column(
        [
            ft.Text("Calimoto Exporter", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Login to your account", size=16),
            ft.Container(height=20),
            email_input,
            password_input,
            login_button,
            login_error
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        expand=True
    )
    
    # Main content container
    main_content = ft.Container(expand=True)
    
    def show_login():
        main_content.content = login_container
        page.update()
    
    async def show_dashboard():
        # Show dashboard UI first
        main_content.content = dashboard_container
        page.update()
        
        # Then load items
        if not items_list.controls:
            await load_items("routes")
        # Final update after loading
        page.update()
    
    # Setup page
    page.padding = 20
    page.add(main_content)
    
    # Start with login
    show_login()
    
    # Attempt to restore session
    await check_session()

ft.run(main, assets_dir="assets")
