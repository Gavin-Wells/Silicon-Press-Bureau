import smtplib
import ssl
from email.message import EmailMessage

from app.services.mail.exceptions import MailConfigurationError, MailDeliveryError
from app.services.mail.providers.base import MailProvider
from app.services.mail.schemas import OutboundEmail


class SmtpMailProvider(MailProvider):
    """基于标准库 smtplib 的 SMTP 发送实现。"""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = True,
        timeout_seconds: int = 10,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.timeout_seconds = timeout_seconds

    def send(self, email: OutboundEmail) -> None:
        if not self.host or not self.port:
            raise MailConfigurationError("SMTP 服务地址未配置")
        if not self.username or not self.password:
            raise MailConfigurationError("SMTP 账号或密码未配置")

        message = self._build_message(email)
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout_seconds,
                    context=context,
                ) as smtp:
                    smtp.login(self.username, self.password)
                    smtp.send_message(message)
                return

            with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as smtp:
                context = ssl.create_default_context()
                smtp.starttls(context=context)
                smtp.login(self.username, self.password)
                smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise MailDeliveryError(f"SMTP 发送失败: {exc}") from exc

    @staticmethod
    def _build_message(email: OutboundEmail) -> EmailMessage:
        if not email.from_email:
            raise MailConfigurationError("发件人地址未配置")

        message = EmailMessage()
        message["To"] = email.to_email
        message["Subject"] = email.subject

        sender = email.from_email
        if email.from_name:
            sender = f"{email.from_name} <{email.from_email}>"
        message["From"] = sender

        if email.reply_to:
            message["Reply-To"] = email.reply_to

        message.set_content(email.body_text)
        if email.body_html:
            message.add_alternative(email.body_html, subtype="html")
        return message
