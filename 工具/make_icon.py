# -*- coding: utf-8 -*-
r"""生成应用图标：红底金边印章式「政」字，输出 SVG 与多尺寸 PNG。

用法：python 工具\make_icon.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[2] / "政治刷题App"
PUBLIC = BASE / "政治刷题App" / "public"
SERIF = "C:/Windows/Fonts/STSONG.TTF"

RED_TOP = (208, 24, 47)
RED_BOTTOM = (128, 10, 30)
GOLD = (232, 194, 106)
CREAM = (255, 252, 246)


def gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (1, size))
    px = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        px[0, y] = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return img.resize((size, size))


def draw_icon(size: int, padding_ratio: float = 0.0) -> Image.Image:
    """padding_ratio>0 时把内容缩进，用于 maskable 图标。"""
    scale = 4
    S = size * scale
    img = gradient(S, RED_TOP, RED_BOTTOM).convert("RGBA")

    # 圆角遮罩
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.235), fill=255)
    img.putalpha(mask)

    # 左上柔光
    glow = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-S * 0.35, -S * 0.55, S * 0.95, S * 0.55], fill=38)
    glow = glow.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(S * 0.08))
    img = Image.composite(Image.new("RGBA", (S, S), (255, 255, 255, 255)), img, glow.point(lambda v: int(v * 0.55)))

    d = ImageDraw.Draw(img)
    inset = S * (0.055 + padding_ratio)
    # 金色内边框（印章感）
    d.rounded_rectangle(
        [inset, inset, S - inset, S - inset],
        radius=int(S * 0.165),
        outline=GOLD + (170,),
        width=max(2, int(S * 0.006)),
    )

    # 「政」字
    glyph_size = int(S * (0.46 - padding_ratio * 0.6))
    font = ImageFont.truetype(SERIF, glyph_size)
    bbox = d.textbbox((0, 0), "政", font=font, stroke_width=int(S * 0.006))
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    gx = (S - gw) / 2 - bbox[0]
    gy = (S - gh) / 2 - bbox[1] - S * 0.02
    d.text((gx, gy), "政", font=font, fill=CREAM, stroke_width=int(S * 0.006), stroke_fill=CREAM)

    # 右下角金点（「点」的象形）
    dot_r = S * (0.028 - padding_ratio * 0.008)
    cx, cy = S * 0.755, S * (0.725 - padding_ratio * 0.05)
    d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=GOLD)

    return img.resize((size, size), Image.LANCZOS)


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0" stop-color="#d0182f"/>
      <stop offset="1" stop-color="#800a1e"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.22" cy="0.08" r="0.85">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="0.6" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="512" height="512" rx="120" fill="url(#bg)"/>
  <rect width="512" height="512" rx="120" fill="url(#glow)"/>
  <rect x="28" y="28" width="456" height="456" rx="86" fill="none" stroke="#e8c26a" stroke-opacity="0.66" stroke-width="3"/>
  <text x="256" y="300" font-family="Noto Serif SC, Source Han Serif SC, Songti SC, SimSun, serif"
        font-size="236" font-weight="700" text-anchor="middle" fill="#fffcf6">政</text>
  <circle cx="386" cy="371" r="14" fill="#e8c26a"/>
</svg>
"""


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "icon.svg").write_text(SVG, "utf-8")
    for size in (192, 512, 1024):
        draw_icon(size).save(PUBLIC / f"icon-{size}.png")
    # maskable：内容再缩进，避免被裁切
    draw_icon(512, padding_ratio=0.06).save(PUBLIC / "icon-maskable-512.png")
    print("图标已生成：icon.svg / icon-192.png / icon-512.png / icon-1024.png / icon-maskable-512.png")


if __name__ == "__main__":
    main()
