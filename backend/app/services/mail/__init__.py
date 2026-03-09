from app.services.mail.dependencies import build_outbound_defaults, get_mail_service
from app.services.mail.exceptions import (
    MailConfigurationError,
    MailDeliveryError,
    MailError,
)
from app.services.mail.schemas import OutboundEmail, EmailAttachment
from app.services.mail.service import MailService

__all__ = [
    "OutboundEmail",
    "EmailAttachment",
    "MailService",
    "MailError",
    "MailConfigurationError",
    "MailDeliveryError",
    "get_mail_service",
    "build_outbound_defaults",
]
