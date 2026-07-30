# Changelog

All notable changes to Infra Map will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-29

### Added

- Initial release of Infra Map
- Interactive map with provider-colored markers and cluster grouping
- Filter by provider, region, and text search
- Detailed data center panels with capacity metrics, uptime SLA, and PUE
- Provider legend with marker colors
- Sidebar with summary statistics
- Self-sustaining data pipeline with caching and stale-data indicators
- Dark theme with consistent CSS custom properties
- Responsive design for mobile and desktop
- Flock Security camera direction cone visualization
- Camera-specific popups showing model, resolution, FOV, and bearing
- Reset View button for quick map re-centering
- Optimized marker rendering with requestAnimationFrame throttling
- PyInstaller build support for standalone Windows .exe