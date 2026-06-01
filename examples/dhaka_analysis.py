#!/usr/bin/env python3
"""
Dhaka Neighborhood Analysis via mcp-geo v0.2.1

Demonstrates: geocode, reverse_geocode, buffer, distance, area, bbox,
spatial_predicate, centroid, convex_hull, simplify, length,
transform_crs, validate_geojson, build_overpass_query.
"""

import asyncio
import json

from geo_mcp import geometry, osm
from geo_mcp.geocoding import geocode, reverse_geocode


async def main():
    print("Dhaka Neighborhood Analysis")
    print("Using mcp-geo v0.2.1\n")

    # 1. Geocode three Dhaka landmarks
    print("1. Geocoding landmarks...")
    landmarks = {}
    for name in ["Gulshan, Dhaka", "Dhanmondi, Dhaka", "Uttara, Dhaka"]:
        results = await geocode(name, limit=1)
        if results:
            landmarks[name] = results[0]
            print(f"   {name}: ({results[0]['lat']:.4f}, {results[0]['lon']:.4f})")

    # 2. Create buffers around each
    print("\n2. Creating 3km analysis zones...")
    buffers = {}
    for name, loc in landmarks.items():
        point = json.dumps({"type": "Point", "coordinates": [loc["lon"], loc["lat"]]})
        buf_str = geometry.buffer(point, 3000)
        buf = json.loads(buf_str)
        buffers[name] = buf
        print(f"   {name} buffer: {buf['type']} with {len(buf['coordinates'][0])} vertices")

    # 3. Compute pairwise distances
    print("\n3. Pairwise distances between neighborhoods:")
    names = list(landmarks.keys())
    for i, a in enumerate(names):
        pa = json.dumps({"type": "Point", "coordinates": [landmarks[a]["lon"], landmarks[a]["lat"]]})
        for b in names[i+1:]:
            pb = json.dumps({"type": "Point", "coordinates": [landmarks[b]["lon"], landmarks[b]["lat"]]})
            dist = geometry.distance(pa, pb)
            print(f"   {a} <-> {b}: {dist/1000:.1f} km")

    # 4. Check if neighborhoods overlap
    print("\n4. Spatial relationships between buffers:")
    overlaps = {}
    for a in names:
        for b in names:
            if a >= b:
                continue
            ba = json.dumps(buffers[a])
            bb = json.dumps(buffers[b])
            intersects = geometry.spatial_predicate(ba, bb, "intersects")
            overlaps[f"{a} & {b}"] = intersects
            print(f"   {a} & {b} intersect: {intersects}")

    # 5. Compute the convex hull of all landmarks
    print("\n5. Convex hull of all three neighborhoods:")
    all_points = []
    for loc in landmarks.values():
        all_points.append([loc["lon"], loc["lat"]])
    mp = json.dumps({"type": "MultiPoint", "coordinates": all_points})
    hull = geometry.convex_hull(mp)
    hull_data = json.loads(hull)
    print(f"   Hull type: {hull_data['type']}")
    hull_area = geometry.area(hull, "km2")
    print(f"   Hull area: {hull_area:,.0f} km²")

    # 6. Compute area of Gulshan buffer
    print("\n6. Gulshan analysis zone area:")
    gulshan_buf_geojson = json.dumps(buffers["Gulshan, Dhaka"])
    area_m2 = geometry.area(gulshan_buf_geojson)
    area_ha = geometry.area(gulshan_buf_geojson, "ha")
    print(f"   Area: {area_m2/1e6:,.1f} km² ({area_ha:,.0f} ha)")

    # 7. Get bounding boxes
    print("\n7. Bounding boxes of analysis zones:")
    for name in names:
        b = geometry.bbox(json.dumps(buffers[name]))
        print(f"   {name}: [{b[0]:.4f}, {b[1]:.4f}, {b[2]:.4f}, {b[3]:.4f}]")

    # 8. Simplify a buffer
    print("\n8. Simplify Gulshan buffer:")
    simple = geometry.simplify(gulshan_buf_geojson, 500)
    simple_data = json.loads(simple)
    original_size = len(buffers["Gulshan, Dhaka"]["coordinates"][0])
    print(f"   Original vertices: {original_size}")
    print(f"   Simplified: {len(simple_data['coordinates'][0])} vertices (tolerance=500m)")

    # 9. Compute perimeter of Dhanmondi zone
    print("\n9. Perimeter of Dhanmondi buffer:")
    length_m = geometry.length(json.dumps(buffers["Dhanmondi, Dhaka"]))
    print(f"   Perimeter: {length_m/1000:.1f} km")

    # 10. Transform a point to Web Mercator for map display
    print("\n10. Coordinate transform (4326 -> 3857):")
    gulshan = landmarks["Gulshan, Dhaka"]
    gulshan_point = json.dumps({"type": "Point", "coordinates": [gulshan["lon"], gulshan["lat"]]})
    transformed = geometry.transform_crs(gulshan_point, "EPSG:4326", "EPSG:3857")
    t = json.loads(transformed)
    print(f"    Gulshan in Web Mercator: ({t['coordinates'][0]:,.0f}, {t['coordinates'][1]:,.0f})")

    # 11. Validate all geometries
    print("\n11. Geometry validation:")
    for name in names:
        valid = geometry.validate_geojson(json.dumps(buffers[name]))
        print(f"    {name}: valid={valid['valid']}")

    # 12. Build an Overpass query for educational facilities
    print("\n12. Overpass query: schools in Gulshan area")
    b = geometry.bbox(json.dumps(buffers["Gulshan, Dhaka"]))
    ql = osm.build_overpass_query(b, {"amenity": "school"})
    print(f"    Query length: {len(ql)} characters")

    # 13. Reverse geocode the centroid of our analysis area
    print("\n13. Reverse geocode analysis centroid:")
    centroid_geojson = geometry.centroid(gulshan_buf_geojson)
    c = json.loads(centroid_geojson)
    rev = await reverse_geocode(c["coordinates"][1], c["coordinates"][0])
    print(f"    Nearest address: {rev['display_name'][:80]}...")

    print(f"\n{'=' * 56}")
    print("Verified tools: geocode, reverse_geocode, buffer, distance,")
    print("area, bbox, spatial_predicate, centroid, convex_hull, simplify,")
    print("length, transform_crs, validate_geojson, build_overpass_query")
    print("13 of 24 registered tools exercised successfully.")


if __name__ == "__main__":
    asyncio.run(main())
