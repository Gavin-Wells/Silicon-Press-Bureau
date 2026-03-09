from datetime import date, datetime
from zoneinfo import ZoneInfo


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def shanghai_now() -> datetime:
    """
    Return naive local datetime in Asia/Shanghai.

    Database DateTime columns in this project are naive, so we normalize to
    local wall-clock time and strip tzinfo before persistence.
    """
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None)


def shanghai_today() -> date:
    """Return local date in Asia/Shanghai."""
    return datetime.now(SHANGHAI_TZ).date()
