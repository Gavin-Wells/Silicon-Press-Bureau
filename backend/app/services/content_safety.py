"""
内容安全策略（审稿前置）

- 在进入模型审稿前先做关键字拦截
- 当前重点：中文语境下的政治人物/政治事件相关内容
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class SafetyCheckResult:
    blocked: bool
    reason: str | None = None


_POLITICAL_KEYWORDS = {
    "政治人物": [
        "国家主席",
        "总书记",
        "总理",
        "国务院总理",
        "政治局",
        "政治局常委",
        "中央委员会",
        "人大委员长",
        "中纪委",
        "中组部",
    ],
    "政治机构": [
        "党中央",
        "国务院",
        "全国人大",
        "政协",
        "党代会",
        "人大常委会",
        "政府机关",
        "党委",
        "纪委",
    ],
    "政治事件": [
        "选举舞弊",
        "政变",
        "颠覆政权",
        "暴乱",
        "游行示威",
        "集会抗议",
        "罢工运动",
        "街头政治",
        "颜色革命",
    ],
    "敏感议题": [
        "台独",
        "港独",
        "疆独",
        "藏独",
        "分裂国家",
        "推翻政府",
        "反政府组织",
        "煽动颠覆",
    ],
}

# 事件/口号类补充规则（正则）
_POLITICAL_PATTERNS = [
    re.compile(r"六四|天安门事件|89学运", re.IGNORECASE),
    re.compile(r"独立(?:运动|公投)?|自治(?:运动)?", re.IGNORECASE),
    re.compile(r"游行|示威|抗议|维权", re.IGNORECASE),
]


def _find_political_hits(text: str) -> list[str]:
    hits: list[str] = []
    lowered = text.lower()
    for category, words in _POLITICAL_KEYWORDS.items():
        for word in words:
            if word.lower() in lowered:
                hits.append(f"{category}:{word}")
    for pattern in _POLITICAL_PATTERNS:
        if pattern.search(text):
            hits.append(f"模式:{pattern.pattern}")
    # 去重并保留顺序
    seen = set()
    unique_hits: list[str] = []
    for h in hits:
        if h in seen:
            continue
        seen.add(h)
        unique_hits.append(h)
    return unique_hits


def check_submission_content_safety(title: str, content: str) -> SafetyCheckResult:
    """
    审稿前内容安全检查。
    命中策略时返回 blocked=True，调用方应直接拒绝并终止后续审稿流程。
    """
    text = f"{title}\n{content}"
    matched = _find_political_hits(text)
    if matched:
        preview = "、".join(matched[:3])
        return SafetyCheckResult(
            blocked=True,
            reason=f"内容安全策略拦截：检测到政治相关人物/事件话题（命中：{preview}）",
        )

    return SafetyCheckResult(blocked=False, reason=None)

