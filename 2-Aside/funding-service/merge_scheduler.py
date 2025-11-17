"""
Simplified merge cycle scheduler using real-time WAT checking.
No pre-created merge cycles, no Celery - just check current time and match.
"""

from datetime import datetime, time, timedelta
import pytz
from typing import Optional, Tuple

# West Africa Time (Nigeria)
WAT = pytz.timezone('Africa/Lagos')

# Merge times in WAT (9am, 3pm, 9pm)
MERGE_TIMES = [
    time(9, 0),   # 9:00 AM WAT
    time(15, 0),  # 3:00 PM WAT
    time(21, 0),  # 9:00 PM WAT
]

# Join window duration (5 minutes after merge time)
JOIN_WINDOW_MINUTES = 5


def get_current_wat_time() -> datetime:
    """Get current time in WAT timezone."""
    return datetime.now(WAT)


def get_next_merge_time() -> Tuple[datetime, datetime]:
    """
    Get the next scheduled merge time in WAT.

    Returns:
        Tuple of (merge_time_utc, join_window_closes_utc)
    """
    now_wat = get_current_wat_time()
    today_wat = now_wat.date()

    # Check today's remaining merge times
    for merge_time in MERGE_TIMES:
        merge_datetime_wat = WAT.localize(
            datetime.combine(today_wat, merge_time)
        )
        if merge_datetime_wat > now_wat:
            merge_datetime_utc = merge_datetime_wat.astimezone(pytz.utc).replace(tzinfo=None)
            join_window_closes_utc = (merge_datetime_wat + timedelta(minutes=JOIN_WINDOW_MINUTES)).astimezone(pytz.utc).replace(tzinfo=None)
            return merge_datetime_utc, join_window_closes_utc

    # No more merges today, get first merge time tomorrow
    tomorrow_wat = today_wat + timedelta(days=1)
    first_merge_time = MERGE_TIMES[0]
    merge_datetime_wat = WAT.localize(
        datetime.combine(tomorrow_wat, first_merge_time)
    )
    merge_datetime_utc = merge_datetime_wat.astimezone(pytz.utc).replace(tzinfo=None)
    join_window_closes_utc = (merge_datetime_wat + timedelta(minutes=JOIN_WINDOW_MINUTES)).astimezone(pytz.utc).replace(tzinfo=None)
    return merge_datetime_utc, join_window_closes_utc


def is_merge_time_now() -> bool:
    """
    Check if current time matches a merge schedule (9am, 3pm, or 9pm WAT).
    Returns True if we're within the first minute of a merge time.
    """
    now_wat = get_current_wat_time()
    current_time = now_wat.time()

    for merge_time in MERGE_TIMES:
        # Check if current time is within 1 minute of a merge time
        merge_hour = merge_time.hour
        merge_minute = merge_time.minute

        if (current_time.hour == merge_hour and
            merge_minute <= current_time.minute < merge_minute + 1):
            return True

    return False


def is_within_join_window() -> bool:
    """
    Check if current time is within the 5-minute join window after a merge time.
    Join window starts at merge time and lasts 5 minutes.
    """
    now_wat = get_current_wat_time()
    current_time = now_wat.time()

    for merge_time in MERGE_TIMES:
        merge_hour = merge_time.hour
        merge_minute = merge_time.minute

        # Calculate join window end time
        window_end = (datetime.combine(now_wat.date(), merge_time) +
                     timedelta(minutes=JOIN_WINDOW_MINUTES)).time()

        # Check if we're between merge time and window end
        if merge_time <= current_time < window_end:
            return True

    return False


def get_current_merge_window_info() -> Optional[dict]:
    """
    Get information about the current merge window if we're in one.

    Returns:
        dict with merge_time, window_closes, seconds_remaining, or None if not in window
    """
    if not is_within_join_window():
        return None

    now_wat = get_current_wat_time()
    current_time = now_wat.time()

    for merge_time in MERGE_TIMES:
        merge_hour = merge_time.hour
        merge_minute = merge_time.minute

        # Calculate join window end time
        merge_datetime = datetime.combine(now_wat.date(), merge_time)
        window_closes_datetime = merge_datetime + timedelta(minutes=JOIN_WINDOW_MINUTES)
        window_closes = window_closes_datetime.time()

        # Check if we're between merge time and window end
        if merge_time <= current_time < window_closes:
            # Calculate seconds remaining
            now_datetime = datetime.combine(now_wat.date(), current_time)
            seconds_remaining = (window_closes_datetime - now_datetime).total_seconds()

            return {
                'merge_time_wat': merge_datetime.strftime('%I:%M %p WAT'),
                'window_closes_wat': window_closes_datetime.strftime('%I:%M %p WAT'),
                'seconds_remaining': int(seconds_remaining),
                'merge_time_utc': merge_datetime.astimezone(pytz.utc).replace(tzinfo=None),
                'window_closes_utc': window_closes_datetime.astimezone(pytz.utc).replace(tzinfo=None)
            }

    return None


def format_next_merge_time() -> str:
    """Get human-readable string for next merge time."""
    merge_time_utc, _ = get_next_merge_time()
    merge_time_wat = pytz.utc.localize(merge_time_utc).astimezone(WAT)
    return merge_time_wat.strftime('%I:%M %p WAT on %B %d, %Y')
