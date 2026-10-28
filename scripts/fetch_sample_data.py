"""Download only the seven pinned synthetic CSV fixtures and verify every byte."""
import csv
import hashlib
import io
import json
from pathlib import Path

import requests
from scripts.common import ROOT, require


def verify_file(content, spec):
    require(hashlib.sha256(content).hexdigest() == spec["sha256"], "Sample file checksum mismatch.")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    require(reader.fieldnames == spec["columns"], "Sample column order changed.")
    require(sum(1 for _ in reader) == spec["rows"], "Sample row count changed.")


def fetch(destination=None):
    destination = Path(destination or ROOT / "data")
    destination.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "sample-manifest.json").read_text())
    for name, spec in manifest["files"].items():
        path = destination / (name + ".csv")
        if not path.exists():
            url = f"https://raw.githubusercontent.com/{manifest['repository']}/{manifest['commit']}/data/{name}.csv"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            content = response.content
            verify_file(content, spec)
            path.write_bytes(content)
        else:
            verify_file(path.read_bytes(), spec)
        print(f"Verified {name}: {spec['rows']} rows")
    return destination


if __name__ == "__main__":
    fetch()
