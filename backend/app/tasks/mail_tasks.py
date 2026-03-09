"""
邮件任务 (Mail Tasks)

职责边界：
  - 在 Celery 中异步发送邮件
  - 处理重试与错误隔离，避免主流程阻塞
"""

from app.tasks.celery_app import celery_app
from app.services.mail import (
    MailConfigurationError,
    MailDeliveryError,
    OutboundEmail,
    build_outbound_defaults,
    get_mail_service,
)


@celery_app.task(bind=True, max_retries=3)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    reply_to: str | None = None,
):
    defaults = build_outbound_defaults()
    email = OutboundEmail(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        reply_to=reply_to,
        from_email=defaults["from_email"],
        from_name=defaults["from_name"],
    )
    service = get_mail_service()

    try:
        service.send_email(email)
        return {"status": "sent", "to": to_email}
    except MailConfigurationError as exc:
        return {"status": "skipped", "reason": str(exc)}
    except MailDeliveryError as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
