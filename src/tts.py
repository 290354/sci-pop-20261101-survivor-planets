#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L1 edge-tts 配音流水线：三音色试听 -> 选定 -> 分段合成 -> 按分镜时间码拼接 -> 生成 SRT"""
import asyncio, os, subprocess, json, math, sys
import edge_tts

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUD = os.path.join(BASE, "audio")
os.makedirs(AUD, exist_ok=True)

# (剧本起始秒, 结束秒, 解说词)
SEGS = [
 (0.0, 14.0, "有一颗行星，三十天绕它的太阳转一圈。它的轨道半径，只有地球到太阳距离的百分之十八。听着挺普通。但这颗行星，按理说，早就不该存在了。"),
 (14.0, 25.0, "因为它的太阳，曾经膨胀到今天的一百多倍。那个范围，把这条轨道，整条，包了进去。"),
 (25.0, 45.0, "恒星把核心的氢烧完，外壳就会疯狂膨胀，变成红巨星，半径能涨上百倍。这时候靠得近的行星，只有两种死法：要么被膨胀的外壳直接吞掉，要么在越来越强的引力潮汐里，一圈一圈往里掉，最后栽进火里。等核心点着氦，外壳缩回去，它就变成一颗红团簇巨星。"),
 (45.0, 70.0, "所以天文学界一直有个默认：红团簇巨星身边，不该再有近距离行星，那是理论禁区。可云南大学钱声帮团队一查，二十四牧夫、HD 12648、TYC 4282，三颗星的身边各有一颗行星，三条轨道，全部落在当年的吞噬范围里面。"),
 (70.0, 100.0, "难点在哪呢？红巨星和红团簇巨星，表面温度、亮度都差不多，光靠拍照根本分不出来。团队换了个办法：听。他们用 TESS 卫星的数据，去抠恒星亮度里极其微弱的周期性起伏，靠星震学反推内部状态。就像敲一口钟，听声音能辨出钟的材质和厚度。结果很清楚：三颗都进了核心氦燃烧阶段，那场大膨胀，它们真的经历过。"),
 (100.0, 140.0, "行星存在的证据，是它拽恒星的那点力气。恒星被拉着周期性靠近、远离我们，光谱线就跟着一红一蓝地挪动。把这些观测散点按周期叠起来，一条光滑的正弦曲线浮出来——那就是行星的签名。团队把三个系统过去的光谱数据重新核了一遍，轨道清清楚楚。其中三十天绕一圈的那颗，是目前已知离红团簇巨星最近的系外行星。"),
 (140.0, 170.0, "换个尺度感受一下。地球到太阳，是一个天文单位。这颗行星，只有零点一八。而它的太阳在最胖的时候，半径是现在的上百倍。把这两个数字放在一起，意思就是：它今天待的这个位置，当年是恒星的身体内部。"),
 (170.0, 210.0, "只找到一颗的话，话还好说：也许是模型算错了膨胀范围，也许是这颗行星运气特别好。但这次是三颗，而且分属三颗不同的恒星。钱声帮说，过去发现单个幸存者还能用偶然解释，这回一次三个，说明不是个例，背后很可能存在某种共同的物理机制。一次偶然是故事，三次就是问题。论文的标题，直接叫“幸存悖论”。"),
 (210.0, 240.0, "那它们到底怎么活下来的？老实说，还是推测。一种可能是：恒星吞掉内侧行星的时候，激起了自己的包层物质，往外甩出一圈再生行星盘，外围的行星在盘里互相摩擦，轨道一点点收进来。另一种可能是双星相互作用、甚至合并这类事件，把行星重新安置了一遍。两条路，都还需要更多观测和模拟去验。"),
 (240.0, 270.0, "先把话说死。第一，论文说的存活，只是行星作为一个独立天体还在，不代表它表面有生命。第二，也不能顺手推出地球会幸存。第三，更现实的提醒是：太阳变成红巨星之前，还有几十亿年的持续增亮，地球的宜居条件，很可能在那之前就先没了。"),
 (270.0, 300.0, "回到开头那个问题。大约五十亿年后，太阳也会走这一遭。经典的推演说，水星、金星会被吞掉，地球悬在极度危险的边缘。而这三颗幸存者提醒我们：恒星到底会吞掉多少，行星有没有办法逃过一劫，双星作用、轨道迁移这些过去被当作边缘情况的变量，可能比我们以为的重要得多。宇宙从来不按教科书出牌。每一次我们觉得“这里不该有东西”，往往就是新规律要露头的时候。"),
 (300.0, 310.0, "这一期就到这儿。下一期聊个更烫手的：一个支撑了三十年的地基假设，被 AI 宣布推翻，可验证渠道握在公司手里，学界不认——那算不算发现？"),
]

VOICES = ["zh-CN-YunxiNeural", "zh-CN-YunyangNeural", "zh-CN-XiaoxiaoNeural"]
PICK = "zh-CN-YunxiNeural"   # 科普男声，语调起伏自然、句尾不塌


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", p], capture_output=True, text=True)
    try:
        return float(r.stdout.strip().split(",")[0])
    except Exception:
        return 0.0


async def synth(text, voice, out, rate="+0%", pitch="+0Hz"):
    c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await c.save(out)


def esc(t):
    return t.replace("&", "&amp;")


async def main():
    # ---- 1. 三音色 15 秒试听样本 ----
    probe = SEGS[0][2][:52]
    print("== 试听样本 ==")
    for v in VOICES:
        p = os.path.join(AUD, "audition_%s.mp3" % v)
        try:
            await synth(probe, v, p)
            print("  %-24s %.2fs  %d bytes" % (v, dur(p), os.path.getsize(p)))
        except Exception as e:
            print("  %-24s FAIL %s" % (v, e))
    print("  -> 选定:", PICK)

    # ---- 2. 语速标定：用第 5 段（150字）测字/秒 ----
    rate = "-4%"
    tp = os.path.join(AUD, "_probe_rate.mp3")
    await synth(SEGS[4][2], PICK, tp, rate=rate)
    cps = len(SEGS[4][2]) / max(dur(tp), 0.01)
    total_chars = sum(len(s[2]) for s in SEGS)
    est = total_chars / cps
    print("== 语速标定 ==  %.2f 字/秒  估算总时长 %.1fs (目标<=312s)" % (cps, est))
    if est > 308:
        rate = "+%d%%" % min(30, int(math.ceil((est / 300.0 - 1) * 100)))
        print("   语速过慢，提升到", rate)
    elif est < 250:
        rate = "-10%"
        print("   语速偏快，降到", rate)

    # ---- 3. 分段合成（插入停顿） ----
    print("== 分段合成 ==", flush=True)
    seg_files, seg_durs = [], []
    for i, (s, e, txt) in enumerate(SEGS):
        out = os.path.join(AUD, "seg_%02d.mp3" % i)
        ssml = txt.replace("——那就是行星的签名。", "——那就是行星的签名。<break time=\"400ms\"/>") \
                  .replace("一次偶然是故事，", "一次偶然是故事，<break time=\"300ms\"/>")
        await synth(ssml, PICK, out, rate=rate, pitch="+0Hz")
        d = dur(out)
        seg_files.append(out); seg_durs.append(d)
        print("  seg%02d  %.2fs  %d字" % (i, d, len(txt)), flush=True)

    # ---- 4. 按分镜时间码拼接 ----
    GAP = 0.55
    cur = 0.0
    timeline = []
    for i, (s, e, txt) in enumerate(SEGS):
        place = max(cur, float(s))
        timeline.append((place, seg_durs[i], txt))
        cur = place + seg_durs[i] + GAP
    VOICE_T = cur + 2.2
    DUR = VOICE_T

    sr = 48000
    inputs = []
    filters = []
    for i, (place, d, txt) in enumerate(timeline):
        inputs += ["-i", seg_files[i]]
        filters.append("[%d:a]aresample=%d,adelay=%d|%d[a%d]" % (i, sr, int(place * 1000), int(place * 1000), i))
    n = len(inputs) // 2
    filters.append("%sconcat=n=%d:v=0:a=1,apad,atrim=0:%s[out]" % ("".join("[a%d]" % i for i in range(n)), n, ("%.3f" % DUR)))
    cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(filters),
           "-map", "[out]", "-ar", str(sr), "-ac", "2", os.path.join(AUD, "voice.wav")]
    subprocess.run(cmd, check=True)
    print("== 语音轨 == %.2fs" % dur(os.path.join(AUD, "voice.wav")))

    # ---- 5. SRT ----
    def ts(x):
        h = int(x // 3600); m = int((x % 3600) // 60); s = x % 60
        return "%02d:%02d:%02d,%03d" % (h, m, int(s), int(round((s - int(s)) * 1000)))
    # 按句切分做字幕行
    import re
    lines = []
    idx = 1
    for place, d, txt in timeline:
        parts = [p for p in re.split(r"(?<=[。！？])", txt) if p.strip()]
        weights = [len(p) for p in parts]
        tot = sum(weights) or 1
        acc = place
        for p, w in zip(parts, weights):
            seg_d = d * w / tot
            lines.append((idx, acc, acc + seg_d, p.strip()))
            acc += seg_d
            idx += 1
    with open(os.path.join(BASE, "video", "episode.srt"), "w", encoding="utf-8") as f:
        for i, a, b, t in lines:
            f.write("%d\n%s --> %s\n%s\n\n" % (i, ts(a), ts(b), t))

    meta = {"duration": DUR, "script_T": 310.0, "voice": PICK, "rate": rate,
            "timeline": [[round(a, 3), round(b, 3)] for a, b, _ in timeline]}
    json.dump(meta, open(os.path.join(AUD, "meta.json"), "w"), ensure_ascii=False, indent=2)
    print("== DONE == DUR=%.2fs  rate=%s  voice=%s" % (DUR, rate, PICK))


if __name__ == "__main__":
    asyncio.run(main())
