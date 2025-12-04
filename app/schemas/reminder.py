from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone

Method = Literal["email", "sms"]

class ReminderCreateRequest(BaseModel):
    title: str = Field(
        ...,
        description="Title of the reminder",
        min_length=1,
        max_length=120,
        json_schema_extra={"example": "Doctor Appointment"}
    )
    message: str = Field(
        ...,
        description="Detailed message for the reminder",
        min_length=1,
        max_length=1000,
        json_schema_extra={"example": "You have a follow-up appointment tomorrow at 10 AM."}
    )
    delivery_time: str = Field(
        ...,
        description="When to deliver the reminder (ISO 8601 format)",
        json_schema_extra={"example": "2025-09-26T10:00:00Z"}
    )
    method: Method = Field(
        default="email",
        description="Method to deliver the reminder",
        json_schema_extra={"example": "email"}
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for the reminder",
        json_schema_extra={"example": "UTC"}
    )
    reminder_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the reminder",
        json_schema_extra={"example": {"to": "patient@example.com"}}
    )

    @field_validator("delivery_time")
    @classmethod
    def validate_iso(cls, v: str) -> str:
        try:
            if v.endswith("Z"):
                v = v.replace("Z", "+00:00")
            dt = datetime.fromisoformat(v)
            _ = dt.astimezone(timezone.utc)
        except Exception as e:
            raise ValueError("delivery_time must be ISO 8601") from e
        return v


# ✅ Internal schema (system uses this, includes user_id)
class ReminderCreate(ReminderCreateRequest):
    user_id: Optional[str] = Field(
        None,
        description="Unique identifier for the user (injected automatically for normal users, optional for admin)",
        min_length=3,
        max_length=256,
        json_schema_extra={"example": "8f6c7e5a-2b41-4ad1-9a52-bb7f6a123456"}
    )


# ✅ New schema for updates (all fields optional)
class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        description="Updated title of the reminder",
        min_length=1,
        max_length=120,
        json_schema_extra={"example": "Updated Doctor Appointment"}
    )
    message: Optional[str] = Field(
        None,
        description="Updated detailed message for the reminder",
        min_length=1,
        max_length=1000,
        json_schema_extra={"example": "Your appointment has been rescheduled to 11 AM."}
    )
    delivery_time: Optional[str] = Field(
        None,
        description="Updated delivery time (ISO 8601 format)",
        json_schema_extra={"example": "2025-09-26T11:00:00Z"}
    )
    method: Optional[Method] = Field(
        None,
        description="Updated delivery method",
        json_schema_extra={"example": "sms"}
    )
    timezone: Optional[str] = Field(
        None,
        description="Updated timezone",
        json_schema_extra={"example": "UTC"}
    )
    reminder_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated additional metadata for the reminder",
        json_schema_extra={"example": {"to": "+1234567890"}}
    )


class ReminderOut(BaseModel):
    id: str = Field(description="Unique identifier of the reminder")
    user_id: str = Field(description="ID of the user who owns this reminder")
    title: str = Field(description="Title of the reminder")
    message: str = Field(description="Detailed message of the reminder")
    delivery_time: str = Field(description="When the reminder will be delivered")
    method: str = Field(description="Delivery method (email/sms)")
    status: str = Field(
        description="Current status of the reminder",
        examples=["scheduled", "sent", "failed", "cancelled"]
    )
    reminder_metadata: Dict[str, Any] = Field(
        description="Additional metadata associated with the reminder"
    )
    created_at: str = Field(description="When the reminder was created")


class CancelOut(BaseModel):
    message: str
