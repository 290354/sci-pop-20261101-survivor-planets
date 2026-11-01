#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成封面 cover.png (1280x720)：取片中一帧 + 暗化 + 标题 + 期号"""
import os, glob
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(BASE, "frames", "f000180.jpg")
im = Image.open(src).convert("RGB").resize((1280, 720))
# 暗化 + 底部渐变，保证文字对比度
d = Image.new("L", (1280, 720), 0)
dr = ImageDraw.Draw(d)
for y in range(720):
    v = int(150 * min(1.0, max(0.0, (y - 180) / 420.0)))
    dr.line([(0, y), (1280, y)], fill=v)
dark = Image.new("RGB", (1280, 720), (14, 17, 22))
im = Image.composite(im, dark, d)

cands = glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True) + \
        glob.glob("/usr/share/fonts/**/NotoSansCJK*.otf", recursive=True) + \
        glob.glob("/usr/share/fonts/**/NotoSerifCJK*.ttc", recursive=True)
fp = cands[0] if cands else None
def F(sz):
    try:
        return ImageFont.truetype(fp, sz) if fp else ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

dr = ImageDraw.Draw(im)
YEL = (244, 211, 69); FG = (236, 230, 217); BLU = (88, 196, 221); DIM = (150, 160, 172)

dr.rectangle([0, 96, 1280, 104], fill=BLU)
dr.text((80, 150), "科普爆点动画周刊", font=F(36), fill=BLU)
dr.text((80, 214), "第 1 期", font=F(30), fill=DIM)

# 主标题（自动缩放防溢出）
title = "三颗本不该存在的行星"
sz = 96
while sz > 40:
    f = F(sz)
    if dr.textlength(title, font=f) <= 1120:
        break
    sz -= 4
dr.text((80, 288), title, font=F(sz), fill=YEL)

sub = "恒星膨胀 ×100，它们却活了下来"
f2 = F(40)
w = dr.textlength(sub, font=f2)
dr.text((80, 288 + sz + 34), sub, font=f2 if w <= 1120 else F(34), fill=FG)

dr.text((80, 560), "The Survival Paradox  ·  PNAS / 云南大学钱声帮团队", font=F(26), fill=DIM)
dr.text((80, 606), "1280×720 · 30fps · 5 分 20 秒 · 含解说与字幕", font=F(24), fill=DIM)
dr.rectangle([80, 650, 420, 653], fill=YEL)

im.save(os.path.join(BASE, "cover.png"), quality=95)
print("cover.png ok", im.size)
