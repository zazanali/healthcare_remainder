
from datetime import datetime, timezone

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso_utc(v: str) -> datetime:
    if v.endswith("Z"):
        v = v.replace("Z", "+00:00")
    dt = datetime.fromisoformat(v)
    return dt.astimezone(timezone.utc)
