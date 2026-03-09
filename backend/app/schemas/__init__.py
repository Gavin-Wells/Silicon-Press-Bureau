"""
Pydantic Schemas — API 请求/响应数据模型

解耦原则：
  - Create schemas: 用于接收用户输入
  - Response schemas: 用于返回给前端
  - Internal schemas: 用于服务间传递（不暴露给前端）
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import Optional, List, Dict, Literal, Any


# ═══════════════════════════════════════════════
#  板块 (Section)
# ═══════════════════════════════════════════════

class ScoringDimensionResponse(BaseModel):
    name: str
    weight: float
    description: str


class SectionResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    min_chars: int
    max_chars: int
    is_user_submittable: bool
    scoring_dimensions: Optional[List[ScoringDimensionResponse]] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
#  投稿 (Submission)
# ═══════════════════════════════════════════════

class SubmissionCreate(BaseModel):
    """用户创建投稿"""
    newspaper_slug: str = Field(..., description="报纸标识")
    section_slug: str = Field(..., description="板块标识")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    pen_name: str = Field(default="匿名", max_length=50)
    contact_email: Optional[str] = Field(default=None, max_length=320, description="可选联系邮箱")

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("标题不能为空")
        return v.strip()

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()

    @field_validator("contact_email")
    @classmethod
    def validate_contact_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip()
        if not normalized:
            return None
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("邮箱格式不正确")
        return normalized


class SubmissionCompareRequest(BaseModel):
    """同稿多编辑评审请求"""
    newspaper_slug: str = Field(..., description="报纸标识")
    section_slug: str = Field(..., description="板块标识")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    editor_keys: Optional[List[str]] = Field(
        default=None,
        description="可选：指定参与评审的编辑模型 key 列表；不传则使用系统默认配置"
    )

    @field_validator('title')
    @classmethod
    def compare_title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("标题不能为空")
        return v.strip()

    @field_validator('content')
    @classmethod
    def compare_content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()

    @field_validator("editor_keys")
    @classmethod
    def normalize_editor_keys(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        normalized = [item.strip() for item in v if item and item.strip()]
        return normalized or None


class SubmissionResponse(BaseModel):
    """投稿详情响应"""
    id: int
    title: str
    content: str
    pen_name: str
    contact_email: Optional[str] = None
    char_count: Optional[int] = None
    status: str
    newspaper_slug: Optional[str] = None
    section_name: Optional[str] = None
    newspaper_name: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    review: Optional["ReviewResponse"] = None

    class Config:
        from_attributes = True


class SubmissionBriefResponse(BaseModel):
    """投稿列表简略响应"""
    id: int
    title: str
    content: Optional[str] = None
    pen_name: str
    char_count: Optional[int] = None
    status: str
    newspaper_slug: Optional[str] = None
    score: Optional[int] = None
    section_name: Optional[str] = None
    newspaper_name: Optional[str] = None
    rejection_reason: Optional[str] = None
    submitted_at: datetime

    class Config:
        from_attributes = True


class ModelReviewComparison(BaseModel):
    editor_key: str
    editor_name: str
    score: Optional[int] = None
    passed: bool
    verdict: str
    threshold: int
    dimension_scores: Optional[Dict[str, int]] = None
    feedback: Optional[str] = None
    error: Optional[str] = None


class SubmissionCompareResponse(BaseModel):
    newspaper_slug: str
    newspaper_name: str
    section_slug: str
    section_name: str
    editor_count: int
    reviews: List[ModelReviewComparison]


# ═══════════════════════════════════════════════
#  审稿 (Review)
# ═══════════════════════════════════════════════

class ReviewResponse(BaseModel):
    """审稿结果"""
    total_score: int
    dimension_scores: Optional[Dict[str, int]] = None
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
#  退稿信 (Rejection)
# ═══════════════════════════════════════════════

class RejectionResponse(BaseModel):
    id: int
    letter_content: str
    letter_style: Optional[str] = None
    is_featured: bool = False
    vote_count: int = 0
    submission_title: Optional[str] = None
    submission_pen_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
#  报纸 (Newspaper)
# ═══════════════════════════════════════════════

class NewspaperResponse(BaseModel):
    id: int
    name: str
    slug: str
    editor_name: str
    editor_persona: Optional[str] = None
    pass_threshold: int

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
#  每日报纸 (DailyIssue)
# ═══════════════════════════════════════════════

class DailyIssueResponse(BaseModel):
    id: int
    issue_date: date
    issue_number: Optional[int] = None
    template_used: Optional[str] = None
    article_count: int
    editor_message: Optional[str] = None
    layout_data: Optional[dict] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IssueMetaResponse(BaseModel):
    newspaper_name: str
    newspaper_slug: str
    issue_date: date
    issue_number: Optional[int] = None
    template_used: Optional[str] = None
    article_count: int = 0
    editor_message: Optional[str] = None
    published_at: Optional[datetime] = None


class LiveIssueResponse(BaseModel):
    """
    直播页统一响应：
      - published: 有已发布版面
      - pending_publish: 暂无已发布版面（可展示“正在编排”）
    """
    status: Literal["published", "pending_publish"]
    newspaper_slug: str
    issue_meta: Optional[IssueMetaResponse] = None
    pages: List[Dict[str, Any]] = Field(default_factory=list)


# ═══════════════════════════════════════════════
#  内部数据模型（服务间传递，不暴露给 API）
# ═══════════════════════════════════════════════

class ReviewResult(BaseModel):
    """审稿 Agent 的内部输出格式"""
    total_score: int
    dimension_scores: Dict[str, int]
    feedback: str
    raw_response: str


class EditResult(BaseModel):
    """编辑 Agent 的内部输出格式"""
    edited_title: str
    edited_content: str
    importance: str = "brief"
    editor_note: str = ""


# ═══════════════════════════════════════════════
#  用户 (User)
# ═══════════════════════════════════════════════

class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="登录名")
    password: str = Field(..., min_length=4, max_length=64, description="密码（至少 4 位）")
    pen_name: Optional[str] = Field(default=None, max_length=50, description="默认笔名")
    email: Optional[str] = Field(default=None, max_length=100, description="可选邮箱")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not normalized:
            raise ValueError("用户名不能为空")
        return normalized

    @field_validator("pen_name")
    @classmethod
    def normalize_pen_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip()
        return normalized or None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        normalized = v.strip().lower()
        if not normalized:
            return None
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("邮箱格式不正确")
        return normalized


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    pen_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录成功返回：用户信息 + JWT token"""
    user: UserResponse
    access_token: str
