"""
AI Agent 集合

每个 Agent 职责单一：
  - ReviewerAgent: 审稿（多维度评分）
  - EditorAgent: 编辑润色
  - RejectorAgent: 生成退稿信

Agent 不做数据库操作 — 纯粹的 LLM 调用封装。
"""

import json
from typing import List, Dict
from app.agents.llm_manager import LLMManager


class ReviewerAgent:
    """审稿 Agent — 多维度评分"""

    def __init__(self, newspaper_slug: str, model_key: str = "gemini-3.1-flash-lite", review_prompt: str | None = None):
        self.llm = LLMManager()
        self.newspaper_slug = newspaper_slug
        self.model_key = model_key
        self.review_prompt = (review_prompt or "").strip()

    def review(
        self,
        title: str,
        content: str,
        section_name: str = "",
        scoring_dimensions: List[Dict] = None,
    ) -> dict:
        """对投稿进行多维度评分

        Args:
            title: 投稿标题
            content: 投稿内容
            section_name: 板块名称
            scoring_dimensions: 评分维度列表 [{name, weight, description}]

        Returns:
            {total_score, dimension_scores, feedback, raw_response}
        """
        # 构建评分维度描述
        dims_text = ""
        if scoring_dimensions:
            dims_text = "\n评分维度：\n"
            for d in scoring_dimensions:
                dims_text += f"  - {d['name']}（权重 {d['weight']:.0%}）：{d['description']}\n"
            dims_text += "\n请对每个维度分别打分（0-100），然后按权重计算总分。"
            dims_text += "\n输出格式（严格 JSON）："
            dims_text += '\n```json\n{"scores": {"维度名": 分数, ...}, "total": 总分, "feedback": "评语"}\n```'
        else:
            dims_text = "\n请打一个总分（0-100）并给出评语。\n输出格式：分数|评语"

        if not self.review_prompt:
            raise ValueError(f"ReviewerAgent 缺少报刊 '{self.newspaper_slug}' 的 review_prompt")

        prompt = self.review_prompt.format(title=title, content=content) + f"\n\n板块：{section_name}" + dims_text

        # 调用 LLM
        response = self.llm.call(self.model_key, "", prompt, temperature=0.3)

        # 解析响应
        return self._parse_response(response, scoring_dimensions)

    def _parse_response(self, response: str, scoring_dimensions: List[Dict] = None) -> dict:
        """解析 LLM 响应为结构化评分"""

        # 尝试解析 JSON 格式响应
        try:
            # 提取 JSON 块
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            dimension_scores = data.get("scores", {})
            total_score = data.get("total", 50)
            feedback = data.get("feedback", "")

            # 验证总分是否与维度分数加权一致
            if scoring_dimensions and dimension_scores:
                calculated = sum(
                    dimension_scores.get(d["name"], 50) * d["weight"]
                    for d in scoring_dimensions
                )
                total_score = round(calculated)

            return {
                "total_score": max(0, min(100, total_score)),
                "dimension_scores": dimension_scores,
                "feedback": feedback,
                "raw_response": response,
            }
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        # Fallback: 解析旧格式 "分数|评语"
        try:
            parts = response.split("|", 1)
            score = int(parts[0].strip())
            feedback = parts[1].strip() if len(parts) > 1 else response
            return {
                "total_score": max(0, min(100, score)),
                "dimension_scores": {},
                "feedback": feedback,
                "raw_response": response,
            }
        except (ValueError, IndexError):
            return {
                "total_score": 50,
                "dimension_scores": {},
                "feedback": response,
                "raw_response": response,
            }


class EditorAgent:
    """编辑 Agent — 润色文章"""

    def __init__(self, newspaper_slug: str, edit_prompt: str | None = None):
        self.llm = LLMManager()
        self.newspaper_slug = newspaper_slug
        self.edit_prompt = (edit_prompt or "").strip()

    def edit(self, title: str, content: str) -> dict:
        """编辑润色

        Returns:
            {edited_title, edited_content, editor_note}
        """
        if not self.edit_prompt:
            raise ValueError(f"EditorAgent 缺少报刊 '{self.newspaper_slug}' 的 edit_prompt")
        prompt = self.edit_prompt.format(title=title, content=content)
        response = self.llm.call("gpt-5.4", "", prompt, temperature=0.7)

        parts = response.split("---", 1)
        if len(parts) == 2:
            title_block = parts[0].strip()
            content_block = parts[1].strip()
            # 去掉模型可能输出的格式标签行，避免「新标题」「新内容」进入正文
            def drop_label_block(text: str, label: str) -> str:
                first_line = (text.split("\n")[0] or "").strip()
                if first_line == label or first_line.startswith(label + "：") or first_line.startswith(label + ":"):
                    rest = text.split("\n", 1)[1] if "\n" in text else ""
                    return rest.strip() or text
                return text
            title_block = drop_label_block(title_block, "新标题")
            content_block = drop_label_block(content_block, "新内容")
            return {
                "edited_title": title_block or title,
                "edited_content": content_block or content,
                "editor_note": "",
            }
        return {
            "edited_title": title,
            "edited_content": response.strip(),
            "editor_note": "编辑未修改标题",
        }


class RejectorAgent:
    """退稿信 Agent — 生成个性化退稿信"""

    def __init__(self, newspaper_slug: str, reject_prompt: str | None = None):
        self.llm = LLMManager()
        self.newspaper_slug = newspaper_slug
        self.reject_prompt = (reject_prompt or "").strip()

    def generate_rejection(self, title: str, score: int, feedback: str) -> str:
        """生成退稿信"""
        if not self.reject_prompt:
            raise ValueError(f"RejectorAgent 缺少报刊 '{self.newspaper_slug}' 的 reject_prompt")
        prompt = self.reject_prompt.format(title=title, score=score, feedback=feedback)
        return self.llm.call("gemini-3.1-flash-lite", "", prompt, temperature=0.8)
