# Architecture

```
geo-mcp
├── src/geo_mcp/
│   ├── server.py              # MCP server entry point — argparse CLI, transport selection
│   ├── config.py              # Load .env, provider configuration, quota tracking
│   ├── providers/
│   │   ├── __init__.py        # Provider plugin registry
│   │   ├── base.py            # AbstractProvider — interface for all providers
│   │   ├── nominatim.py       # Nominatim geocoding provider
│   │   ├── overpass.py        # Overpass API provider (OSM queries)
│   │   └── photon.py          # Photon geocoding provider
│   ├── tools/
│   │   ├── __init__.py        # MCP tool registration
│   │   ├── geocode.py         # geocode / reverse_geocode tools
│   │   ├── search.py          # search_pois, search_features tools
│   │   └── isochrone.py       # Isochrone / routing tools
│   └── transports/
│       ├── stdio.py           # stdio transport (default for MCP clients)
│       ├── sse.py             # Server-Sent Events transport
│       └── http.py            # Streamable HTTP transport
├── tests/
│   ├── test_server.py         # Server startup / transport tests
│   ├── test_tools.py          # Tool registration and mock execution tests
│   └── test_integration.py    # End-to-end integration test with --dry-run
├── EXAMPLES.md                # Usage examples for MCP clients
├── pyproject.toml
└── .env.example
```

## Data Flow

```
MCP Client (Claude, etc.)
    │
    ▼
server.py (argparse → transport)
    │
    ├──► stdio / sse / http transport
    │       │
    │       ▼
    │    MCP protocol handler
    │       │
    │       ├──► tools.list → registered tools
    │       └──► tools.call → tool handler
    │               │
    │               ▼
    │           providers/
    │               ├── NominatimProvider
    │               ├── OverpassProvider
    │               └── PhotonProvider
    │                   │
    │                   ├──► --dry-run → mock data
    │                   └──► live API call → quota tracked
    │
    └──► Response (JSON)
```

## Key Design Decisions

- **Provider plugin system**: Providers implement `AbstractProvider` — adding a new geocoding source is a single file.
- **--dry-run mode**: Returns mock data without hitting APIs, enabling CI testing.
- **Quota tracking**: Each provider call is logged for rate-limit awareness.
- **Multiple transports**: stdio (default), SSE, and streamable HTTP per MCP spec.
- **Subcommands**: `doctor` (health check), `tools` (list tools), `providers` (list configured providers).
