import hashlib
import json
from pathlib import Path

from app import compute_checksum, load_and_validate_data, validate_data

DATA_DIR = Path(__file__).parent.parent / "data"


def test_data_loading():
    data_file = DATA_DIR / "data_centers.json"
    assert data_file.exists()
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0


def test_clean_data_loading():
    data_file = DATA_DIR / "data_centers_clean.json"
    assert data_file.exists()
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0
    error = validate_data(data)
    assert error is None


def test_schema_validation_valid():
    valid_data = [
        {
            "name": "Test DC",
            "provider": "AWS",
            "region": "US-East",
            "city": "Virginia",
            "country": "US",
            "latitude": 39.0,
            "longitude": -77.0,
            "services": [],
        }
    ]
    error = validate_data(valid_data)
    assert error is None


def test_schema_validation_missing_fields():
    invalid_data = [
        {
            "name": "Test DC",
            "provider": "AWS",
        }
    ]
    error = validate_data(invalid_data)
    assert error is not None


def test_schema_validation_invalid_latitude():
    invalid_data = [
        {
            "name": "Test DC",
            "provider": "AWS",
            "region": "US-East",
            "city": "Virginia",
            "country": "US",
            "latitude": "not_a_number",
            "longitude": -77.0,
            "services": [],
        }
    ]
    error = validate_data(invalid_data)
    assert error is not None


def test_schema_validation_flock_missing_fields():
    invalid_data = [
        {
            "name": "Flock Camera",
            "provider": "Flock Security",
            "region": "US-East",
            "city": "Virginia",
            "country": "US",
            "latitude": 39.0,
            "longitude": -77.0,
            "services": ["camera"],
        }
    ]
    error = validate_data(invalid_data)
    assert error is not None
    assert "bearing" in error


def test_checksum_file_exists():
    data_file = DATA_DIR / "data_centers.json"
    sha256_file = DATA_DIR / "data_centers.json.sha256"
    assert data_file.exists()
    assert sha256_file.exists()


def test_checksum_verification():
    data_file = DATA_DIR / "data_centers.json"
    sha256_file = DATA_DIR / "data_centers.json.sha256"

    actual_checksum = compute_checksum(str(data_file))
    with open(sha256_file, "r") as f:
        expected_checksum = f.read().strip()

    assert actual_checksum.lower() == expected_checksum.lower()


def test_checksum_computation():
    data_file = DATA_DIR / "data_centers.json"
    checksum = compute_checksum(str(data_file))
    assert isinstance(checksum, str)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)