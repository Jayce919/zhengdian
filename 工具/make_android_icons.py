# -*- coding: utf-8 -*-
"""把应用图标写入 Capacitor 的 Android res 目录（含自适应图标前景）。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RES = Path(__file__).resolve().parents[2] / "打包" / "apk" / "android" / "app" / "src" / "main" / "res"
SERIF = "C:/Windows/Fonts/STSONG.TTF"
GOLD = (232, 194, 106)
CREAM = (255, 252, 246)
RED = (200, 16, 46)

DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
LAUNCHER_DP = 48
FOREGROUND_DP = 108


def glyph_layer(size: int) -> Image.Image:
    """透明底，画金色细边 + 奶白「政」+ 金点，内容位于中央 78%。"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = size * 0.11
    d.rounded_rectangle(
        [box, box, size - box, size - box],
        radius=int(size * 0.16),
        outline=GOLD + (200,),
        width=max(2, int(size * 0.008)),
    )
    fs = int(size * 0.5)
    font = ImageFont.truetype(SERIF, fs)
    bbox = d.textbbox((0, 0), "政", font=font)
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - gw) / 2 - bbox[0], (size - gh) / 2 - bbox[1] - size * 0.015),
           "政", font=font, fill=CREAM)
    r = size * 0.026
    cx, cy = size * 0.735, size * 0.715
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
    return img


def launcher(size: int) -> Image.Image:
    """带红底的方形图标。"""
    base = Image.new("RGBA", (size, size), RED + (255,))
    base.alpha_composite(glyph_layer(size))
    return base


def round_icon(size: int) -> Image.Image:
    img = launcher(size)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    img.putalpha(mask)
    return img


def main() -> None:
    for name, mult in DENSITIES.items():
        folder = RES / f"mipmap-{name}"
        folder.mkdir(parents=True, exist_ok=True)
        lz = round(LAUNCHER_DP * mult)
        fz = round(FOREGROUND_DP * mult)
        launcher(lz).save(folder / "ic_launcher.png")
        round_icon(lz).save(folder / "ic_launcher_round.png")
        # 前景放大到 108dp 画布，内容按 0.62 缩放，落在自适应图标安全区
        fg = Image.new("RGBA", (fz, fz), (0, 0, 0, 0))
        inner = glyph_layer(int(fz * 0.62))
        off = (fz - inner.width) // 2
        fg.alpha_composite(inner, (off, off))
        fg.save(folder / "ic_launcher_foreground.png")
        print(f"  mipmap-{name}: {lz}px / fg {fz}px")

    colors = RES / "values" / "ic_launcher_background.xml"
    colors.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <color name="ic_launcher_background">#C8102E</color>\n</resources>\n',
        "utf-8",
    )
    print("背景色改为 #C8102E")


if __name__ == "__main__":
    main()
