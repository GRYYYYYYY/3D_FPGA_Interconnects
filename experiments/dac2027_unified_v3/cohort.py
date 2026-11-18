"""Select the output directory of exactly one physical allocation."""
import os
from pathlib import Path

here = Path(__file__).resolve().parent
allocation = os.environ.get("V3_ALLOCATION", "a")
if allocation not in ("a", "b", "c"):
    raise ValueError(f"Unknown V3 allocation {allocation!r}")
root = here if allocation == "a" else here / f"allocation_{allocation}"
run = root / "run"
audit = root / "audit"
