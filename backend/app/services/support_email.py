"""Plain-text support email provider abstraction with a production fail-closed SMTP implementation."""
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid
import os
import smtplib
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Delivery:
    status: str
    provider_message_id: str


def _sender_configuration() -> tuple[str, str]:
    sender = os.getenv("SUPPORT_EMAIL_FROM", "").strip()
    domain = os.getenv("SUPPORT_EMAIL_VERIFIED_DOMAIN", "").strip().lower()
    if (os.getenv("SUPPORT_EMAIL_SENDER_APPROVED") != "true" or "@" not in sender
            or not domain or sender.rsplit("@", 1)[1].lower() != domain):
        raise RuntimeError("Support sender is not approved")
    return sender, domain


def send_plain_text(*, recipient: str, subject: str, body: str,
                    thread_reference: str | None = None) -> Delivery:
    environment = os.getenv("APP_ENV", "")
    if environment in {"development", "test"}:
        return Delivery("suppressed", "test-" + make_msgid(domain="example.invalid").strip("<>"))
    if environment != "production" or os.getenv("SUPPORT_EMAIL_PROVIDER") != "smtp":
        raise RuntimeError("Production support email provider is unavailable")
    sender, domain = _sender_configuration()
    host = os.getenv("SUPPORT_EMAIL_SMTP_HOST", "").strip()
    username = os.getenv("SUPPORT_EMAIL_SMTP_USERNAME", "")
    password = os.getenv("SUPPORT_EMAIL_SMTP_PASSWORD", "")
    try:
        port = int(os.getenv("SUPPORT_EMAIL_SMTP_PORT", "465"))
    except ValueError:
        raise RuntimeError("Support email provider configuration is invalid") from None
    parsed = urlsplit("//" + host)
    if (not parsed.hostname or parsed.username or parsed.password or parsed.path
            or parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
            or port not in {465, 587} or not username or not password):
        raise RuntimeError("Support email provider configuration is invalid")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message_id = make_msgid(domain=domain)
    message["Message-ID"] = message_id
    if thread_reference:
        safe_reference = thread_reference.strip()
        if "\n" in safe_reference or "\r" in safe_reference:
            raise RuntimeError("Support thread reference is invalid")
        message["In-Reply-To"] = safe_reference
        message["References"] = safe_reference
    message.set_content(body)
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=15) as client:
            client.login(username, password)
            client.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=15) as client:
            client.starttls()
            client.login(username, password)
            client.send_message(message)
    return Delivery("sent", message_id.strip("<>"))
