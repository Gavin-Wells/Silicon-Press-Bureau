from app.services.mail.exceptions import MailConfigurationError
from app.services.mail.providers.base import MailProvider
from app.services.mail.schemas import OutboundEmail


class MailService:
    """应用层邮件服务，封装发送策略与业务约束。"""

    def __init__(self, provider: MailProvider, *, enabled: bool = True) -> None:
        self.provider = provider
        self.enabled = enabled

    def send_email(self, email: OutboundEmail) -> None:
        if not self.enabled:
            raise MailConfigurationError("邮件服务未启用（MAIL_ENABLED=false）")
        self.provider.send(email)
