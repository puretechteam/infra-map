# Infra Map

[![CI](https://github.com/puretechteam/infra-map/actions/workflows/ci.yml/badge.svg)](https://github.com/puretechteam/infra-map/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.1.0-informational)](https://github.com/puretechteam/infra-map/releases)

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

> **Note:** The `Makefile` is the preferred cross-platform build tool. It works on Linux, macOS, and Windows (with WSL or Git Bash). Use `make install`, `make run`, `make build`, etc. The `.bat` scripts are kept for reference on native Windows without WSL or Git Bash.

### Development Server

1. Install dependencies:
   ```
   make install
   ```

2. Run the Flask development server:
   ```
   make run
   ```

3. Open http://localhost:5000 in your browser.

### Development Dependencies

For development and testing, install:
```
make install-dev
```

### PyInstaller Build

1. Ensure dependencies are installed (see above).

2. Run the build:
   ```
   make build
   ```

   The output executable will be placed in the `dist/` directory with the version number embedded in the filename (e.g., `infra-map-0.1.0.exe`).

## Data Sources

- Bundled data: `data/data_centers.json` (141,736 entries total; see Data Processing below)
- External data: Fetched at runtime via `/api/fetch-external` proxy endpoint
- Cached data: Stored in `cache/` directory with 1-hour TTL

### Data Processing

The raw data file `data/data_centers.json` contains a mix of data center entries and OpenStreetMap ALPR surveillance camera nodes with different schemas. Before use, the data must be preprocessed to filter out entries that do not conform to the expected data center schema.

Run the preprocessing script:

```
python scripts/preprocess_data.py
```

This reads `data/data_centers.json`, removes entries missing required fields (`name`, `provider`, `latitude`, `longitude`), and writes the cleaned data to `data/data_centers_clean.json`. A summary of removed and remaining entries is printed to the console.

The preprocessing step is necessary because approximately 31% of the raw dataset consists of OSM ALPR camera nodes with a different schema (`type: "node"`, `id`, `lat`, `lon`, `tags`) that lack the data center fields required by the application.

### Providers Included

AWS, Alibaba Cloud, Azure, Cloudflare, Akamai, CoreWeave, DigitalOcean, Equinix, Equinix Metal, Flock Security, GCP, Hetzner, IBM Cloud, IonOS, Lambda Labs, Linode/Akamai, OVHcloud, Oracle Cloud, Scaleway, Tencent Cloud, Vultr

## Recent Changes

- Added camera direction cone visualization for Flock Security cameras (triangular overlays pointing in bearing direction, visible at zoom >= 12)
- Fixed Flock camera popup detection to also check `services` array for camera entries
- Added requestAnimationFrame-throttled marker rendering for improved performance with 600+ markers
- Added Reset View button to quickly re-center the map at default view
- Reduced header padding, filter dropdown font sizes, search input width, and mode toggle button sizes for a more compact UI
- Expanded Flock camera dataset from 607 to 660 entries with realistic global locations

## Roadmap

- Add real-time alerting for infrastructure anomalies
- Support for custom map layers and annotations
- Integration with monitoring tools (Prometheus, Grafana)
- Historical capacity planning charts
- Multi-region cost comparison view

## Project Structure

```
infra-map/
├── app.py                  # Flask backend
├── build.bat               # PyInstaller build script
├── dependencies.bat        # Dependency installer
├── requirements.txt        # Runtime dependencies
├── VERSION                 # Version number
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── scripts/
│   └── preprocess_data.py  # Data preprocessing script
├── data/
│   ├── data_centers.json        # Raw bundled data (mixed schema)
│   └── data_centers_clean.json  # Cleaned data center data
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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Security

Please report security vulnerabilities to the project maintainers. See [SECURITY.md](SECURITY.md) for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.