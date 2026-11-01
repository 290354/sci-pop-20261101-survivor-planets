#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Playwright + Chromium 逐帧截图渲染器（多进程并行）
用法: python3.11 src/render.py <总帧数> <进程数>
"""
import os, sys, re, json, time, math
from multiprocessing import Pool

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(BASE, "frames")
os.makedirs(FR, exist_ok=True)
META = json.load(open(os.path.join(BASE, "audio", "meta.json")))
DUR = META["duration"]
FPS = 30
TOTAL = int(sys.argv[1]) if len(sys.argv) > 1 else int(round(DUR * FPS))
NPROC = int(sys.argv[2]) if len(sys.argv) > 2 else 6

# --- 解析 SRT ---
def load_srt(p):
    txt = open(p, encoding="utf-8").read()
    blocks = re.findall(r"(\d+)\s*\n([\d:,]+)\s*-->\s*([\d:,]+)\s*\n(.+?)(?=\n\n|\Z)", txt, re.S)
    out = []
    def sec(s):
        h, m, rest = s.split(":"); s2, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s2) + int(ms) / 1000.0
    for _, a, b, t in blocks:
        out.append([sec(a), sec(b), t.replace("\n", " ").strip()])
    return out

SUBS = load_srt(os.path.join(BASE, "video", "episode.srt"))
URL = "file://" + os.path.join(BASE, "src", "index.html") + "?export=1&dur=%.3f" % DUR


def worker(args):
    wid, start, end = args
    from playwright.sync_api import sync_playwright
    t0 = time.time()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=[
            "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
            "--force-device-scale-factor=1", "--hide-scrollbars", "--mute-audio"])
        pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        pg.goto(URL, wait_until="load")
        pg.evaluate("subs => { window.SUBS = subs; }", SUBS)
        pg.wait_for_function("window.__ready === true", timeout=30000)
        clip = {"x": 0, "y": 0, "width": 1280, "height": 720}
        for i in range(start, end):
            t = i / float(FPS)
            try:
                pg.evaluate("window.renderAt(%r)" % t)
            except Exception as e:
                if i == start:
                    print("EVAL FAIL", e); break
            pg.screenshot(path=os.path.join(FR, "f%06d.jpg" % i), type="jpeg",
                          quality=92, clip=clip, animations="disabled")
            if i == start + 5:
                el = time.time() - t0
                print("  [w%d] 6帧耗时 %.2fs -> 预计 %.0fs" % (wid, el, el / 6 * (end - start)), flush=True)
        b.close()
    return wid, start, end, time.time() - t0


def main():
    print("DUR=%.2fs  TOTAL=%d帧  NPROC=%d  -> frames/%06d.jpg" % (DUR, TOTAL, NPROC, 0))
    chunk = int(math.ceil(TOTAL / float(NPROC)))
    jobs = [(i, i * chunk, min(TOTAL, (i + 1) * chunk)) for i in range(NPROC) if i * chunk < TOTAL]
    t0 = time.time()
    with Pool(len(jobs)) as pool:
        for wid, s, e, el in pool.imap_unordered(worker, jobs):
            print("  worker %d done: [%d,%d) %.1fs" % (wid, s, e, el), flush=True)
    print("RENDER DONE %.1fs" % (time.time() - t0))
    # 连续性检查
    miss = [i for i in range(TOTAL) if not os.path.exists(os.path.join(FR, "f%06d.jpg" % i))]
    print("missing frames:", len(miss), miss[:10])


if __name__ == "__main__":
    main()
