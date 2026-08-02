# Infra Map

[![CI](https://github.com/puretechteam/infra-map/actions/workflows/ci.yml/badge.svg)](https://github.com/puretechteam/infra-map/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.1.0-informational)](https://github.com/puretechteam/infra-map/releases)

A web-based interactive map visualization of data centers and infrastructure locations worldwide. Built with Flask and Leaflet.js, Infra Map provides real-time data fetching with offline fallback support.

## Features

- Interactive map with provider-colored markers and cluster grouping
- Viewport filtering for data centers (renders correctly when panning the map)
- Improved marker clustering algorithm for better performance with large datasets
- Flock Security camera direction cone visualization at correct size (removed /15 divisor that made cones 15x too small)
- Filter by provider, region, and text search
- Detailed data center panels with capacity metrics, uptime SLA, and PUE
- Provider legend with marker colors
- Sidebar with summary statistics
- Self-sustaining data pipeline with caching and stale-data indicators
- Data file checksum verification for integrity
- CSS overflow/positioning fixes (no duplicate map rendering, no horizontal scrolling)
- Dark theme with consistent CSS custom properties
- Responsive design for mobile and desktop
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

## Testing

Run the test suite with:

```
make test
```

Or directly with pytest:

```
pytest
```

Tests are located in the `tests/` directory and use the `pytest` framework. The `tests/conftest.py` file provides a `client` fixture that returns a Flask test client configured in testing mode.

## Data Sources

> **Note:** The large data files in `data/` (`data_centers.json`, `data_centers_clean.json`, `alpr_batch*.json`) are gitignored to keep the repository size manageable. Before preprocessing, the raw `data_centers.json` must be obtained from the project data source. Then run:
>
> > python scripts/preprocess_data.py
> >
> This generates `data_centers_clean.json` from the raw data.

- Bundled data: `data/data_centers.json` (98,038 entries total: 290 data centers, 97,748 flock cameras; see Data Processing below)
- External data: Fetched at runtime via `/api/fetch-external` proxy endpoint
- Cached data: Stored in `cache/` directory with 1-hour TTL

### Data Processing

The raw data file `data/data_centers.json` contains a mix of data center entries and OpenStreetMap ALPR surveillance camera nodes with different schemas. Before use, the data must be preprocessed to filter out entries that do not conform to the expected data center schema.

Run the preprocessing script:

```
python scripts/preprocess_data.py
```

This reads `data/data_centers.json`, removes entries missing required fields (`name`, `provider`, `latitude`, `longitude`), and writes the cleaned data to `data/data_centers_clean.json`. A summary of removed and remaining entries is printed to the console.

The preprocessing step is necessary because approximately 0.2% of the raw dataset consists of OSM ALPR camera nodes with a different schema (`type: "node"`, `id`, `lat`, `lon`, `tags`) that lack the data center fields required by the application.

### Providers Included

AWS, Alibaba Cloud, Azure, Cloudflare, Akamai, CoreWeave, DigitalOcean, Equinix, Equinix Metal, Flock Security, GCP, Hetzner, IBM Cloud, IonOS, Lambda Labs, Linode/Akamai, OVHcloud, Oracle Cloud, Scaleway, Tencent Cloud, Vultr

## Recent Changes

- Fixed viewport filtering bug: data centers now render correctly when panning the map
- Fixed flock camera clustering: always uses leaflet.markercluster, removed conditional threshold
- Fixed CSS overflow/positioning issues causing duplicate map rendering and horizontal scrolling
- Fixed cone rendering size (removed /15 divisor that made cones 15x too small)
- Fixed checksum verification for data_centers.json
- Updated .gitignore with proper entries for data files
- Performance improvements: increased disableClusteringAtZoom to 14, increased maxClusterRadius to 80, removed moveend handler that was rebuilding all markers on every pan

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
├── build.bat               # PyInstaller build script (gitignored)
├── dependencies.bat        # Dependency installer (gitignored)
├── requirements.txt        # Runtime dependencies
├── VERSION                 # Version number
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── scripts/
│   └── preprocess_data.py  # Data preprocessing script
├── data/
│   ├── data_centers.json        # Raw bundled data (gitignored)
│   ├── data_centers_clean.json  # Cleaned data center data (gitignored)
│   ├── data_centers.json.sha256 # Checksum file (gitignored)
│   ├── alpr_batch*.json         # ALPR raw data files (gitignored)
│   └── alpr_batch*.json.sha256  # ALPR checksum files (gitignored)
├── cache/                  # Runtime data cache
├── static/
│   ├── index.html          # Main HTML page
│   ├── css/
│   │   └── style.css       # Stylesheet
│   ├── js/
│   │   ├── map.js          # Map and marker logic
│   │   ├── map.py          # Build utility script (gitignored)
│   │   └── filters.js      # Filter and UI logic
│   └── data/
│       ├── data_centers.json      # Bundled fallback data (gitignored)
│       └── data_centers.json.sha256  # Checksum file (gitignored)
```

## Configuration

No API keys are hardcoded. External data fetching uses environment variables or runtime configuration. Configuration files are excluded from version control via `.gitignore`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Security

Please report security vulnerabilities to the project maintainers. See [SECURITY.md](SECURITY.md) for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
