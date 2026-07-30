import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {"name", "provider", "latitude", "longitude"}


def main() -> None:
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "data_centers.json"
    output_path = project_root / "data" / "data_centers_clean.json"

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    cleaned = [
        entry for entry in data
        if REQUIRED_FIELDS.issubset(entry.keys())
    ]

    removed = total - len(cleaned)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Total entries: {total}")
    print(f"Removed entries: {removed}")
    print(f"Remaining entries: {len(cleaned)}")
    print(f"Cleaned data written to: {output_path}")


if __name__ == "__main__":
    main()