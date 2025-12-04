
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, Text, String, select, update, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy.types import JSON as SA_JSON
from app.config import settings

class Base(DeclarativeBase):
    pass

class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_time: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String, nullable=False, default="UTC")
    method: Mapped[str] = mapped_column(String, nullable=False)
    reminder_metadata: Mapped[Dict[str, Any]] = mapped_column(SA_JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)

engine = create_engine(settings.DATABASE_URL, echo=False, future=True)
Base.metadata.create_all(engine)

def insert_reminder(rec: Dict[str, Any]) -> None:
    with Session(engine) as s:
        s.add(Reminder(**rec))
        s.commit()

def update_status(rem_id: str, status: str) -> None:
    with Session(engine) as s:
        s.execute(update(Reminder).where(Reminder.id==rem_id).values(status=status))
        s.commit()

def get(rem_id: str) -> Optional[Dict[str, Any]]:
    with Session(engine) as s:
        obj = s.get(Reminder, rem_id)
        return None if obj is None else obj.__dict__ | {}

def exists(rem_id: str) -> bool:
    with Session(engine) as s:
        obj = s.get(Reminder, rem_id)
        return obj is not None

def list_reminders(user_id: str, limit: int = 50, offset: int = 0, is_admin: bool = False) -> List[Dict[str, Any]]:
    with Session(engine) as s:
        stmt = select(Reminder).order_by(Reminder.created_at.desc()).limit(limit).offset(offset)
        if not is_admin:
            stmt = stmt.where(Reminder.user_id == user_id)
        rows = s.scalars(stmt).all()
        return [r.__dict__ | {} for r in rows]

def fetch_due(upto_iso: str) -> List[Dict[str, Any]]:
    with Session(engine) as s:
        stmt = select(Reminder).where(Reminder.status=="scheduled", Reminder.delivery_time <= upto_iso)
        rows = s.scalars(stmt).all()
        return [r.__dict__ | {} for r in rows]

def cleanup_old_reminders(days_old: int = 30) -> int:
    from sqlalchemy import text
    with Session(engine) as s:
        # SQLite and Postgres both understand now and interval-ish via julianday/now(); use a generic string compare fallback
        q = text("""
            DELETE FROM reminders
            WHERE created_at < strftime('%Y-%m-%dT%H:%M:%fZ', datetime('now', :delta))
        """)
        # For Postgres, we'll fallback to simple comparison by passing ISO cutoff from Python if needed.
        try:
            res = s.execute(q, {"delta": f"-{days_old} days"})
            s.commit()
            return getattr(res, "rowcount", 0) or 0
        except Exception:
            # Fallback portable way
            from datetime import datetime, timedelta, timezone
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
            stmt = delete(Reminder).where(Reminder.created_at < cutoff)
            res = s.execute(stmt)
            s.commit()
            return getattr(res, "rowcount", 0) or 0


def update_reminder(rem_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update arbitrary fields of a reminder."""
    with Session(engine) as s:
        stmt = (
            update(Reminder)
            .where(Reminder.id == rem_id)
            .values(**fields)
            .returning(Reminder)
        )
        res = s.execute(stmt).fetchone()
        s.commit()
        if res:
            # SQLAlchemy row returns model instance
            obj = res[0]
            return obj.__dict__ | {}
        return None
