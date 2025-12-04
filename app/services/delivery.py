
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Any
from twilio.rest import Client
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

def _has_smtp():
    return all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASS])

def _has_twilio():
    return all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM])

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def send_email(to_email: str, subject: str, body: str) -> bool:
    if not _has_smtp():
        print(f"[FAKE EMAIL] to={to_email} subject={subject}")
        return True
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())
    return True

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def send_sms(to_number: str, subject: str, body: str) -> bool:
    if not _has_twilio():
        print(f"[FAKE SMS] to={to_number} body={subject} - {body}")
        return True
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(body=f"{subject} - {body}", from_=settings.TWILIO_FROM, to=to_number)
    print(f"[SMS SID] {message.sid}")
    return True

def deliver(rem: Dict[str, Any]) -> bool:
    method = rem.get("method", "email")
    if method == "email":
        return send_email(rem["user_id"], rem["title"], rem["message"])
    if method == "sms":
        return send_sms(rem["user_id"], rem["title"], rem["message"])
    print(f"[DELIVERY ERROR] Unsupported method: {method}")
    return False
