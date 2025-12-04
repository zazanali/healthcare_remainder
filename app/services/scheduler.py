
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import ConflictingIdError
from typing import Optional

from app.schemas.reminder import ReminderCreate
from app.utils.time import parse_iso_utc, now_utc_iso
from app.services import db, delivery

_scheduler: Optional[BackgroundScheduler] = None

def _deliver(rem_id: str):
    rem = db.get(rem_id)
    if not rem or rem["status"] != "scheduled":
        return
    ok = False
    try:
        ok = delivery.deliver(rem)
    finally:
        db.update_status(rem_id, "sent" if ok else "failed")

def create_reminder(p: ReminderCreate):
    dt_utc = parse_iso_utc(p.delivery_time)
    if dt_utc <= datetime.now(timezone.utc):
        raise ValueError("delivery_time must be in the future (UTC)")
    from uuid import uuid4
    rem_id = str(uuid4())
    rec = {**p.model_dump(), "id": rem_id, "delivery_time": dt_utc.isoformat(), "created_at": now_utc_iso(), "status": "scheduled"}
    db.insert_reminder(rec)
    if _scheduler and _scheduler.running:
        try:
            _scheduler.add_job(_deliver, id=rem_id, trigger="date", run_date=dt_utc, args=[rem_id], replace_existing=False)
        except (ConflictingIdError, AttributeError, ValueError):
            pass
    return rec

def remove_job_safe(rem_id: str):
    if _scheduler and _scheduler.running:
        try:
            _scheduler.remove_job(rem_id)
        except (AttributeError, ValueError):
            pass

def _check_due_fallback():
    now_iso = now_utc_iso()
    for rem in db.fetch_due(now_iso):
        _deliver(rem["id"])

def scheduler_startup():
    global _scheduler
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(_check_due_fallback, "interval", minutes=1)
    _scheduler.add_job(db.cleanup_old_reminders, CronTrigger(hour=0, minute=0))
    _scheduler.start()

def scheduler_shutdown():
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
