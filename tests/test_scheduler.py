"""Tests for the scheduler service: token issuance and heartbeat monitoring."""
import uuid
from datetime import date, datetime, time, timedelta
from unittest.mock import patch, MagicMock

import pytest

from app.database import Base
from app.models.device import Device
from app.models.schedule_entry import ScheduleEntry
from app.models.attendance_token import AttendanceToken
from app.models.user import User


class _NonClosingSession:
    """Wraps a real session but makes close() a no-op so tests can still inspect objects."""

    def __init__(self, real):
        self._real = real

    def close(self):
        pass  # no-op: keep session open for test assertions

    def __getattr__(self, name):
        return getattr(self._real, name)


@pytest.fixture
def mock_session_local(db_session):
    """Replace SessionLocal in scheduler module with factory returning the test session."""
    def _factory():
        return _NonClosingSession(db_session)
    return _factory


@pytest.fixture
def fixed_now():
    """Return a datetime that falls within the 08:00-09:30 window."""
    today = date.today()
    return datetime.combine(today, time(8, 30))


@pytest.fixture
def seed_teacher(db_session):
    """Create a teacher user for schedule entry FK."""
    teacher = User(
        email="teacher@test.com",
        first_name="Test",
        last_name="Teacher",
        role="teacher",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def seed_device(db_session):
    """Create an enabled, online device."""
    device = Device(
        device_id="e101",
        is_enabled=True,
        is_online=True,
        last_seen=datetime.now(),
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def seed_schedule_entry(db_session, seed_device, seed_teacher):
    """Create a schedule entry for today, 08:00-09:30."""
    entry = ScheduleEntry(
        device_id=seed_device.id,
        teacher_id=seed_teacher.id,
        class_name="10A",
        weekday=date.today().weekday(),
        start_time=time(8, 0),
        end_time=time(9, 30),
    )
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


class TestIssueTokens:
    """Tests for _issue_tokens scheduler job."""

    def test_issue_tokens_creates_token(
        self, db_session, mock_session_local, seed_device, seed_schedule_entry, fixed_now, monkeypatch
    ):
        """Seed device (enabled) + schedule entry for now, verify token created."""
        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)
        monkeypatch.setattr("app.services.scheduler.datetime", MagicMock(
            now=MagicMock(return_value=fixed_now),
            combine=datetime.combine,
        ))
        monkeypatch.setattr("app.services.scheduler.date", MagicMock(
            today=MagicMock(return_value=fixed_now.date()),
        ))

        with patch("app.services.scheduler.publish_token") as mock_publish:
            from app.services.scheduler import _issue_tokens
            _issue_tokens()

        token = db_session.query(AttendanceToken).first()
        assert token is not None
        assert token.is_active is True
        assert token.device_id == seed_device.id
        assert token.schedule_entry_id == seed_schedule_entry.id

    def test_issue_tokens_skips_disabled_device(
        self, db_session, mock_session_local, seed_device, seed_schedule_entry, fixed_now, monkeypatch
    ):
        """Device with is_enabled=False should not get a token."""
        seed_device.is_enabled = False
        db_session.commit()

        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)
        monkeypatch.setattr("app.services.scheduler.datetime", MagicMock(
            now=MagicMock(return_value=fixed_now),
            combine=datetime.combine,
        ))
        monkeypatch.setattr("app.services.scheduler.date", MagicMock(
            today=MagicMock(return_value=fixed_now.date()),
        ))

        with patch("app.services.scheduler.publish_token"):
            from app.services.scheduler import _issue_tokens
            _issue_tokens()

        token = db_session.query(AttendanceToken).first()
        assert token is None

    def test_issue_tokens_skips_outside_window(
        self, db_session, mock_session_local, seed_device, seed_schedule_entry, monkeypatch
    ):
        """Schedule entry outside current time window should not get a token."""
        outside_now = datetime.combine(date.today(), time(10, 0))  # after 09:30 end

        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)
        monkeypatch.setattr("app.services.scheduler.datetime", MagicMock(
            now=MagicMock(return_value=outside_now),
            combine=datetime.combine,
        ))
        monkeypatch.setattr("app.services.scheduler.date", MagicMock(
            today=MagicMock(return_value=outside_now.date()),
        ))

        with patch("app.services.scheduler.publish_token"):
            from app.services.scheduler import _issue_tokens
            _issue_tokens()

        token = db_session.query(AttendanceToken).first()
        assert token is None

    def test_deactivate_previous_token(
        self, db_session, mock_session_local, seed_device, seed_schedule_entry, fixed_now, monkeypatch
    ):
        """Existing active token should be deactivated when new one is created."""
        old_token = AttendanceToken(
            token=str(uuid.uuid4()),
            device_id=seed_device.id,
            schedule_entry_id=seed_schedule_entry.id,
            lesson_date=date.today(),
            is_active=True,
            created_at=fixed_now - timedelta(minutes=5),
            expires_at=datetime.combine(date.today(), time(9, 30)),
        )
        db_session.add(old_token)
        db_session.commit()

        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)
        monkeypatch.setattr("app.services.scheduler.datetime", MagicMock(
            now=MagicMock(return_value=fixed_now),
            combine=datetime.combine,
        ))
        monkeypatch.setattr("app.services.scheduler.date", MagicMock(
            today=MagicMock(return_value=fixed_now.date()),
        ))

        with patch("app.services.scheduler.publish_token"):
            from app.services.scheduler import _issue_tokens
            _issue_tokens()

        db_session.refresh(old_token)
        assert old_token.is_active is False

        new_token = db_session.query(AttendanceToken).filter(
            AttendanceToken.is_active == True  # noqa: E712
        ).first()
        assert new_token is not None
        assert new_token.id != old_token.id

    def test_token_url_format(
        self, db_session, mock_session_local, seed_device, seed_schedule_entry, fixed_now, monkeypatch
    ):
        """publish_token should be called with correct URL format."""
        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)
        monkeypatch.setattr("app.services.scheduler.datetime", MagicMock(
            now=MagicMock(return_value=fixed_now),
            combine=datetime.combine,
        ))
        monkeypatch.setattr("app.services.scheduler.date", MagicMock(
            today=MagicMock(return_value=fixed_now.date()),
        ))

        with patch("app.services.scheduler.publish_token") as mock_publish:
            from app.services.scheduler import _issue_tokens
            _issue_tokens()

        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        device_id_arg = call_args[0][0]
        url_arg = call_args[0][1]
        assert device_id_arg == "e101"
        assert url_arg.startswith("http://127.0.0.1/checkin?token=")
        # Verify UUID format in URL
        token_str = url_arg.split("token=")[1]
        uuid.UUID(token_str)  # raises if not valid UUID

    def test_token_expiry(
        self, db_session, mock_session_local, seed_device, seed_schedule_entry, fixed_now, monkeypatch
    ):
        """Token expires_at should equal datetime.combine(today, schedule_entry.end_time)."""
        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)
        monkeypatch.setattr("app.services.scheduler.datetime", MagicMock(
            now=MagicMock(return_value=fixed_now),
            combine=datetime.combine,
        ))
        monkeypatch.setattr("app.services.scheduler.date", MagicMock(
            today=MagicMock(return_value=fixed_now.date()),
        ))

        with patch("app.services.scheduler.publish_token"):
            from app.services.scheduler import _issue_tokens
            _issue_tokens()

        token = db_session.query(AttendanceToken).first()
        expected_expiry = datetime.combine(date.today(), time(9, 30))
        assert token.expires_at == expected_expiry


class TestCheckHeartbeats:
    """Tests for _check_heartbeats scheduler job."""

    def test_check_heartbeats_marks_stale_offline(
        self, db_session, mock_session_local, monkeypatch
    ):
        """Device with last_seen > 90s ago should be marked offline."""
        device = Device(
            device_id="stale01",
            is_enabled=True,
            is_online=True,
            last_seen=datetime.now() - timedelta(seconds=100),
        )
        db_session.add(device)
        db_session.commit()

        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)

        from app.services.scheduler import _check_heartbeats
        _check_heartbeats()

        db_session.refresh(device)
        assert device.is_online is False

    def test_check_heartbeats_within_threshold(
        self, db_session, mock_session_local, monkeypatch
    ):
        """Device with last_seen < 90s ago should remain online."""
        device = Device(
            device_id="fresh01",
            is_enabled=True,
            is_online=True,
            last_seen=datetime.now() - timedelta(seconds=30),
        )
        db_session.add(device)
        db_session.commit()

        monkeypatch.setattr("app.services.scheduler.SessionLocal", mock_session_local)

        from app.services.scheduler import _check_heartbeats
        _check_heartbeats()

        db_session.refresh(device)
        assert device.is_online is True
