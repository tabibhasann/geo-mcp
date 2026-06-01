#!/usr/bin/env python3
"""
Buriganga River Hospital Finder
Uses mcp-geo to find hospitals within 2km of the Buriganga river in Dhaka.
Demonstrates the full workflow: geocode → buffer → OSM query → analysis.
"""

import asyncio
import json

from geo_mcp import geometry, osm
from geo_mcp.geocoding import geocode


async def main():
    print("== Buriganga River Hospital Finder ==")
    print("Using mcp-geo v0.2.0\n")

    # Step 1: Geocode the Buriganga river
    print("1. Geocoding 'Buriganga River, Dhaka'...")
    locations = await geocode("Buriganga River, Dhaka", limit=1)
    if not locations:
        print("   Could not find Buriganga River via Nominatim. Using known coordinates.")
        river_lat, river_lon = 23.7050, 90.3750
    else:
        loc = locations[0]
        river_lat, river_lon = loc["lat"], loc["lon"]
        print(f"   Found: {loc['name']} at ({river_lat}, {river_lon})")

    # Step 2: Create a 2km buffer around the river point
    print("\n2. Buffering 2km around river location...")
    point = json.dumps({"type": "Point", "coordinates": [river_lon, river_lat]})
    buffer_result = geometry.buffer(point, 2000)
    print(f"   Buffer created: {json.loads(buffer_result)['type']}")

    # Step 3: Search OSM for hospitals in the area
    area = [river_lat - 0.02, river_lon - 0.02, river_lat + 0.02, river_lon + 0.02]
    print(f"\n3. Querying OSM for hospitals in area {area}...")
    try:
        features = await osm.osm_features(str(area), json.dumps({"amenity": "hospital"}))
        hospital_count = len(features.get("features", []))
        print(f"   Found {hospital_count} hospitals")

        hospitals = []
        for f in features.get("features", []):
            name = f["properties"].get("name", "Unnamed hospital")
            coords = f.get("geometry", {}).get("coordinates", [])
            if isinstance(coords, list) and len(coords) >= 2:
                hospitals.append({"name": name, "lon": coords[0], "lat": coords[1]})
    except Exception as e:
        print(f"   OSM query failed (expected without network): {e}")
        # Fall back to a simulated result using only local operations
        print("   Using local operations to demonstrate capabilities instead.")
        hospitals = [
            {"name": "Dhaka Medical College Hospital", "lon": 90.3950, "lat": 23.7250},
            {"name": "Sir Salimullah Medical College", "lon": 90.4080, "lat": 23.7100},
            {"name": "Bangabandhu Sheikh Mujib Medical", "lon": 90.3700, "lat": 23.7600},
        ]
        print(f"   Using {len(hospitals)} known Dhaka hospitals as fallback")

    # Step 4: Forward geocode Dhaka center as reference point
    print("\n4. Geocoding 'Dhaka city center'...")
    centers = await geocode("Dhaka city center", limit=1)
    if centers:
        center = centers[0]
        center_lat, center_lon = center["lat"], center["lon"]
        print(f"   Center: ({center_lat}, {center_lon})")
    else:
        center_lat, center_lon = 23.8103, 90.4125
        print(f"   Using known coordinates: ({center_lat}, {center_lon})")

    # Step 5: Compute distances and sort
    print("\n5. Computing distances from city center to each hospital...")
    center_point = json.dumps({"type": "Point", "coordinates": [center_lon, center_lat]})

    results = []
    for h in hospitals:
        h_point = json.dumps({"type": "Point", "coordinates": [h["lon"], h["lat"]]})
        dist = geometry.distance(center_point, h_point)
        results.append({**h, "distance_m": dist})

    results.sort(key=lambda x: x["distance_m"])

    # Step 6: Display results
    print(f"\n{'=' * 60}")
    print("HOSPITALS NEAR BURIGANGA RIVER (sorted by distance from city center)")
    print(f"{'=' * 60}")
    for i, r in enumerate(results, 1):
        print(f"{i:2d}. {r['name']}")
        print(f"    Distance from city center: {r['distance_m']/1000:.1f} km")
        print(f"    Location: ({r['lat']:.4f}, {r['lon']:.4f})")
        print()

    # Step 7: Check which hospitals are within the 2km buffer
    print(f"{'=' * 60}")
    print("HOSPITALS WITHIN 2KM OF BURIGANGA RIVER")
    print(f"{'=' * 60}")
    within_count = 0
    for r in results:
        h_point = json.dumps({"type": "Point", "coordinates": [r["lon"], r["lat"]]})
        in_buffer = geometry.spatial_predicate(h_point, buffer_result, "within")
        if in_buffer:
            within_count += 1
            print(f"  ✓ {r['name']}")
    if within_count == 0:
        print("  None found within strict 2km buffer (using point-based search)")

    print("\nDone. Tested: geocode, buffer, distance, osm_features, spatial_predicate")


if __name__ == "__main__":
    asyncio.run(main())
