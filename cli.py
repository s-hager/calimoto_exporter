import asyncio
import os
from calimoto_client import CalimotoClient

if __name__ == "__main__":
    async def main():
        async with CalimotoClient() as client:
            if not client.load_credentials_from_env_or_file():
                print("No credentials found in environment or .credentials file.")
                return

            if not await client.login():
                print("Login failed.")
                return

            print("\nSelect Mode:")
            print("[1] Routes (Planned)")
            print("[2] Tracks (Recorded via App)")
            
            mode = "routes"
            while True:
                choice = input("Enter choice (1 or 2): ").strip()
                if choice == "1":
                    mode = "routes"
                    break
                elif choice == "2":
                    mode = "tracks"
                    break

            print(f"Fetching {mode}...")
            items = await client.get_items(mode)
            if not items:
                print(f"No {mode} found.")
                return

            print(f"\nFound {len(items)} {mode}:")
            
            def get_date(r):
                return r.get('createdAt') or r.get('timeCreated', {}).get('iso') or ""
            
            sorted_items = sorted(items, key=get_date, reverse=True)

            for i, item in enumerate(sorted_items):
                name = item.get('name', 'Unnamed')
                date = get_date(item)[:10]
                dist_km = round(item.get('distance', 0) / 1000, 1)
                print(f"[{i+1}] {name} ({dist_km} km) - {date}")

            while True:
                try:
                    selection = input(f"\nSelect a {mode[:-1]} (1-{len(sorted_items)}): ")
                    idx = int(selection) - 1
                    if 0 <= idx < len(sorted_items):
                        item = sorted_items[idx]
                        name = item.get('name', 'Unnamed')
                        
                        safe_name = CalimotoClient.sanitize_filename(name)
                        filename = f"{safe_name}_{mode[:-1]}.gpx"
                        
                        print(f"Downloading {filename}...")
                        gpx_content = await client.get_gpx_content(item, mode)
                        
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(gpx_content)
                            
                        print(f"Successfully saved to {filename}")
                        break
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except Exception as e:
                    print(f"Error: {e}")
                    break

    asyncio.run(main())
