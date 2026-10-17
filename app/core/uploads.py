from pathlib import Path

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
ROOM_TYPE_DIR = UPLOAD_ROOT / "room-types"
ROOM_TYPE_DIR.mkdir(parents=True, exist_ok=True)
MAX_IMAGE_BYTES = 3 * 1024 * 1024
