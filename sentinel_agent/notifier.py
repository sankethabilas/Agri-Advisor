"""Alert notification delivery subsystem for Outbreak Sentinel.

Provides a pluggable Notifier interface with ConsoleNotifier (default)
and SmsNotifier (Twilio stub).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from sentinel_agent.config import settings

logger = logging.getLogger("sentinel_agent.notifier")


@dataclass
class NotificationMessage:
    audience: str  # 'officer' or 'farmer'
    district: str
    contact: str
    message: str
    language: str
    channel: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseNotifier(ABC):
    """Abstract Base Class for Alert Notifiers."""

    @abstractmethod
    def send(
        self,
        audience: str,
        district: str,
        contact: str,
        message: str,
        language: str = "en",
        channel: str = "sms",
    ) -> bool:
        pass


class ConsoleNotifier(BaseNotifier):
    """Default notifier that logs and records dispatches in-memory for testing and audits."""

    def __init__(self) -> None:
        self.sent_messages: List[NotificationMessage] = []

    def send(
        self,
        audience: str,
        district: str,
        contact: str,
        message: str,
        language: str = "en",
        channel: str = "sms",
    ) -> bool:
        record = NotificationMessage(
            audience=audience,
            district=district,
            contact=contact,
            message=message,
            language=language,
            channel=channel,
        )
        self.sent_messages.append(record)
        logger.info(
            "[ALERT DISPATCHED] Audience=%s | District=%s | Contact=%s | Lang=%s\n%s",
            audience.upper(),
            district,
            contact,
            language,
            message,
        )
        return True

    def clear(self) -> None:
        self.sent_messages.clear()


class SmsNotifier(BaseNotifier):
    """Twilio-style SMS notifier stub."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ) -> None:
        self.account_sid = account_sid or settings.twilio_account_sid
        self.auth_token = auth_token or settings.twilio_auth_token
        self.from_number = from_number or settings.twilio_from_number
        self.console_fallback = ConsoleNotifier()

    def send(
        self,
        audience: str,
        district: str,
        contact: str,
        message: str,
        language: str = "en",
        channel: str = "sms",
    ) -> bool:
        if not (self.account_sid and self.auth_token and self.from_number):
            logger.debug("Twilio credentials not configured; using console logging.")
            return self.console_fallback.send(audience, district, contact, message, language, channel)

        # Truncate to SMS safe limit
        sms_body = message[:320]
        try:
            # Twilio API integration stub
            logger.info("Sending live SMS via Twilio to %s: %s", contact, sms_body)
            return True
        except Exception as err:
            logger.error("Failed to send live SMS via Twilio: %s", err)
            return False


# Singleton instance
default_notifier = ConsoleNotifier()


def get_notifier() -> BaseNotifier:
    if settings.sms_enabled:
        return SmsNotifier()
    return default_notifier
