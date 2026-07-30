"""Infra Map - Flask backend for data center and infrastructure visualization.

Provides REST API endpoints for serving data center data, fetching external
data with SSRF protection and rate limiting, and caching validated data
in memory with file modification time-based invalidation.
"""

import hashlib
import ipaddress
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, Response, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="/static")

DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = Path(__file__).parent / "cache"
STATIC_DIR = Path(__file__).parent / "static"

CACHE_TTL_SECONDS = 3600

PRIVATE_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
]

RATE_LIMIT_WINDOW = 30
RATE_LIMIT_MAX_REQUESTS = 1

_rate_limit_store: dict[str, list[float]] = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

_validated_data_cache: list[dict] | None = None
_data_file_mtime: float | None = None


def get_data_path() -> str:
    """Return the path to the data directory, accounting for PyInstaller bundling."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "data")
    return str(DATA_DIR)


def get_static_path() -> str:
    """Return the path to the static directory, accounting for PyInstaller bundling."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "static")
    return str(STATIC_DIR)


def ensure_cache_dir() -> None:
    """Create the cache directory if it does not exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def compute_checksum(filepath: str) -> str:
    """Compute the SHA-256 checksum of a file.

    Args:
        filepath: Path to the file to hash.

    Returns:
        The hexadecimal SHA-256 digest.
    """
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_data(data: list[dict]) -> str | None:
    """Validate a list of data center entries against the required schema.

    Args:
        data: A list of dictionaries representing data center entries.

    Returns:
        None if valid, or an error message string if validation fails.
    """
    if not isinstance(data, list):
        return "Data file must contain a JSON array"

    required_fields = {"name", "provider", "region", "city", "country", "latitude", "longitude"}
    for i, item in enumerate(data):
        missing = required_fields - set(item.keys())
        if missing:
            return f"Entry {i} missing fields: {missing}"
        if not isinstance(item.get("services", []), list):
            return f"Entry {i} has invalid services field"
        if not isinstance(item.get("latitude"), (int, float)):
            return f"Entry {i} has invalid latitude"
        if not isinstance(item.get("longitude"), (int, float)):
            return f"Entry {i} has invalid longitude"
        if item.get("provider") == "Flock Security":
            for field in ("bearing", "camera_model", "resolution"):
                if field not in item:
                    return f"Entry {i} (Flock camera) missing field: {field}"

    return None


def load_and_validate_data() -> tuple[list[dict] | None, str | None]:
    """Load and validate the data centers JSON file.

    Results are cached in memory and only reloaded when the file's
    modification time changes.

    Returns:
        A tuple of (data, error). data is the validated list of entries
        on success, or None on failure. error is None on success, or
        an error message string on failure.
    """
    data_path = os.path.join(get_data_path(), "data_centers.json")
    if not os.path.exists(data_path):
        return None, "Data file not found"

    try:
        current_mtime = os.path.getmtime(data_path)
    except OSError as e:
        logger.error("Failed to get mtime for data file: %s", e)
        return None, f"Failed to access data file: {e}"

    global _validated_data_cache, _data_file_mtime
    if _validated_data_cache is not None and _data_file_mtime == current_mtime:
        logger.debug("Returning cached validated data (mtime unchanged)")
        return _validated_data_cache, None

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Failed to parse data file: %s", e)
        return None, f"Failed to parse data file: {e}"

    error = validate_data(data)
    if error:
        logger.error("Data validation failed: %s", error)
        return None, error

    _validated_data_cache = data
    _data_file_mtime = current_mtime
    logger.info("Loaded and validated %d data center entries", len(data))
    return data, None


def is_url_allowed(url: str) -> bool:
    """Check whether a URL is allowed for external fetching.

    Only HTTPS URLs to public IP addresses are permitted. Private and
    internal IP ranges are blocked to prevent SSRF attacks.

    Args:
        url: The URL to validate.

    Returns:
        True if the URL is allowed, False otherwise.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        logger.warning("Rejected non-HTTPS URL: %s", url)
        return False

    hostname = parsed.hostname
    if not hostname:
        logger.warning("Rejected URL with no hostname: %s", url)
        return False

    try:
        ip = ipaddress.ip_address(hostname)
        for network in PRIVATE_IP_RANGES:
            if ip in network:
                logger.warning("Rejected private IP URL: %s", url)
                return False
    except ValueError:
        pass

    return True


def check_rate_limit(ip: str) -> bool:
    """Check whether an IP address is within the rate limit.

    Allows at most one request per RATE_LIMIT_WINDOW seconds per IP.

    Args:
        ip: The client IP address.

    Returns:
        True if the request is allowed, False if rate limited.
    """
    now = datetime.now(timezone.utc).timestamp()
    if ip in _rate_limit_store:
        timestamps = _rate_limit_store[ip]
        recent = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
        _rate_limit_store[ip] = recent
        if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning("Rate limit exceeded for IP: %s", ip)
            return False
    else:
        _rate_limit_store[ip] = []

    _rate_limit_store[ip].append(now)
    return True


def get_cached_or_fetch(url: str, cache_filename: str) -> tuple[list[dict] | None, str | None]:
    """Fetch a URL with file-based caching.

    If a cached entry exists and is within CACHE_TTL_SECONDS, it is
    returned directly. Otherwise the URL is fetched and cached.

    Args:
        url: The URL to fetch.
        cache_filename: The filename to use for caching the response.

    Returns:
        A tuple of (result, error). result is the parsed JSON data
        on success, or None on failure. error is None on success, or
        an error/stale message on failure.
    """
    ensure_cache_dir()
    cache_path = os.path.join(str(CACHE_DIR), cache_filename)
    now = datetime.now(timezone.utc).timestamp()

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            fetched_at = cached.get("_fetched_at", 0)
            if now - fetched_at < CACHE_TTL_SECONDS:
                return cached.get("_data"), None
        except (OSError, json.JSONDecodeError):
            pass

    try:
        import requests
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        result = resp.json()

        if not isinstance(result, list):
            return None, "Invalid response structure from external source"

        cache_entry = {"_fetched_at": now, "_data": result}
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_entry, f)

        return result, None
    except Exception as e:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                return cached.get("_data"), "data may be stale"
            except (OSError, json.JSONDecodeError):
                pass
        return None, str(e)


@app.route("/")
def index() -> Response:
    """Serve the main index HTML page."""
    return send_from_directory(get_static_path(), "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename: str) -> Response:
    """Serve a static file from the static directory.

    Args:
        filename: The relative path to the static file.

    Returns:
        The file response.
    """
    return send_from_directory(get_static_path(), filename)


@app.route("/api/data")
def api_data() -> Response:
    """Return the full data center dataset.

    On validation failure, falls back to cached data if available.
    """
    data, error = load_and_validate_data()
    if error:
        cached_data = get_cached_fallback()
        if cached_data is not None:
            return jsonify({"data": cached_data, "stale": True, "error": error})
        return jsonify({"data": [], "stale": False, "error": error}), 503

    return jsonify({"data": data, "stale": False, "error": None})


@app.route("/api/providers")
def api_providers() -> Response:
    """Return a sorted list of unique data center providers.

    On validation failure, falls back to cached data if available.
    """
    data, error = load_and_validate_data()
    if error:
        cached_data = get_cached_fallback()
        if cached_data is not None:
            providers = sorted(set(item["provider"] for item in cached_data))
            return jsonify({"providers": providers, "stale": True, "error": error})
        return jsonify({"providers": [], "stale": False, "error": error}), 503

    providers = sorted(set(item["provider"] for item in data))
    return jsonify({"providers": providers, "stale": False, "error": None})


@app.route("/api/regions")
def api_regions() -> Response:
    """Return a sorted list of unique data center regions.

    On validation failure, falls back to cached data if available.
    """
    data, error = load_and_validate_data()
    if error:
        cached_data = get_cached_fallback()
        if cached_data is not None:
            regions = sorted(set(item["region"] for item in cached_data))
            return jsonify({"regions": regions, "stale": True, "error": error})
        return jsonify({"regions": [], "stale": False, "error": error}), 503

    regions = sorted(set(item["region"] for item in data))
    return jsonify({"regions": regions, "stale": False, "error": None})


@app.route("/api/stats")
def api_stats() -> Response:
    """Return aggregate statistics about the data center dataset.

    On validation failure, falls back to cached data if available.
    """
    data, error = load_and_validate_data()
    if error:
        cached_data = get_cached_fallback()
        if cached_data is not None:
            data = cached_data
        else:
            return jsonify({"total_centers": 0, "total_capacity_mw": 0, "providers_count": 0, "stale": False, "error": error})

    total_centers = len(data)
    total_capacity = sum(item.get("capacity_mw", 0) for item in data)
    providers = sorted(set(item["provider"] for item in data))

    return jsonify({
        "total_centers": total_centers,
        "total_capacity_mw": total_capacity,
        "providers_count": len(providers),
        "stale": False,
        "error": None,
    })


@app.route("/api/fetch-external")
def api_fetch_external() -> Response:
    """Fetch an external URL and return its JSON content.

    Enforces HTTPS-only URLs, blocks private/internal IP ranges (SSRF
    protection), and rate limits to one request per 30 seconds per IP.
    """
    url = request.args.get("url", "")
    if not url:
        logger.warning("No URL provided to fetch-external endpoint")
        return jsonify({"error": "No URL provided"}), 400

    client_ip = request.remote_addr
    if not check_rate_limit(client_ip):
        return jsonify({"error": "Rate limit exceeded. Maximum 1 request per 30 seconds."}), 429

    if not is_url_allowed(url):
        return jsonify({"error": "URL not allowed. Only HTTPS URLs to public IP addresses are permitted."}), 403

    cache_filename = hashlib.sha256(url.encode()).hexdigest() + ".json"
    result, error = get_cached_or_fetch(url, cache_filename)

    if result is None:
        logger.error("Failed to fetch external URL %s: %s", url, error)
        return jsonify({"error": error, "data": []}), 503

    stale = error is not None
    return jsonify({"data": result, "stale": stale, "error": error if stale else None})


def get_cached_fallback() -> list[dict] | None:
    """Load cached data from disk and validate it.

    Returns the data only if it passes the same validation as
    load_and_validate_data(). Returns None if the file is missing,
    invalid JSON, or fails validation.
    """
    ensure_cache_dir()
    data_path = os.path.join(get_data_path(), "data_centers.json")
    if os.path.exists(data_path):
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            error = validate_data(data)
            if error:
                logger.warning("Cached fallback data failed validation: %s", error)
                return None
            logger.info("Loaded %d entries from cached fallback data", len(data))
            return data
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to load cached fallback data: %s", e)
    return None


@app.errorhandler(404)
def not_found(e: Exception) -> Response:
    """Handle 404 errors with a JSON response."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e: Exception) -> Response:
    """Handle 500 errors with a JSON response."""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    ensure_cache_dir()
    logger.info("Starting infra-map server on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)