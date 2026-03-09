from pydantic import BaseModel, Field


class EmailAttachment(BaseModel):
    """邮件附件（通过 base64 传输，便于任务队列序列化）。"""

    filename: str = Field(..., min_length=1, max_length=255)
    content_base64: str = Field(..., min_length=1)
    mime_type: str = Field(default="application/octet-stream", min_length=3, max_length=120)


class OutboundEmail(BaseModel):
    """标准化的邮件发送请求。"""

    to_email: str = Field(..., min_length=3, max_length=320)
    subject: str = Field(..., min_length=1, max_length=200)
    body_text: str = Field(..., min_length=1)
    body_html: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    attachments: list[EmailAttachment] = Field(default_factory=list)
