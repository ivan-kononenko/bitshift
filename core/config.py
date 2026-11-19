from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LICENSE_PATH = REPO_ROOT / "LICENSE"
PUZZLES_PATH = REPO_ROOT / "data" / "puzzles.json"
EXAMPLE_PUZZLES_PATH = REPO_ROOT / "data" / "puzzles.example.json"


def get_manifest_path() -> Path:
    """Returns data/puzzles.json if present, falling back to puzzles.example.json."""
    return PUZZLES_PATH if PUZZLES_PATH.exists() else EXAMPLE_PUZZLES_PATH