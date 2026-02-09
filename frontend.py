import flet as ft
import asyncio
import base64

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
    
    # Download state (since FilePicker is async)
    class DownloadState:
        content = None
        filename = None
        
    download_state = DownloadState()
    
    def on_save_result(e: ft.FilePickerResultEvent):
        # Note: on desktop, save_file only returns the path. We must write the file manually.
        if e.path:
            try:
                with open(e.path, "w", encoding="utf-8") as f:
                    f.write(download_state.content)
                status_text.show_status(f"Saved to {e.path}")
            except Exception as ex:
                status_text.show_error(f"Failed to save to {e.path}", ex)
            finally:
                download_state.content = None # Clear memory
        else:
            status_text.show_status("Save cancelled")
            download_state.content = None # Clear memory
            
    file_picker = ft.FilePicker(on_result=on_save_result)
    page.overlay.append(file_picker)

    
    # Components
    
    # --- Login View ---
    email_input = ft.TextField(label="Email", width=300)
    password_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    login_error = StatusText()
    
    async def handle_login(e):
        login_button.disabled = True
        login_error.show_status("Logging in...")
        
        client.set_credentials(email_input.value, password_input.value)
        try:
            await client.login()
            page.go("/dashboard")
        except Exception as ex:
            login_error.show_error("Login failed", ex)
            login_button.disabled = False
            page.update()

    login_button = ft.ElevatedButton("Login", on_click=handle_login)
    
    login_view = ft.View(
        "/",
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Calimoto Exporter", size=30, weight=ft.FontWeight.BOLD),
                        ft.Text("Login to your account", size=16),
                        email_input,
                        password_input,
                        login_button,
                        login_error
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        ]
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
                    border=ft.border.all(1, ft.Colors.GREY_800),
                    border_radius=5,
                )
                items_list.controls.append(tile)
            
            status_text.show_status(f"Found {len(items)} {mode}")
            
        except Exception as ex:
            status_text.show_error("Error", ex)
        
        page.update()

    async def download_item(item, mode):
        try:
            name = item.get('name', 'Unnamed')
            safe_name = client.sanitize_filename(name)
            filename = f"{safe_name}_{mode[:-1]}.gpx"
            
            status_text.show_status(f"Downloading {filename}...")
            
            gpx_content = await client.get_gpx_content(item, mode)
            
            # Prepare content for download handler
            download_state.content = gpx_content
            download_state.filename = filename 
            
            file_picker.save_file(file_name=filename, allowed_extensions=["gpx"])
            status_text.show_status(f"Select location to save {filename}...")
            
        except Exception as ex:
            status_text.show_error("Download failed", ex)
        page.update()

    async def on_nav_change(e):
        mode = "routes" if e.control.selected_index == 0 else "tracks"
        await load_items(mode)

    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
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
    
    dashboard_view = ft.View(
        "/dashboard",
        [
            ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        [
                            ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
                            status_text,
                            items_list
                        ],
                        expand=True,
                        spacing=20
                    )
                ],
                expand=True
            )
        ]
    )

    async def route_change(route):
        page.views.clear()
        page.views.append(login_view)
        if page.route == "/dashboard":
            page.views.append(dashboard_view)
            # Initial load
            if not items_list.controls:
                 await load_items("routes")
        page.update()

    async def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Check if credentials exist in env/file to pre-fill
    if client.load_credentials_from_env_or_file():
        email_input.value = client.email
        password_input.value = client.password

    page.go(page.route)

ft.app(target=main, assets_dir="assets")
