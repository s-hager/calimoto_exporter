import asyncio
import os
from calimoto_client import CalimotoClient

if __name__ == "__main__":
    async def main():
        async with CalimotoClient() as client:
            print("\nSelect Mode:")
            print("[1] Routes (Planned)")
            print("[2] Tracks (Recorded via App)")
            print("[3] Route Planner (GraphHopper)")
            
            mode = "routes"
            while True:
                choice = input("Enter choice (1, 2, or 3): ").strip()
                if choice == "1":
                    mode = "routes"
                    break
                elif choice == "2":
                    mode = "tracks"
                    break
                elif choice == "3":
                    mode = "graphhopper"
                    break

            if mode == "graphhopper":
                print("\nGraphHopper Route Planner:")
                print("[1] Import from GraphHopper URL (from browser dev tools network tab)")
                print("[2] Enter coordinates manually")
                
                gh_choice = ""
                while True:
                    gh_choice = input("Enter choice (1 or 2): ").strip()
                    if gh_choice in ["1", "2"]:
                        break
                
                points = None
                url = None
                profile = "motorcycle"
                
                if gh_choice == "1":
                    url = input("\nPaste GraphHopper URL: ").strip()
                    if not url:
                        print("URL cannot be empty.")
                        return
                else:
                    print("\nEnter coordinates (latitude,longitude), one per line.")
                    print("Example: 47.800333,13.045415")
                    print("Press Enter on an empty line when finished.")
                    
                    coords = []
                    while True:
                        line = input(f"Point {len(coords)+1}: ").strip()
                        if not line:
                            if len(coords) < 2:
                                print("At least 2 points are required.")
                                continue
                            break
                        try:
                            lat_str, lon_str = line.split(",")
                            coords.append((float(lat_str.strip()), float(lon_str.strip())))
                        except ValueError:
                            print("Invalid format. Use 'latitude,longitude' (e.g. 47.800333,13.045415)")
                    
                    points = coords
                    
                    print("\nSelect routing profile:")
                    print("[1] motorcycle (winding) [default]")
                    print("[2] motorcycle_fastest")
                    print("[3] motorcycle_fastest_without_motorways")
                    print("[4] motorcycle_extreme_winding")
                    
                    profile_choice = input("Enter choice (1-4): ").strip()
                    if profile_choice == "2":
                        profile = "motorcycle_fastest"
                    elif profile_choice == "3":
                        profile = "motorcycle_fastest_without_motorways"
                    elif profile_choice == "4":
                        profile = "motorcycle_extreme_winding"
                    else:
                        profile = "motorcycle"

                        
                print("\nCalculating/Fetching route...")
                try:
                    decoded_points = await client.get_routing_route(url=url, points=points, routing_profile=profile)
                    
                    # Generate GPX file name
                    default_filename = "graphhopper_route.gpx"
                    filename = input(f"Enter output filename [default: {default_filename}]: ").strip()
                    if not filename:
                        filename = default_filename
                    if not filename.endswith(".gpx"):
                        filename += ".gpx"
                        
                    gpx_content = client._convert_to_gpx(decoded_points, "GraphHopper Route")
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(gpx_content)
                        
                    print(f"Successfully saved {len(decoded_points)} points to {filename}")
                except Exception as e:
                    print(f"Error: {e}")
                return

            if not client.load_credentials_from_env_or_file():
                print("No credentials found in environment or .credentials file.")
                return

            if not await client.login():
                print("Login failed.")
                return

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
