from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)

    @classmethod
    def get_value(cls, db: Session, key: str, default: str | None = None) -> str | None:
        """Get a setting value by key, returning default if not found."""
        row = db.query(cls).filter(cls.key == key).first()
        return row.value if row else default

    @classmethod
    def set_value(cls, db: Session, key: str, value: str) -> None:
        """Upsert a setting key-value pair."""
        row = db.query(cls).filter(cls.key == key).first()
        if row:
            row.value = value
        else:
            db.add(cls(key=key, value=value))
