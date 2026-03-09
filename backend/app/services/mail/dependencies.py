from functools import lru_cache

from app.core.config import settings
from app.services.mail.providers.smtp_provider import SmtpMailProvider
from app.services.mail.service import MailService


@lru_cache
def get_mail_service() -> MailService:
    provider = SmtpMailProvider(
        host=settings.MAIL_SERVER_SMTP,
        port=settings.MAIL_SERVER_SMTP_PORT,
        username=settings.MAIL_USERNAME,
        password=settings.MAIL_PASSWORD,
        use_ssl=settings.MAIL_SERVER_SMTP_SSL,
        timeout_seconds=settings.MAIL_TIMEOUT_SECONDS,
    )
    return MailService(provider=provider, enabled=settings.MAIL_ENABLED)


def build_outbound_defaults() -> dict:
    from_email = settings.MAIL_FROM_ADDRESS or settings.MAIL_USERNAME
    return {
        "from_email": from_email,
        "from_name": settings.MAIL_FROM_NAME,
    }
