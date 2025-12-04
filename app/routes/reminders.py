from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query, status
from app.schemas.reminder import (
    ReminderCreate,
    ReminderCreateRequest,
    ReminderOut,
    CancelOut,
    ReminderUpdate,
)
from app.services import scheduler, db
from app.utils.security import get_current_user, verify_hmac_signature, User

router = APIRouter()

# -----------------------------
# Create a reminder (normal user)
# -----------------------------
@router.post(
    "/reminders",
    response_model=ReminderOut,
    description="Create a new reminder for the authenticated user. Path: /reminders"
)
def create_reminder(payload: ReminderCreateRequest, user: User = Depends(get_current_user)):
    data = ReminderCreate(**payload.model_dump(), user_id=user.id)
    return scheduler.create_reminder(data)


# -----------------------------
# Admin creates reminder for a user
# -----------------------------
from app.utils.security import require_admin

@router.post(
    "/admin/users/{uid}/reminders",
    response_model=ReminderOut,
    description="Admin creates a reminder for a specific user. Path: /admin/users/{uid}/reminders"
)
def admin_create_reminder(
    uid: str,
    payload: ReminderCreateRequest,
    admin: User = Depends(require_admin)   #  Now it will only be accessible by admin
):
    data = ReminderCreate(**payload.model_dump(), user_id=uid)
    return scheduler.create_reminder(data)



# -----------------------------
# List reminders
# -----------------------------
@router.get(
    "/users/{uid}/reminders",
    response_model=List[ReminderOut],
    description="List reminders for a user. Path: /users/{uid}/reminders"
)
def list_reminders(
    uid: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user)
):
    is_admin = user.role == "admin"

    if not is_admin and uid != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return db.list_reminders(uid, limit=limit, offset=offset, is_admin=is_admin)


# -----------------------------
# Cancel reminder
# -----------------------------
@router.post(
    "/reminders/{rem_id}/cancel",
    response_model=CancelOut,
    description="Cancel a reminder by ID. Path: /reminders/{rem_id}/cancel"
)
def cancel_reminder(rem_id: str, user: User = Depends(get_current_user)):
    reminder = db.get(rem_id)
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    if user.role == "admin" or reminder["user_id"] == user.id:
        scheduler.remove_job_safe(rem_id)
        db.update_status(rem_id, "cancelled")
        return {"message": f"Reminder {rem_id} cancelled"}

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


# -----------------------------
# Trigger via webhook
# -----------------------------
@router.post(
    "/webhooks/trigger_reminder",
    response_model=ReminderOut,
    description="Trigger a reminder via webhook. Path: /webhooks/trigger_reminder"
)
async def webhook_trigger(
    request: Request,
    x_signature: str = Header(default=""),
    user: User = Depends(get_current_user)
):
    body = await request.body()
    if not verify_hmac_signature(body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = ReminderCreate.model_validate_json(body.decode())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    payload.user_id = user.id
    return scheduler.create_reminder(payload)


# -----------------------------
# Update reminder
# -----------------------------

@router.put("/reminders/{rem_id}", response_model=dict)
def update_reminder(rem_id: str, payload: ReminderUpdate, user: User = Depends(get_current_user)):
    reminder = db.get(rem_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    if user.role == "admin" or reminder["user_id"] == user.id:
        updated_data = payload.model_dump(exclude_none=True)
        db.update_reminder(rem_id, updated_data)
        return {"message": f"Reminder {rem_id} updated successfully",}

    raise HTTPException(status_code=403, detail="Not authorized")




@router.get("/reminders/{rem_id}", response_model=ReminderOut)
def get_reminder(rem_id: str, user: User = Depends(get_current_user)):
    reminder = db.get(rem_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    # Admin can view any reminder, users only their own
    if user.role == "admin" or reminder["user_id"] == user.id:
        return reminder
    raise HTTPException(status_code=403, detail="Not authorized")