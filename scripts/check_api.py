"""Try a few Cricbuzz endpoints and save their JSON so we can see the real structure.

Usage:  python scripts\check_api.py
Prints only status and top-level keys (never your key). Samples go to data/api_samples/.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.cricbuzz_client import ApiError, CricbuzzClient  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "api_samples"

ENDPOINTS = [
    ("live_matches", "/matches/v1/live", None),
    ("recent_matches", "/matches/v1/recent", None),
    ("top_runs", "/stats/v1/topstats/0", {"statsType": "mostRuns"}),
    ("rankings_batsmen", "/stats/v1/rankings/batsmen", {"formatType": "odi"}),
    ("series_international", "/series/v1/international", None),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        client = CricbuzzClient()
    except ApiError as exc:
        print("Setup problem:", exc)
        return
    for name, path, params in ENDPOINTS:
        try:
            data = client.get(path, params)
        except ApiError as exc:
            print(f"{name:<22} FAILED: {exc}")
            continue
        (OUT_DIR / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        print(f"{name:<22} OK     top-level keys: {keys}")
        time.sleep(1)


if __name__ == "__main__":
    main()
