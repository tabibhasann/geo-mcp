# mcp-geo — Examples

This page is a growing collection of end-to-end workflows mcp-geo can power.
The patterns below are language-agnostic: any MCP client (Claude Desktop,
Cursor, OpenAI Codex CLI, custom agents) can drive them.

If you've used mcp-geo in a real workflow and would like to share it, open
a PR adding it here.

## 1. "Find hospitals near a river" (Buriganga example)

The headline demo from the README. An agent can answer
*"which hospitals are within 2 km of the Buriganga river in Dhaka?"* by
chaining:

1. `geocode("Buriganga River, Dhaka")` → `[{lat, lon, ...}]`
2. `buffer(point, distance_m=2000)` → 2 km polygon
3. `osm_features(area=buffer, tags={"amenity": "hospital"})` → hospitals
4. `distance(point, hospital)` for each result → ranking
5. `static_map(feature_collection=results)` → PNG preview

Example agent prompt:

> Show me hospitals within 2 km of the Buriganga river in Dhaka and plot
> the closest five on a map.

## 2. Isochrone-based "where can I reach in 15 minutes by car"

1. `geocode("Brandenburg Gate, Berlin")` → center point
2. `isochrone(lat, lon, range_value=900, range_type="time", profile="driving-car")`
   → reachable polygon
3. `osm_features(area=polygon, tags={"amenity": "restaurant"})`
   → restaurants within the 15-minute drive

Requires `GEO_MCP_ORS_API_KEY`.

## 3. Elevation profile for a hike

1. `geocode("Trailhead, Mount Tamalpais")` → start
2. `geocode("Mount Tamalpais summit")` → end
3. Sample a path between them and call
   `elevation_profile(coordinates=path)` to get elevations.
4. `static_map(path, style="osm")` to render the route.

## 4. Inspect a local GeoPackage

For users with local GIS data:

```text
1. vector_info("data/landuse.gpkg")
2. vector_read("data/landuse.gpkg", bbox=[-122.5, 37.7, -122.3, 37.85], where="category='park'")
3. buffer each feature by 100 m
4. static_map(feature_collection=..., style="carto-darkmatter")
```

Requires `pip install "mcp-geo[files]"` and a real .gpkg on disk.

## 5. Raster sampling over a vector mask

```text
1. raster_info("data/elevation.tif")
2. sample_raster(path="data/elevation.tif", points_geojson=cities_gdf)
3. zonal_stats(raster_path="data/elevation.tif", zones_geojson=countries_gdf, stats=["mean", "max"])
```

Requires `pip install "mcp-geo[raster]"`.

## 6. "Suggest tools" — for complex multi-step tasks

The server ships with two meta-tools that help the agent plan:

- `list_all_tools()` — full catalog grouped by category
- `suggest_tools("rank restaurants by drive time from my hotel")` — keyword
  routing that returns a recommended subset

Use these to keep large tool catalogs from blowing up the context window.

## 7. Spatial queries over a large local dataset

```text
1. vector_read("data/buildings.gpkg", limit=2000)
2. build_spatial_index(feature_collection=...)
3. spatial_query(target_collection=buildings, query_geojson=buffer_of_query, predicate="within")
4. spatial_join(points=ev_chargers, polygons=buildings)  # nearest polygon per point
5. nearest_neighbor(query_geojson=query, candidates_geojson=buildings, k=5)
```

These accelerated tools use shapely STRtree under the hood and stay
responsive on multi-thousand-feature collections.
