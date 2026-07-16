# mcp-geo — Examples

This page is a growing collection of end-to-end workflows mcp-geo can power.
The patterns below are language-agnostic: any MCP client (Claude Desktop,
Cursor, OpenAI Codex CLI, custom agents) can drive them.

If you've used mcp-geo in a real workflow and would like to share it, open
a PR adding it here.

## Copy-Paste Workflows

These three workflows are ready to paste into any MCP client configured with
mcp-geo. Each lists the exact tool calls, expected output shape, and what
requires network or credentials.

### Workflow 1: Find and rank hospitals near a landmark

**Requires:** Network (Nominatim + Overpass). No API key needed.

**Agent prompt:**

> Find hospitals within 2 km of the Buriganga River in Dhaka, rank them by
> distance, and show the closest 5 on a map.

**Tool call sequence:**

```text
1. geocode("Buriganga River, Dhaka", limit=1)
   → [{lat: 23.705, lon: 90.375, name: "Buriganga River, Dhaka", ...}]

2. buffer(geojson='{"type":"Point","coordinates":[90.375,23.705]}', distance_m=2000)
   → {"type":"Polygon","coordinates":[[[90.355,23.705], ...]]}

3. osm_features(area='{"type":"Polygon","coordinates":[...]}', tags='{"amenity":"hospital"}')
   → {"type":"FeatureCollection","features":[{geometry:{type:Point,coordinates:[...]},properties:{name:"..."}}]}

4. For each hospital: distance(geojson1=river_point, geojson2=hospital_point)
   → 1234.5 (metres)

5. static_map(feature_collection=ranked_hospitals_geojson)
   → {"image":"<base64 PNG>","format":"png","size":[800,600]}
```

**If network is unavailable:** Use `--dry-run` mode or skip steps 1 and 3.
Steps 2, 4, and 5 work fully offline (geometry + matplotlib only).

### Workflow 2: 15-minute drive-time accessibility analysis

**Requires:** Network + `GEO_MCP_ORS_API_KEY` (free at [openrouteservice.org](https://openrouteservice.org/dev/#/signup)).

**Agent prompt:**

> What restaurants can I reach within a 15-minute drive from Brandenburg
> Gate in Berlin?

**Tool call sequence:**

```text
1. geocode("Brandenburg Gate, Berlin", limit=1)
   → [{lat: 52.5163, lon: 13.3777, ...}]

2. isochrone(lat=52.5163, lon=13.3777, range_value=900, range_type="time", profile="driving-car")
   → {"type":"FeatureCollection","features":[{geometry:{type:Polygon,...}}]}

3. osm_features(area=isochrone_polygon_geojson, tags='{"amenity":"restaurant"}')
   → {"type":"FeatureCollection","features":[...]}
```

**If ORS API key is not set:** Step 2 returns a clear error:
`"Isochrones require an OpenRouteService API key. Set GEO_MCP_ORS_API_KEY."`
Steps 1 and 3 still work independently.

### Workflow 3: Local GeoPackage inspection and spatial query

**Requires:** `pip install "mcp-geo[files]"`. No network. No API key.

**Agent prompt:**

> Inspect the landuse GeoPackage in my data folder, find all park parcels
> larger than 1 hectare, and buffer them by 100 metres.

**Tool call sequence:**

```text
1. vector_info(path="data/landuse.gpkg")
   → {"driver":"GPKG","crs":"EPSG:4326","features":1234,"schema":[{"name":"category","dtype":"str"},...]}

2. vector_read(path="data/landuse.gpkg", where="category='park'")
   → {"type":"FeatureCollection","features":[{geometry:{...},properties:{area_m2:...}}]}

3. For each park feature: area(geojson=feature_geometry, unit="ha")
   → 2.5 (hectares)

4. Filter features where area > 1.0 ha

5. For each filtered feature: buffer(geojson=feature_geometry, distance_m=100)
   → {"type":"Polygon","coordinates":[...]}

6. workspace_store(name="buffered_parks", data=buffered_features_geojson)
   → {"success":true}
```

**If pyogrio is not installed:** Steps 1 and 2 return a clear error:
`"Install the relevant extra, for example: pip install 'mcp-geo[files,raster,visual]'"`
Steps 3–6 work offline (geometry + workspace only).

## Additional Workflows

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
