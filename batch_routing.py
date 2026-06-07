#!/usr/bin/env python3
import asyncio
import csv
import math
import os
import random
import re
import sys
import argparse
from datetime import datetime

# Ensure we can import calimoto_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calimoto_client import CalimotoClient

def destination_point(lat, lon, distance_km, bearing_degrees):
    """
    Computes coordinates of a destination point given start point,
    distance in km, and bearing in degrees using the great-circle formula.
    """
    R = 6371.0  # Earth's radius in km
    bearing = math.radians(bearing_degrees)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    
    lat2 = math.asin(math.sin(lat1) * math.cos(distance_km / R) +
                     math.cos(lat1) * math.sin(distance_km / R) * math.cos(bearing))
    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(distance_km / R) * math.cos(lat1),
                             math.cos(distance_km / R) - math.sin(lat1) * math.sin(lat2))
    
    return math.degrees(lat2), math.degrees(lon2)

def generate_coordinate_pairs(num_pairs, min_dist=5.0, max_dist=100.0):
    """
    Generates random coordinate pairs within Central Europe/Austria region
    distanced between min_dist and max_dist km apart.
    """
    pairs = []
    # Centered around Salzburg region
    # Latitude: 47.0 to 48.5
    # Longitude: 12.5 to 16.5
    for i in range(num_pairs):
        start_lat = random.uniform(47.0, 48.5)
        start_lon = random.uniform(12.5, 16.5)
        distance = random.uniform(min_dist, max_dist)
        bearing = random.uniform(0.0, 360.0)
        
        end_lat, end_lon = destination_point(start_lat, start_lon, distance, bearing)
        pairs.append({
            "id": i + 1,
            "start_lat": start_lat,
            "start_lon": start_lon,
            "end_lat": end_lat,
            "end_lon": end_lon,
            "distance_km": round(distance, 2)
        })
    return pairs

def save_coordinates_csv(pairs, filename):
    """Saves the generated coordinate pairs to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "start_lat", "start_lon", "end_lat", "end_lon", "distance_km"])
        writer.writeheader()
        for p in pairs:
            writer.writerow(p)

async def route_with_retry(client, points, profile, max_retries=3):
    """Helper to perform routing with exponential backoff on failure."""
    backoff = 10.0
    for attempt in range(max_retries):
        try:
            return await client.get_routing_route(points=points, routing_profile=profile)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"  [Attempt {attempt+1}/{max_retries} Failed]: {e}. Retrying in {backoff:.1f}s...")
            await asyncio.sleep(backoff)
            backoff *= 2.0

async def main():
    parser = argparse.ArgumentParser(description="Batch Route Exporter using GraphHopper")
    parser.add_argument("--pairs", type=int, default=100, help="Number of coordinate pairs to generate (default: 100)")
    parser.add_argument("--min-delay", type=float, default=10.0, help="Minimum delay between requests in seconds (default: 10.0)")
    parser.add_argument("--max-delay", type=float, default=60.0, help="Maximum delay between requests in seconds (default: 60.0)")
    parser.add_argument("--output-dir", type=str, default="routes_gpx", help="Output directory for GPX files (default: routes_gpx)")
    parser.add_argument("--coords-file", type=str, default="routes_coordinates.csv", help="CSV file for storing coordinates (default: routes_coordinates.csv)")
    parser.add_argument("--resume", action="store_true", help="Resume an existing run using coordinates from the CSV file")
    
    args = parser.parse_args()

    # Create directories
    os.makedirs(args.output_dir, exist_ok=True)

    if args.resume:
        if not os.path.exists(args.coords_file):
            print(f"Error: Coordinates file '{args.coords_file}' not found. Cannot resume.")
            sys.exit(1)
        print(f"Resuming batch run using coordinates from {args.coords_file}...")
        pairs = []
        with open(args.coords_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pairs.append({
                    "id": int(row["id"]),
                    "start_lat": float(row["start_lat"]),
                    "start_lon": float(row["start_lon"]),
                    "end_lat": float(row["end_lat"]),
                    "end_lon": float(row["end_lon"]),
                    "distance_km": float(row["distance_km"])
                })
    else:
        print(f"Starting a new run. Generating {args.pairs} random start/end coordinates...")
        pairs = generate_coordinate_pairs(args.pairs)
        save_coordinates_csv(pairs, args.coords_file)
        print(f"Saved generated coordinates to {args.coords_file}")

    profiles = [
        "motorcycle",
        "motorcycle_fastest",
        "motorcycle_fastest_without_motorways",
        "motorcycle_extreme_winding"
    ]
    
    total_requests = len(pairs) * len(profiles)
    current_request = 0

    print(f"Starting batch routing for {len(pairs)} pairs across {len(profiles)} profiles ({total_requests} requests total)...")
    print(f"GPX files will be saved in directory: {args.output_dir}/")
    print("-" * 60)

    async with CalimotoClient() as client:
        for p in pairs:
            p_id = p["id"]
            p_id_str = f"{p_id:03d}"
            points = [
                (p["start_lat"], p["start_lon"]),
                (p["end_lat"], p["end_lon"])
            ]
            
            print(f"\n[Route Pair {p_id}/{len(pairs)}]: ({p['start_lat']:.6f}, {p['start_lon']:.6f}) -> ({p['end_lat']:.6f}, {p['end_lon']:.6f}) [{p['distance_km']:.1f} km]")
            
            for profile in profiles:
                current_request += 1
                gpx_filename = f"route_{p_id_str}_{profile}.gpx"
                gpx_path = os.path.join(args.output_dir, gpx_filename)
                
                # Check if file already exists (to resume/skip in case of manual restarts)
                if args.resume and os.path.exists(gpx_path):
                    print(f"  [{current_request}/{total_requests}] Skipping {gpx_filename} (already exists)")
                    continue
                
                print(f"  [{current_request}/{total_requests}] Fetching route for profile: {profile}...")
                
                try:
                    decoded_points = await route_with_retry(client, points, profile)
                    gpx_content = client._convert_to_gpx(decoded_points, f"Route {p_id_str} - {profile}")
                    
                    with open(gpx_path, "w", encoding="utf-8") as f:
                        f.write(gpx_content)
                    print(f"    Saved {len(decoded_points)} points to {gpx_path}")
                except Exception as e:
                    print(f"    [Error] Failed to fetch route for {gpx_filename}: {e}")

                # Optional delay between requests (skip delay on very last request)
                if current_request < total_requests:
                    delay = random.uniform(args.min_delay, args.max_delay)
                    print(f"    Waiting {delay:.1f}s before next request...")
                    await asyncio.sleep(delay)

    print("\nBatch routing run completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBatch routing run aborted by user.")
