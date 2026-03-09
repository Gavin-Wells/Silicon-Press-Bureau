from __future__ import annotations

from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Iterable, List
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search?q="
HN_SEARCH_API = "https://hn.algolia.com/api/v1/search_by_date"
GITHUB_COMMITS_API = "https://api.github.com/repos/{repo}/commits"


def fetch_live_news_briefs(
    newspaper_slug: str,
    newspaper_name: str | None = None,
    editor_persona: str | None = None,
    section_names: Iterable[str] | None = None,
    news_config: dict | None = None,
    max_items: int = 8,
    timeout_seconds: int = 8,
) -> List[dict]:
    max_items = max(1, min(20, int(max_items)))
    timeout_seconds = max(2, int(timeout_seconds))

    keywords = _build_google_news_keywords(
        newspaper_slug=newspaper_slug,
        newspaper_name=newspaper_name,
        editor_persona=editor_persona,
        section_names=section_names,
        news_config=news_config,
    )
    query = quote_plus(f"{keywords} when:1d")
    feed_url = f"{GOOGLE_NEWS_RSS_BASE}{query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"

    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True, trust_env=False) as client:
            resp = client.get(feed_url)
            resp.raise_for_status()
            parsed = _parse_rss(resp.text, max_items)
            if parsed:
                return parsed
    except Exception:
        pass

    hn_items = _fetch_hn_fallback(
        newspaper_slug,
        newspaper_name=newspaper_name,
        editor_persona=editor_persona,
        section_names=section_names,
        news_config=news_config,
        max_items=max_items,
        timeout_seconds=timeout_seconds,
    )
    if hn_items:
        return hn_items

    return _fetch_github_fallback(
        newspaper_slug,
        newspaper_name=newspaper_name,
        editor_persona=editor_persona,
        section_names=section_names,
        news_config=news_config,
        max_items=max_items,
        timeout_seconds=timeout_seconds,
    )


def _build_google_news_keywords(
    newspaper_slug: str,
    newspaper_name: str | None,
    editor_persona: str | None,
    section_names: Iterable[str] | None,
    news_config: dict | None,
) -> str:
    if isinstance(news_config, dict) and str(news_config.get("google_keywords", "")).strip():
        return str(news_config["google_keywords"]).strip()
    terms = _collect_terms(newspaper_slug, newspaper_name, editor_persona, section_names)
    if not terms:
        return "热点 新闻"
    return " OR ".join(terms[:6])


def _build_hn_query(
    newspaper_slug: str,
    newspaper_name: str | None,
    editor_persona: str | None,
    section_names: Iterable[str] | None,
    news_config: dict | None,
) -> str:
    if isinstance(news_config, dict) and str(news_config.get("hn_query", "")).strip():
        return str(news_config["hn_query"]).strip()
    terms = _collect_terms(newspaper_slug, newspaper_name, editor_persona, section_names)
    ascii_terms = [term for term in terms if term.isascii()]
    if ascii_terms:
        return " OR ".join(ascii_terms[:4])
    return "technology OR culture OR media OR trend"


def _collect_terms(
    newspaper_slug: str,
    newspaper_name: str | None,
    editor_persona: str | None,
    section_names: Iterable[str] | None,
) -> List[str]:
    candidates = [
        *[part for part in newspaper_slug.replace("-", "_").split("_") if part],
        newspaper_name or "",
        *list(section_names or []),
    ]
    if editor_persona:
        candidates.extend(editor_persona.replace("，", " ").replace("。", " ").split())

    normalized: List[str] = []
    seen = set()
    stop_words = {"日报", "报", "报刊", "编辑部", "AI", "ai"}
    for item in candidates:
        text = str(item).strip()
        if len(text) < 2 or text in stop_words:
            continue
        if text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def _parse_rss(rss_text: str, max_items: int) -> List[dict]:
    root = ElementTree.fromstring(rss_text)
    channel = root.find("channel")
    if channel is None:
        return []

    items = channel.findall("item")
    result = []
    for idx, item in enumerate(items[:max_items]):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source = ""
        source_node = item.find("source")
        if source_node is not None:
            source = (source_node.text or "").strip()
        source = source or "Google News"

        if not title or not link:
            continue

        result.append(
            {
                "id": f"N{idx + 1}",
                "title": title,
                "url": link,
                "source": source,
                "published_at": _normalize_pub_date(pub_date),
            }
        )
    return result


def _normalize_pub_date(value: str) -> str:
    if not value:
        return ""
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return value


def _fetch_hn_fallback(
    newspaper_slug: str,
    newspaper_name: str | None,
    editor_persona: str | None,
    section_names: Iterable[str] | None,
    news_config: dict | None,
    max_items: int,
    timeout_seconds: int,
) -> List[dict]:
    query = _build_hn_query(newspaper_slug, newspaper_name, editor_persona, section_names, news_config)

    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True, trust_env=False) as client:
            resp = client.get(
                HN_SEARCH_API,
                params={"query": query, "tags": "story", "hitsPerPage": max_items},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    hits = data.get("hits", []) if isinstance(data, dict) else []
    result = []
    for idx, hit in enumerate(hits[:max_items]):
        if not isinstance(hit, dict):
            continue
        title = (hit.get("title") or hit.get("story_title") or "").strip()
        url = (hit.get("url") or hit.get("story_url") or "").strip()
        published_at = (hit.get("created_at") or "").strip()
        if not title or not url:
            continue
        result.append(
            {
                "id": f"N{idx + 1}",
                "title": title,
                "url": url,
                "source": "Hacker News",
                "published_at": published_at,
            }
        )
    return result


def _fetch_github_fallback(
    newspaper_slug: str,
    newspaper_name: str | None,
    editor_persona: str | None,
    section_names: Iterable[str] | None,
    news_config: dict | None,
    max_items: int,
    timeout_seconds: int,
) -> List[dict]:
    repo_pool = _select_repo_pool(newspaper_slug, newspaper_name, editor_persona, section_names, news_config)

    out: List[dict] = []
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True, trust_env=False) as client:
            for repo in repo_pool:
                if len(out) >= max_items:
                    break
                resp = client.get(GITHUB_COMMITS_API.format(repo=repo), params={"per_page": 2})
                if resp.status_code != 200:
                    continue
                rows = resp.json()
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if len(out) >= max_items:
                        break
                    if not isinstance(row, dict):
                        continue
                    sha = str(row.get("sha", "")).strip()
                    commit = row.get("commit", {}) if isinstance(row.get("commit"), dict) else {}
                    author_obj = commit.get("author", {}) if isinstance(commit.get("author"), dict) else {}
                    message = str(commit.get("message", "")).split("\n", 1)[0].strip()
                    html_url = str(row.get("html_url", "")).strip()
                    published_at = str(author_obj.get("date", "")).strip()
                    if not sha or not message or not html_url:
                        continue
                    out.append(
                        {
                            "id": f"N{len(out) + 1}",
                            "title": f"{repo}: {message}",
                            "url": html_url,
                            "source": "GitHub",
                            "published_at": published_at,
                        }
                    )
    except Exception:
        return []
    return out


def _select_repo_pool(
    newspaper_slug: str,
    newspaper_name: str | None,
    editor_persona: str | None,
    section_names: Iterable[str] | None,
    news_config: dict | None,
) -> List[str]:
    if isinstance(news_config, dict):
        repos = news_config.get("github_repos")
        if isinstance(repos, list):
            normalized = [str(item).strip() for item in repos if str(item).strip()]
            if normalized:
                return normalized
    joined = " ".join(_collect_terms(newspaper_slug, newspaper_name, editor_persona, section_names)).lower()
    if any(token in joined for token in ("ai", "模型", "芯片", "技术", "数据", "开源", "model", "chip")):
        return ["openai/openai-python", "huggingface/transformers", "pytorch/pytorch"]
    if any(token in joined for token in ("音乐", "文化", "诗", "城市", "艺术", "music", "art", "culture")):
        return ["vercel/next.js", "vitejs/vite", "withastro/astro"]
    if any(token in joined for token in ("热搜", "辟谣", "群聊", "反转", "争议", "viral", "social", "controversy")):
        return ["sindresorhus/awesome", "github/roadmap", "microsoft/vscode"]
    return ["openai/openai-python", "github/roadmap", "vercel/next.js"]
