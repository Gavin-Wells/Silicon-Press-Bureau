from pydantic import BaseModel, Field


class OutboundEmail(BaseModel):
    """标准化的邮件发送请求。"""

    to_email: str = Field(..., min_length=3, max_length=320)
    subject: str = Field(..., min_length=1, max_length=200)
    body_text: str = Field(..., min_length=1)
    body_html: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
