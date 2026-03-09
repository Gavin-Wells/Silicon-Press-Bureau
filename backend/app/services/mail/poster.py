from __future__ import annotations

import re
import importlib
from io import BytesIO
from pathlib import Path
from typing import Any

def _load_font(image_font: Any, size: int, *, bold: bool = False, serif: bool = False) -> Any:
    if serif:
        candidates = [
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    else:
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for font_path in candidates:
        if not Path(font_path).exists():
            continue
        try:
            return image_font.truetype(font_path, size=size)
        except Exception:
            continue
    return image_font.load_default()


def _normalize_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    return normalized


def _wrap_text(
    draw: Any,
    text: str,
    font: Any,
    max_width: int,
    max_lines: int,
) -> list[str]:
    if not text:
        return []

    lines: list[str] = []
    current = ""
    for char in text:
        candidate = f"{current}{char}"
        candidate_width = draw.textbbox((0, 0), candidate, font=font)[2]
        if candidate_width <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = char
        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines and current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if lines and len("".join(lines)) < len(text):
        clipped = lines[-1]
        while clipped and draw.textbbox((0, 0), f"{clipped}…", font=font)[2] > max_width:
            clipped = clipped[:-1]
        lines[-1] = f"{clipped}…" if clipped else "…"

    return lines


def build_acceptance_poster_png(
    *,
    newspaper_name: str,
    title: str,
    content: str,
    homepage_url: str,
) -> bytes:
    try:
        qrcode = importlib.import_module("qrcode")
        pil_image = importlib.import_module("PIL.Image")
        pil_draw = importlib.import_module("PIL.ImageDraw")
        pil_font = importlib.import_module("PIL.ImageFont")
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少海报依赖，请安装 Pillow 与 qrcode") from exc

    width, height = 1240, 1754
    poster = pil_image.new("RGB", (width, height), "#f7f4ee")
    draw = pil_draw.Draw(poster)

    border_color = "#6f56b2"
    text_color = "#2f2a33"
    muted_color = "#7f748d"

    margin = 72
    draw.rectangle(
        (margin, margin, width - margin, height - margin),
        outline=border_color,
        width=5,
    )

    title_font = _load_font(pil_font, 72, bold=True, serif=True)
    section_font = _load_font(pil_font, 40, bold=True, serif=True)
    body_font = _load_font(pil_font, 38, serif=True)
    meta_font = _load_font(pil_font, 30, serif=True)
    badge_font = _load_font(pil_font, 24, bold=True)

    x = margin + 44
    y = margin + 44

    draw.text((x, y), "中稿了", font=title_font, fill=border_color)
    y += 94

    draw.text((x, y), f"《{newspaper_name}》录用通知", font=meta_font, fill=muted_color)
    y += 80

    draw.line((x, y, width - margin - 44, y), fill=border_color, width=3)
    y += 34

    draw.text((x, y), _normalize_text(title), font=section_font, fill=text_color)
    y += 72

    normalized_content = _normalize_text(content)
    content_lines = _wrap_text(
        draw,
        normalized_content,
        body_font,
        max_width=width - (margin + 44) * 2,
        max_lines=20,
    )

    line_height = 52
    for line in content_lines:
        draw.text((x, y), line, font=body_font, fill=text_color)
        y += line_height

    footer_y = height - margin - 250
    draw.line((x, footer_y - 36, width - margin - 44, footer_y - 36), fill="#d3c9e4", width=2)
    draw.text((x, footer_y), f"报纸：{newspaper_name}", font=meta_font, fill=text_color)
    draw.text((x, footer_y + 46), "Scan to open homepage", font=badge_font, fill=muted_color)

    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data(homepage_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#2f2a33", back_color="white").convert("RGB")
    qr_img = qr_img.resize((180, 180))
    qr_x = width - margin - 44 - 180
    qr_y = height - margin - 44 - 180
    poster.paste(qr_img, (qr_x, qr_y))

    output = BytesIO()
    poster.save(output, format="PNG", optimize=True)
    return output.getvalue()
