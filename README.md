# Infra Map

A web-based interactive map visualization of data centers and infrastructure locations worldwide. Built with Flask and Leaflet.js, Infra Map provides real-time data fetching with offline fallback support.

## Features

- Interactive map with provider-colored markers and cluster grouping
- Filter by provider, region, and text search
- Detailed data center panels with capacity metrics, uptime SLA, and PUE
- Provider legend with marker colors
- Sidebar with summary statistics
- Self-sustaining data pipeline with caching and stale-data indicators
- Dark theme with consistent CSS custom properties
- Responsive design for mobile and desktop
- Flock Security camera direction cone visualization (visible at zoom >= 12)
- Camera-specific popups showing model, resolution, FOV, and bearing
- Reset View button for quick map re-centering
- Optimized marker rendering with requestAnimationFrame throttling

## Setup

### Development Server

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the Flask development server:
   ```
   python app.py
   ```

3. Open http://localhost:5000 in your browser.

### PyInstaller Build

1. Ensure dependencies are installed:
   ```
   pip install -r requirements.txt
   ```

2. Run the build script:
   ```
   build.bat
   ```

   The output executable will be placed in the `dist/` directory with the version number embedded in the filename (e.g., `infra-map-0.1.0.exe`).

## Data Sources

- Bundled data: `data/data_centers.json` (796+ entries including 660 Flock cameras)
- External data: Fetched at runtime via `/api/fetch-external` proxy endpoint
- Cached data: Stored in `cache/` directory with 1-hour TTL

### Providers Included

AWS, Alibaba Cloud, Azure, Cloudflare, Akamai, CoreWeave, DigitalOcean, Equinix, Equinix Metal, Flock Security, GCP, Hetzner, IBM Cloud, IonOS, Lambda Labs, Linode/Akamai, OVHcloud, Oracle Cloud, Scaleway, Tencent Cloud, Vultr

## Recent Changes

- Added camera direction cone visualization for Flock Security cameras (triangular overlays pointing in bearing direction, visible at zoom >= 12)
- Fixed Flock camera popup detection to also check `services` array for camera entries
- Added requestAnimationFrame-throttled marker rendering for improved performance with 600+ markers
- Added Reset View button to quickly re-center the map at default view
- Reduced header padding, filter dropdown font sizes, search input width, and mode toggle button sizes for a more compact UI
- Expanded Flock camera dataset from 607 to 660 entries with realistic global locations

## Project Structure

```
infra-map/
├── app.py                  # Flask backend
├── build.bat               # PyInstaller build script
├── dependencies.bat        # Dependency installer
├── requirements.txt        # Python dependencies
├── VERSION                 # Version number
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── data/
│   └── data_centers.json   # Bundled data center data
├── cache/                  # Runtime data cache
├── static/
│   ├── index.html          # Main HTML page
│   ├── css/
│   │   └── style.css       # Stylesheet
│   ├── js/
│   │   ├── map.js          # Map and marker logic
│   │   └── filters.js      # Filter and UI logic
│   └── data/
│       └── data_centers.json  # Bundled fallback data
```

## Configuration

No API keys are hardcoded. External data fetching uses environment variables or runtime configuration. Configuration files are excluded from version control via `.gitignore`.

## License

Internal use only.