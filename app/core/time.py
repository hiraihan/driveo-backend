from datetime import datetime, date, timezone, timedelta

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def today_wib() -> date:
    return (utcnow() + timedelta(hours=7)).date()
