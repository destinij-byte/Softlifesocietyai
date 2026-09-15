from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(dt: datetime) -> datetime:
    """MongoDB (real or mocked) hands back naive datetimes by default — treat
    them as UTC rather than risk a naive/aware comparison crash."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
