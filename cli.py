import asyncio
import os
from calimoto_client import CalimotoClient

if __name__ == "__main__":
    async def main():
        async with CalimotoClient() as client:
            if not await client.login():
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
                        # Logic to determine filename is now partly in client, but we need to pass output path if we want control
                        # or rely on client returning content. The original script saved it.
                        # Let's recreate the filename logic here to pass it to the client, or let the client handle it.
                        # The client's download_gpx method now accepts an output_file. 
                        # If we want to replicate exact behavior:
                        
                        safe_name = CalimotoClient.sanitize_filename(name)
                        filename = f"{safe_name}_{mode[:-1]}.gpx"
                        
                        await client.download_gpx(item, mode, output_file=filename)
                        break
                except ValueError:
                    pass

    asyncio.run(main())
