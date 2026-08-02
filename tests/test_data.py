import json
from pathlib import Path
from unittest.mock import patch

from app import (
    _verify_data_checksum,
    compute_checksum,
    load_and_validate_data,
    validate_data,
    verify_alpr_checksums,
)

DATA_DIR = Path(__file__).parent.parent / "data"


def test_data_loading():
    data_file = DATA_DIR / "data_centers.json"
    assert data_file.exists()
    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0


def test_clean_data_loading():
    data_file = DATA_DIR / "data_centers_clean.json"
    assert data_file.exists()
    with open(data_file, encoding="utf-8") as f:
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
    with open(sha256_file) as f:
        expected_checksum = f.read().strip()

    assert actual_checksum.lower() == expected_checksum.lower()


def test_checksum_computation():
    data_file = DATA_DIR / "data_centers.json"
    checksum = compute_checksum(str(data_file))
    assert isinstance(checksum, str)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)


def test_verify_data_checksum_valid():
    data_file = DATA_DIR / "data_centers.json"
    verified, error = _verify_data_checksum(str(data_file))
    assert verified is True
    assert error is None


def test_verify_data_checksum_mismatch():
    data_file = DATA_DIR / "data_centers.json"
    with patch(
        "app.compute_checksum",
        return_value="0000000000000000000000000000000000000000000000000000000000000000",
    ):
        verified, error = _verify_data_checksum(str(data_file))
    assert verified is False
    assert error is not None


def test_verify_data_checksum_no_file():
    verified, error = _verify_data_checksum(str(DATA_DIR / "nonexistent.json"))
    assert verified is False
    assert error is not None


def test_load_and_validate_data_returns_checksum_verified():
    data, error, checksum_verified = load_and_validate_data()
    assert data is not None
    assert error is None
    assert checksum_verified is True


def test_load_and_validate_data_checksum_mismatch_rejected():
    sha256_file = DATA_DIR / "data_centers.json.sha256"
    with open(sha256_file, encoding="utf-8") as f:
        original_stored = f.read().strip()
    try:
        with open(sha256_file, "w", encoding="utf-8") as f:
            f.write("0000000000000000000000000000000000000000000000000000000000")
        import app
        app._data_file_mtime = None
        app._validated_data_cache = None
        data, error, checksum_verified = load_and_validate_data()
        assert data is None
        assert error is not None
        assert checksum_verified is False
    finally:
        with open(sha256_file, "w", encoding="utf-8") as f:
            f.write(original_stored)


def test_verify_alpr_checksums():
    results = verify_alpr_checksums()
    assert isinstance(results, dict)
    for i in range(1, 6):
        key = f"alpr_batch{i}.json"
        assert key in results
        assert results[key] is True
