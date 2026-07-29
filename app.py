import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="/static")

DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = Path(__file__).parent / "cache"
STATIC_DIR = Path(__file__).parent / "static"

CACHE_TTL_SECONDS = 3600


def get_data_path():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "data")
    return str(DATA_DIR)


def get_static_path():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "static")
    return str(STATIC_DIR)


def ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def compute_checksum(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_and_validate_data():
    data_path = os.path.join(get_data_path(), "data_centers.json")
    if not os.path.exists(data_path):
        return None, "Data file not found"

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return None, f"Failed to parse data file: {e}"

    if not isinstance(data, list):
        return None, "Data file must contain a JSON array"

    required_fields = {"name", "provider", "region", "city", "country", "latitude", "longitude"}
    for i, item in enumerate(data):
        missing = required_fields - set(item.keys())
        if missing:
            return None, f"Entry {i} missing fields: {missing}"
        if not isinstance(item.get("services", []), list):
            return None, f"Entry {i} has invalid services field"
        if not isinstance(item.get("latitude"), (int, float)):
            return None, f"Entry {i} has invalid latitude"
        if not isinstance(item.get("longitude"), (int, float)):
            return None, f"Entry {i} has invalid longitude"
        if item.get("provider") == "Flock Security":
            for field in ("bearing", "camera_model", "resolution"):
                if field not in item:
                    return None, f"Entry {i} (Flock camera) missing field: {field}"

    return data, None


def get_cached_or_fetch(url, cache_filename):
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
        except (json.JSONDecodeError, IOError):
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
            except (json.JSONDecodeError, IOError):
                pass
        return None, str(e)


@app.route("/")
def index():
    return send_from_directory(get_static_path(), "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(get_static_path(), filename)


@app.route("/api/data")
def api_data():
    data, error = load_and_validate_data()
    if error:
        cached_data = get_cached_fallback()
        if cached_data is not None:
            return jsonify({"data": cached_data, "stale": True, "error": error})
        return jsonify({"data": [], "stale": False, "error": error}), 503

    return jsonify({"data": data, "stale": False, "error": None})


@app.route("/api/providers")
def api_providers():
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
def api_regions():
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
def api_stats():
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
        "error": None
    })


@app.route("/api/fetch-external")
def api_fetch_external():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    cache_filename = hashlib.sha256(url.encode()).hexdigest() + ".json"
    result, error = get_cached_or_fetch(url, cache_filename)

    if result is None:
        return jsonify({"error": error, "data": []}), 503

    stale = error is not None
    return jsonify({"data": result, "stale": stale, "error": error if stale else None})


def get_cached_fallback():
    ensure_cache_dir()
    data_path = os.path.join(get_data_path(), "data_centers.json")
    if os.path.exists(data_path):
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    ensure_cache_dir()
    app.run(host="0.0.0.0", port=5000, debug=False)