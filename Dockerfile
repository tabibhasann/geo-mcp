FROM python:3.12-slim

LABEL maintainer="Tabib Hasan"
LABEL description="Geospatial MCP server - give AI agents geocoding, routing, spatial ops, and OSM querying"

WORKDIR /app

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[files,raster,visual]"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GEO_MCP_USER_AGENT="mcp-geo-docker/0.3.0"

# Expose port for HTTP/SSE transport
EXPOSE 8000

# Default command: run in stdio mode
CMD ["mcp-geo"]
