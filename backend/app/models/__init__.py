from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, JSON, Float, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# ═══════════════════════════════════════════════
#  用户
# ═══════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(64), nullable=True)   # 简单 SHA256 盐哈希，空表示老用户未设密码
    email         = Column(String(100), unique=True)
    pen_name      = Column(String(50))     # 默认笔名
    created_at    = Column(DateTime, server_default=func.now())

    submissions = relationship("Submission", back_populates="user")


# ═══════════════════════════════════════════════
#  报纸
# ═══════════════════════════════════════════════

class Newspaper(Base):
    __tablename__ = "newspapers"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100), nullable=False)       # "Agent先锋报"
    slug           = Column(String(50), unique=True, nullable=False)  # "agent_pioneer"
    editor_name    = Column(String(100))                       # "0xA1"
    editor_persona = Column(Text)                              # 编辑人设 prompt
    pass_threshold = Column(Integer, default=60)               # 过审分数线
    created_at     = Column(DateTime, server_default=func.now())

    submissions = relationship("Submission", back_populates="newspaper")
    issues      = relationship("DailyIssue", back_populates="newspaper")
    config      = relationship("NewspaperConfig", uselist=False, back_populates="newspaper")


class NewspaperConfig(Base):
    __tablename__ = "newspaper_configs"

    id                     = Column(Integer, primary_key=True, index=True)
    newspaper_id           = Column(Integer, ForeignKey("newspapers.id"), unique=True, nullable=False)
    review_prompt          = Column(Text)
    edit_prompt            = Column(Text)
    reject_prompt          = Column(Text)
    scoring_profile        = Column(JSON)
    issue_config           = Column(JSON)
    news_config            = Column(JSON)
    invite_config          = Column(JSON)
    publish_config         = Column(JSON)
    rejection_letter_style = Column(String(50))
    created_at             = Column(DateTime, server_default=func.now())

    newspaper = relationship("Newspaper", back_populates="config")


# ═══════════════════════════════════════════════
#  板块（Section）
# ═══════════════════════════════════════════════

class Section(Base):
    __tablename__ = "sections"

    id                  = Column(Integer, primary_key=True, index=True)
    newspaper_id        = Column(Integer, ForeignKey("newspapers.id"), nullable=False)
    name                = Column(String(50), nullable=False)    # "技术" "诗选"
    slug                = Column(String(50), nullable=False)    # "tech" "poetry"
    description         = Column(Text)
    min_chars           = Column(Integer, default=50)
    max_chars           = Column(Integer, default=500)
    is_user_submittable = Column(Boolean, default=True)
    sort_order          = Column(Integer, default=0)
    scoring_dimensions  = Column(JSON)                          # [{name, weight, description}]

    __table_args__ = (
        UniqueConstraint('newspaper_id', 'slug', name='uq_section_newspaper_slug'),
    )

    newspaper   = relationship("Newspaper")
    submissions = relationship("Submission", back_populates="section")


# ═══════════════════════════════════════════════
#  投稿（Submission）
# ═══════════════════════════════════════════════

class Submission(Base):
    __tablename__ = "submissions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"))
    newspaper_id  = Column(Integer, ForeignKey("newspapers.id"), nullable=False)
    section_id    = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title         = Column(String(200), nullable=False)
    content       = Column(Text, nullable=False)
    pen_name      = Column(String(50), default="匿名")
    contact_email = Column(String(320))
    char_count    = Column(Integer)                # 自动计算
    status        = Column(String(20), default="pending")
    # status 枚举: pending → reviewing → approved / rejected
    submitted_at  = Column(DateTime, server_default=func.now())
    reviewed_at   = Column(DateTime)

    user       = relationship("User", back_populates="submissions")
    newspaper  = relationship("Newspaper", back_populates="submissions")
    section    = relationship("Section", back_populates="submissions")
    review     = relationship("Review", uselist=False, back_populates="submission")
    rejection  = relationship("RejectionLetter", uselist=False, back_populates="submission")
    curated    = relationship("CuratedArticle", uselist=False, back_populates="submission")


# ═══════════════════════════════════════════════
#  审稿评分（Review）— 多维度
# ═══════════════════════════════════════════════

class Review(Base):
    __tablename__ = "reviews"

    id               = Column(Integer, primary_key=True, index=True)
    submission_id    = Column(Integer, ForeignKey("submissions.id"), unique=True)
    agent_type       = Column(String(50))                    # "agent_pioneer" / "shoegaze"
    total_score      = Column(Integer)                       # 加权总分 0-100
    dimension_scores = Column(JSON)                          # {"逻辑严密度": 75, ...}
    feedback         = Column(Text)                          # 详细评语
    raw_response     = Column(Text)                          # LLM 原始返回（debug 用）
    created_at       = Column(DateTime, server_default=func.now())

    submission = relationship("Submission", back_populates="review")


# ═══════════════════════════════════════════════
#  退稿信
# ═══════════════════════════════════════════════

class RejectionLetter(Base):
    __tablename__ = "rejection_letters"

    id               = Column(Integer, primary_key=True, index=True)
    submission_id    = Column(Integer, ForeignKey("submissions.id"), unique=True)
    letter_content   = Column(Text, nullable=False)
    letter_style     = Column(String(20))    # "code_review" / "poetry"
    is_featured      = Column(Boolean, default=False)
    vote_count       = Column(Integer, default=0)   # 退稿信投票数
    created_at       = Column(DateTime, server_default=func.now())

    submission = relationship("Submission", back_populates="rejection")


# ═══════════════════════════════════════════════
#  选稿（编辑润色后，待排版）
# ═══════════════════════════════════════════════

class CuratedArticle(Base):
    __tablename__ = "curated_articles"

    id              = Column(Integer, primary_key=True, index=True)
    submission_id   = Column(Integer, ForeignKey("submissions.id"), unique=True)
    newspaper_id    = Column(Integer, ForeignKey("newspapers.id"), nullable=False)
    section_id      = Column(Integer, ForeignKey("sections.id"), nullable=False)
    edited_title    = Column(String(300))
    edited_content  = Column(Text)
    importance      = Column(String(20), default="brief")   # "headline" / "secondary" / "brief"
    editor_note     = Column(Text)                          # 编辑内部批注
    issue_date      = Column(Date, nullable=False)          # 排入哪天的报纸
    created_at      = Column(DateTime, server_default=func.now())

    submission = relationship("Submission", back_populates="curated")
    newspaper  = relationship("Newspaper")
    section    = relationship("Section")


# ═══════════════════════════════════════════════
#  每日报纸（发布品）
# ═══════════════════════════════════════════════

class DailyIssue(Base):
    __tablename__ = "daily_issues"

    id              = Column(Integer, primary_key=True, index=True)
    newspaper_id    = Column(Integer, ForeignKey("newspapers.id"), nullable=False)
    issue_date      = Column(Date, nullable=False)
    issue_number    = Column(Integer)
    layout_data     = Column(JSON)                  # layoutEngine 的完整输出
    template_used   = Column(String(50))            # 版式模板名
    article_count   = Column(Integer, default=0)
    editor_message  = Column(Text)                  # 当日编辑寄语
    is_published    = Column(Boolean, default=False)
    published_at    = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('newspaper_id', 'issue_date', name='uq_issue_newspaper_date'),
    )

    newspaper = relationship("Newspaper", back_populates="issues")
