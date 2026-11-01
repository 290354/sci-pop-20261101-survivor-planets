# 科普爆点动画周刊 · 第 1 期：三颗本不该存在的行星

> **The Survival Paradox of Close-In Planets Orbiting Red Clump Giants**
> 恒星膨胀成红巨星，会吞掉身边靠得太近的行星——这是教科书里的常识。
> 可云南大学钱声帮团队发现：有三颗行星，本该被吞掉，今天还在原地转圈。

- **成片**：[`video/episode.mp4`](video/episode.mp4)（1280×720 / 30fps / 约 5 分 20 秒 / 含解说音轨与配乐）
- **字幕**：[`video/episode.srt`](video/episode.srt)（随片交付，画面内也已绘制大字幕）
- **封面**：`cover.png`（1280×720）
- **脚本**：[`script.md`](script.md) · **选题**：[`选题.md`](选题.md)
- **渲染源码**：`src/index.html`（Canvas 动画主体）+ `src/render.py`（Playwright 逐帧截图）+ `src/tts.py`（配音流水线）

## 本期成片规格

| 项 | 值 |
|---|---|
| 分辨率 | 1280×720（横屏 16:9） |
| 帧率 | 30 fps |
| 时长 | 约 320 秒（5:20，落在 4:30–5:30 区间） |
| 音轨 | 立体声 AAC：中文解说（edge-tts `zh-CN-YunxiNeural`，语速 −4%）+ 合成氛围配乐（−26 dB，压在 −20 dB 以下） |
| 总帧数 | 9618 帧（`frames/`，渲染中间产物，未入库） |

## 制作路线：B —— HTML + Canvas 逐帧渲染

**为什么不是 A（Manim）**：本期题材是天文 / 尺度对比 / 时间演化类，核心画面是恒星半径的连续膨胀收缩、轨道演化、光变曲线描线、散点相位折叠——这些用 Canvas 的连续量绘制（每帧一个 `renderAt(t)`）比 Manim 的对象动画更省渲染成本；同时全片中文排版密集，Canvas + Noto Sans CJK 可控且无 LaTeX / TeX Live 依赖，符合"宁可降配置，不可交半成品"。

**实现要点**

- 页面 `src/index.html` 暴露 `window.renderAt(t)`（t 为秒，浮点），`?export=1` 时不启动 `requestAnimationFrame` 实时循环，只由外部驱动。
- `src/render.py` 用 Playwright + Chromium headless 逐帧截图（6 进程并行分片），输出 `frames/f%06d.jpg`。
- 音画对齐：剧本时间轴固定 `SCRIPT_T = 310`，成片时长 `DUR` 取解说音频实际总长，动画内部做线性映射 `ts = t × (SCRIPT_T / DUR)`，任何语速下画面与解说都自动对齐。
- 字幕按 SRT 真实时间轴在画面内绘制（`window.SUBS` 注入），并单独输出 `.srt` 文件。
- 视觉规范：背景 `#0E1116`、正文 `#ECE6D9`，主色仅三色 `#58C4DD` / `#F4D345` / `#FC6255`；中文字体 Noto Sans CJK SC，所有文本绘制均做 `measureText` 超宽自动缩字号，杜绝出画；每 8–15 秒必有视觉变化，无整屏文字一次性淡入。

**风格参考**：整体为"深空深底 + 明亮强调色"的科普讲解风格，取 `code-animation-prompts` 中 M1（白板手绘式"先看见、再命名"）与 B3（粒子聚形）两层提示词的思路；分镜节奏与镜头运动参考 `fy-code-animation` 的 modules/recipes 组织方式（只取规范，不套整包依赖）。

## 配音档位：L1（edge-tts）

- 三个音色各合成约 12 秒试听样本（`audio/audition_*.mp3`）：`zh-CN-YunxiNeural` 11.81s / `zh-CN-YunyangNeural` 11.57s / `zh-CN-XiaoxiaoNeural` 12.00s。
- 选定 **`zh-CN-YunxiNeural`**（男声，句尾不塌、数字与术语清晰，适合科普播报）。
- 正式合成：12 段分镜逐段生成，插入 `<break time="300~400ms"/>` 控制停顿，语速 `−4%`；每段用 `ffprobe` 取时长后按分镜时间码拼接（`ffmpeg adelay + concat`）。
- 配乐：ffmpeg `aevalsrc` 生成的低频 drone + 五度泛音氛围垫，−26 dB 混入，不与解说抢频段；结论处留白由段间 0.55s 间隔自然形成。

## 选题来源（全部为真实可访问链接）

| 来源 | 链接 |
|---|---|
| 云南大学 · 论文发布 | https://www.ynu.edu.cn/info/1429/39745.htm |
| 新华社 / 中国网 | https://big5.china.com.cn/gate/big5/news.china.com.cn/2026-10/26/content_118749989.shtml |
| 光明网（今日头条转载） | https://www.toutiao.com/article/7701175638577414696/ |
| 海峡都市报 | https://dzb.hxnews.com/news/kjzx/202610/27/2275901.shtml |
| 24 Boo 词条 | https://baike.baidu.com/item/24Boo/69509154 |

事实核对：三颗宿主星 24 Boo / HD 12648 / TYC 4282-605-1 均经 TESS 星震学确认处于核心氦燃烧（红团簇）阶段；24 Boo b 约 30 天公转一周，轨道半径约为日地距离的 18%，为已知距红团簇巨星最近的系外行星。两条逃生路径（再生行星盘 / 双星相互作用或合并）在正片中已明确标注为**推测**。

## 如何复现

```bash
# 0. 依赖
pip3 install edge-tts playwright && playwright install chromium
apt-get install -y fonts-noto-cjk ffmpeg

# 1. 配音（三音色试听 + 分段合成 + 拼接 + SRT）
python3.11 src/tts.py

# 2. 逐帧渲染（参数：总帧数 进程数）
python3.11 src/render.py 9618 6

# 3. 配乐 + 合成成片
bash src/build.sh
```

## 目录结构

```
.
├── README.md          本文件
├── 选题.md            选题会记录（候选表 + 三项打分 + 选定理由）
├── script.md          5 分钟分镜脚本（时间码 | 画面 | 屏幕文字 | 解说 | 转场）
├── cover.png          封面 1280×720
├── src/
│   ├── index.html     Canvas 动画主体（暴露 window.renderAt(t)）
│   ├── render.py      Playwright 逐帧截图渲染器（多进程）
│   ├── tts.py         edge-tts 配音流水线
│   └── build.sh       配乐 + 字幕 + 合成成片
├── audio/             试听样本、分段 mp3、voice.wav、meta.json
└── video/
    ├── episode.mp4    成片
    └── episode.srt    字幕
```

## 已知瑕疵

1. 成片 5:20，略长于脚本设计的 4:50–5:10（解说按 4.63 字/秒实测语速铺排，未强行提速，仍在 4:30–5:30 硬指标内）。
2. 配乐为程序化合成的氛围垫，情绪起伏较平缓，未做逐章节动态配器。
3. 分辨率取 1280×720（满足 ≥1280×720 下限），非 1080p，为保证 28 分钟内出片而作的取舍。
4. 逐帧中间产物 `frames/` 约数千个 JPEG，未纳入仓库（体积原因），可用 `src/render.py` 重新生成。
