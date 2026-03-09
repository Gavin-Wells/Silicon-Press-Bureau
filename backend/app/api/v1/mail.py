from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.mail import (
    MailConfigurationError,
    MailDeliveryError,
    OutboundEmail,
    build_outbound_defaults,
    get_mail_service,
    MailService,
)

router = APIRouter()


class SendMailRequest(BaseModel):
    to_email: str = Field(..., min_length=3, max_length=320)
    subject: str = Field(..., min_length=1, max_length=200)
    body_text: str = Field(..., min_length=1)
    body_html: str | None = None
    reply_to: str | None = None


class SendMailResponse(BaseModel):
    success: bool
    message: str


@router.post("/send", response_model=SendMailResponse)
def send_mail(
    payload: SendMailRequest,
    mail_service: MailService = Depends(get_mail_service),
):
    defaults = build_outbound_defaults()
    email = OutboundEmail(
        to_email=payload.to_email,
        subject=payload.subject,
        body_text=payload.body_text,
        body_html=payload.body_html,
        reply_to=payload.reply_to,
        from_email=defaults["from_email"],
        from_name=defaults["from_name"],
    )
    try:
        mail_service.send_email(email)
    except MailConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except MailDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SendMailResponse(success=True, message="邮件发送成功")
