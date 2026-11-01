#!/usr/bin/env bash
# 配乐生成 + 音画合成 + 封面
set -e
cd "$(dirname "$0")/.."
DUR=$(python3.11 -c "import json;print(json.load(open('audio/meta.json'))['duration'])")
echo "DUR=$DUR"

# ---- 1. 配乐：低频 drone + 五度泛音，缓慢 LFO 起伏（L3 就地合成方案） ----
OUT_ST=$(python3.11 -c "print(%.3f-5.0)" "$DUR" 2>/dev/null || echo 315)
ffmpeg -y -v error -f lavfi \
  -i "aevalsrc=0.34*sin(2*PI*55*t)*(0.62+0.38*sin(2*PI*0.050*t)) \
      +0.21*sin(2*PI*82.5*t)*(0.62+0.38*sin(2*PI*0.037*t)) \
      +0.14*sin(2*PI*110*t)*(0.60+0.40*sin(2*PI*0.029*t)) \
      +0.07*sin(2*PI*220*t)*(0.50+0.50*sin(2*PI*0.021*t)) \
      :s=48000:d=$DUR" \
  -af "volume=-26dB,afade=t=in:st=0:d=3,afade=t=out:st=$OUT_ST:d=5,pan=stereo|c0=c0|c1=c0" \
  -ar 48000 -ac 2 audio/bgm.wav
echo "bgm ok"

# ---- 2. 混音：解说为主，配乐垫底 ----
ffmpeg -y -v error -i audio/voice.wav -i audio/bgm.wav \
  -filter_complex "[0:a]aresample=48000[a0];[1:a]aresample=48000[a1];\
[a0][a1]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.92,volume=1.0[a]" \
  -map "[a]" -ar 48000 -ac 2 audio/mix.wav
echo "mix ok"

# ---- 3. 合成成片（30fps，画面内已含字幕） ----
ffmpeg -y -v error -framerate 30 -i frames/f%06d.jpg -i audio/mix.wav \
  -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart -shortest video/episode.mp4
echo "video ok"

# ---- 4. 封面 ----
python3.11 src/cover.py

ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,avg_frame_rate \
  -of default=noprint_wrappers=1 video/episode.mp4
