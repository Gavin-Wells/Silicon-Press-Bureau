from abc import ABC, abstractmethod

from app.services.mail.schemas import OutboundEmail


class MailProvider(ABC):
    """邮件基础设施接口，便于替换 SMTP/第三方平台。"""

    @abstractmethod
    def send(self, email: OutboundEmail) -> None:
        """发送邮件，失败时抛出领域异常。"""
