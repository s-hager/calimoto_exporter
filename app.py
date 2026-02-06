import flet as ft
from calimoto_client import CalimotoClient
import asyncio
import os

async def main(page: ft.Page):
    page.title = "Calimoto GPX Exporter"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Client instance
    client = CalimotoClient()

    # UI Elements
    status_text = ft.Text("Ready", size=14, color=ft.Colors.GREY_400)
    
    def log(message):
        status_text.value = message
        page.update()
        print(message)

    client.log_callback = log
    await client.initialize()

    # Login View Elements
    email_input = ft.TextField(label="Email", width=300)
    password_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    login_button = ft.ElevatedButton("Login", width=300)

    # Dashboard Elements
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Routes"),
            ft.Tab(text="Tracks"),
        ],
        expand=1,
    )
    
    items_list = ft.ListView(expand=True, spacing=10)
    refresh_button = ft.IconButton(icon=ft.Icons.REFRESH)

    async def login_click(e):
        if not email_input.value or not password_input.value:
            log("Please enter email and password")
            return
            
        login_button.disabled = True
        page.update()
        
        success = await client.login(email_input.value, password_input.value)
        
        if success:
            log("Login successful!")
            page.clean()
            show_dashboard()
        else:
            log("Login failed. Check inputs.")
            login_button.disabled = False
            page.update()

    login_button.on_click = login_click

    async def download_item(item, mode):
        log(f"Downloading {item.get('name')}...")
        
        # We'll stick to saving in the current directory for now, 
        # as file pickers can be complex in async flet vs simple saving.
        # But let's try to grab the content and save it.
        
        name = item.get('name', 'Unnamed')
        safe_name = CalimotoClient.sanitize_filename(name)
        filename = f"{safe_name}_{mode[:-1]}.gpx"
        
        # In a real mobile app we might need to ask where to save, 
        # but for this POC saving to local dir is fine.
        result = await client.download_gpx(item, mode, output_file=filename)
        
        if result:
            log(f"Saved to {filename}")
            page.open(ft.SnackBar(content=ft.Text(f"Saved: {filename}"), open=True))
        else:
            log("Download failed")

    async def load_items(mode_name):
        items_list.controls.clear()
        items_list.controls.append(ft.ProgressBar(width=200))
        page.update()
        
        items = await client.get_items(mode_name)
        
        items_list.controls.clear()
        
        if not items:
            items_list.controls.append(ft.Text(f"No {mode_name} found."))
        else:
            # Sort by date
            def get_date(r):
                return r.get('createdAt') or r.get('timeCreated', {}).get('iso') or ""
            sorted_items = sorted(items, key=get_date, reverse=True)
            
            for item in sorted_items:
                name = item.get('name', 'Unnamed')
                date = get_date(item)[:10]
                dist = round(item.get('distance', 0) / 1000, 1)
                
                # Capture item and mode in closure for button
                # We need to use default args to bind current values
                # Define a closure for the click handler
                async def on_download_click(e):
                    # Extract data from the control
                    item_data = e.control.data["item"]
                    mode_data = e.control.data["mode"]
                    await download_item(item_data, mode_data)

                btn = ft.IconButton(
                    icon=ft.Icons.DOWNLOAD,
                    data={"item": item, "mode": mode_name},
                    on_click=on_download_click
                )
                
                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(name, weight="bold", size=16),
                                        ft.Text(f"{date} • {dist} km", size=12, color=ft.Colors.GREY_400),
                                    ],
                                    expand=True,
                                ),
                                btn
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    )
                )
                items_list.controls.append(card)
        
        page.update()
        log(f"Loaded {len(items)} {mode_name}")

    async def tab_change(e):
        mode = "routes" if tabs.selected_index == 0 else "tracks"
        await load_items(mode)

    tabs.on_change = tab_change

    def show_dashboard():
        page.add(
            ft.Row([ft.Text("Dashboard", size=24, weight="bold"), refresh_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            tabs,
            items_list,
            status_text
        )
        # Initial load
        asyncio.create_task(load_items("routes"))

    async def on_refresh_click(e):
        mode = "routes" if tabs.selected_index == 0 else "tracks"
        await load_items(mode)

    refresh_button.on_click = on_refresh_click

    # Attempt to pre-fill or auto-login
    client._load_credentials()
    if client.email:
        email_input.value = client.email
    if client.password:
        password_input.value = client.password

    # Show Login
    page.add(
        ft.Column(
            [
                ft.Text("Calimoto Exporter", size=30, weight="bold"),
                ft.Container(height=20),
                email_input,
                password_input,
                ft.Container(height=20),
                login_button,
                ft.Container(height=20),
                status_text,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
