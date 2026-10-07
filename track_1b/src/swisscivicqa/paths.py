"""Locate the project data directory (works from a checkout and from an installed package)."""
import os
from pathlib import Path


def project_root() -> Path:
    env = os.environ.get("SWISSCIVICQA_ROOT")
    if env:
        return Path(env).resolve()
    checkout = Path(__file__).resolve().parents[2]
    if (checkout / "data" / "source").is_dir():
        return checkout
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "data" / "source").is_dir():
            return candidate
    raise FileNotFoundError("data/source not found; run inside track_1b/ or set SWISSCIVICQA_ROOT")


ROOT = project_root()
