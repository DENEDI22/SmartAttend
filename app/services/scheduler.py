"""Scheduler service: issues time-limited tokens to devices and monitors heartbeats."""
import logging
import uuid
from datetime import datetime, date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database import SessionLocal
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.attendance_token import AttendanceToken
from app.services.mqtt import publish_token

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _issue_tokens():
    """Query active schedule entries and issue tokens for enabled devices.

    Runs every minute. For each matching entry:
    1. Deactivate any previous active tokens for the device
    2. Create a new token with expiry at lesson end
    3. Publish the check-in URL via MQTT
    """
    now = datetime.now()
    today = date.today()
    current_time = now.time()
    weekday = today.weekday()

    db = SessionLocal()
    try:
        # Find schedule entries that are currently active on enabled devices
        entries = (
            db.query(ScheduleEntry)
            .join(Device, Device.id == ScheduleEntry.device_id)
            .filter(
                ScheduleEntry.weekday == weekday,
                ScheduleEntry.start_time <= current_time,
                ScheduleEntry.end_time > current_time,
                Device.is_enabled == True,  # noqa: E712
            )
            .all()
        )

        settings = get_settings()

        for entry in entries:
            device = db.query(Device).filter(Device.id == entry.device_id).first()
            if not device:
                continue

            # Deactivate previous active tokens for this device
            db.query(AttendanceToken).filter(
                AttendanceToken.device_id == device.id,
                AttendanceToken.is_active == True,  # noqa: E712
            ).update({"is_active": False})

            # Create new token
            token_str = str(uuid.uuid4())
            token = AttendanceToken(
                token=token_str,
                device_id=device.id,
                schedule_entry_id=entry.id,
                lesson_date=today,
                is_active=True,
                created_at=now,
                expires_at=datetime.combine(today, entry.end_time),
            )
            db.add(token)
            db.commit()

            # Publish token URL to device via MQTT
            url = f"http://{settings.server_ip}/checkin?token={token_str}"
            publish_token(device.device_id, url)
            logger.info("Issued token for device %s: %s", device.device_id, url)

    except Exception:
        db.rollback()
        logger.exception("Error issuing tokens")
    finally:
        db.close()


def _check_heartbeats():
    """Mark devices as offline if their last_seen exceeds the 90-second threshold.

    Runs every 30 seconds (checks twice per 90s window for timely detection).
    """
    threshold = datetime.now() - timedelta(seconds=90)
    db = SessionLocal()
    try:
        db.query(Device).filter(
            Device.is_online == True,  # noqa: E712
            Device.last_seen < threshold,
        ).update({"is_online": False})
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error checking heartbeats")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler with token issuance and heartbeat jobs."""
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _issue_tokens,
        trigger=IntervalTrigger(minutes=1),
        id="issue_tokens",
        max_instances=1,
    )
    _scheduler.add_job(
        _check_heartbeats,
        trigger=IntervalTrigger(seconds=30),
        id="check_heartbeats",
        max_instances=1,
    )
    _scheduler.start()
    logger.info("Scheduler started with token issuance (1min) and heartbeat check (30s)")


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
