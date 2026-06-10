import os, json, subprocess, sys, requests
from groq import Groq

# ====== الإعدادات من Environment ======
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://www.youtube.com/@samir-lail.mestapha-lherda")
FB_PAGE_ID = os.environ["FB_PAGE_ID"]
FB_ACCESS_TOKEN = os.environ["FB_ACCESS_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
BG_PATH = os.path.join(os.path.dirname(__file__), "assets", "bg.jpg")

# تحميل الخلفية
bg_dir = os.path.dirname(BG_PATH)
os.makedirs(bg_dir, exist_ok=True)
if not os.path.exists(BG_PATH):
    subprocess.run(["wget", "-q", "-O", BG_PATH,
        "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=1280&h=720&fit=crop"], check=True)

client = Groq(api_key=GROQ_API_KEY)

# ====== State ======
STATE_FILE = "state.json"
state = {"downloaded": []}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ====== تحميل من يوتوب ======
def get_latest():
    cmd = ["yt-dlp", "--flat-playlist", "--dump-json",
           "--playlist-end", "5", CHANNEL_URL]
    r = subprocess.run(cmd, capture_output=True, text=True)
    for line in r.stdout.strip().split("\n"):
        if not line: continue
        try:
            data = json.loads(line)
            return {"id": data["id"], "title": data["title"], "url": data["webpage_url"]}
        except: continue
    return None

def download_video(url, path="input.mp4"):
    cookies = os.environ.get("YT_COOKIES")
    cookies_args = ["--cookies", "yt_cookies.txt"] if cookies else []

    # First, dump video info for debugging
    info = subprocess.run(["yt-dlp", "--dump-json", "--flat-playlist",
                           url], capture_output=True, text=True, timeout=30)
    if info.returncode == 0 and info.stdout.strip():
        import json as j
        try: print("  video:", j.dumps(j.loads(info.stdout), indent=2)[:600])
        except: pass

    base = ["-o", path, "--no-progress", "--retries", "5",
            "--verbose", "--force-ipv4",
            "--sleep-requests", "1", "--sleep-interval", "3",
            "--geo-bypass"]

    strategies = [
        ["--extractor-args", "youtube:player_client=ios", "-f", "bestaudio[ext=m4a]"],
        ["--extractor-args", "youtube:player_client=ios", "-f", "best"],
        ["--extractor-args", "youtube:player_client=android_creator", "-f", "best"],
        ["--user-agent", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
         "-f", "bestaudio[ext=m4a]"],
        ["--extractor-args", "youtube:player_client=android", "-f", "18"],
        ["--extractor-args", "youtube:player_client=android", "-f", "22"],
        ["--extractor-args", "youtube:player_client=web", "--js-runtimes", "deno", "-f", "best"],
        ["--js-runtimes", "node", "-f", "best"],
        ["--extractor-args", "youtube:skip=dash,webpage,hls", "-f", "best"],
        ["-f", "best"],
    ]

    for strat in strategies:
        cmd = ["yt-dlp"] + base + cookies_args + strat + [url]
        print(f"yt-dlp trying: {' '.join(strat)}")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and os.path.exists(path) and os.path.getsize(path) > 10000:
            print(f"yt-dlp success with: {' '.join(strat)}")
            return path
        # Print first and last parts of stderr
        head = r.stderr[:300]
        tail = r.stderr[-500:]
        print(f"  rc={r.returncode}: {head}")
        print(f"  ...{tail}")

    raise RuntimeError("All yt-dlp strategies failed")

print("🔍 جلب أحدث فيديو...")
video = get_latest()
if not video:
    print("❌ ما لقيناش فيديو")
    sys.exit(1)

if video["id"] in state["downloaded"]:
    print(f"⏭️ {video['title'][:40]} - محمل من قبل")
    sys.exit(0)

print(f"📥 تحميل: {video['title'][:50]}")
download_video(video["url"])
original_title = video["title"]

# ====== Groq ======
print("🤖 Groq كاتولد الوصف...")
chat = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system",
         "content": "أنت منتج بودكاست محترف. أعد كتابة عنوان ووصف الفيديو بصياغة جديدة جذابة مع الحفاظ على نفس الفكرة والمحتوى."
        },
        {"role": "user",
         "content": f"العنوان الأصلي: {original_title}\n\nأعد كتابة:\n1. عنوان جديد للبودكاست يبدأ بـ '🎙️ podcaste abdo |'\n2. وصف جديد (نفس القصة/الفكرة، صياغة مختلفة احترافية)\n3. هاشتاغات: #podcast #shorts #podcasteabdo"
        }
    ]
)
raw = chat.choices[0].message.content
print(raw)

generated_title = f"🎙️ podcaste abdo | {original_title}"
generated_desc = f"{original_title}\n—\n#podcast #shorts #podcasteabdo"
for line in raw.strip().split("\n"):
    line = line.strip().strip('"').strip("'")
    if any(m in line for m in ["🎙️", "podcaste", "podcast ", "بودكاست"]):
        if "|" in line or "🎙️" in line:
            generated_title = line.rstrip(",")
    elif line.startswith("#"):
        if line not in generated_desc:
            generated_desc += f"\n{line}"

import re
def sanitize_ffmpeg(text):
    return re.sub(r"['\"\\]", "", text)[:60]

safe_title = sanitize_ffmpeg(generated_title)
print(f"📝 {safe_title}")

# ====== Podcast Montage ======
MUSIC_PATH = os.path.join(os.path.dirname(__file__), "assets", "bg_music.mp3")
print("🎬 Podcast Montage...")

filt = (
    # Audio: split → [a_fx] (voice FX) + [a_waves] (visualizer)
    f"[0:a]asplit=2[a_fx][a_waves];"
    # Voice FX: silence removal → pitch up 3% → speed 5% → EQ → echo
    f"[a_fx]silenceremove=1:0:-50dB,"
    f"asetrate=44100*1.03,atempo=1/1.03,"   # pitch +3% only
    f"atempo=1.05,"                          # speed +5% + pitch +5%
    f"equalizer=f=100:t=q:w=1:g=5,"         # Bass boost
    f"equalizer=f=8000:t=q:w=1:g=-3,"       # Treble cut
    f"aecho=0.8:0.7:60:0.4[voice];"         # Studio reverb
    # Mix voice + background music (10% volume)
    f"[voice][1:a]amix=inputs=2:duration=first:weights=1 0.1[a_out];"
    # Visualizer
    f"[a_waves]showwaves=s=1280x540:mode=cline:rate=25:colors=#FFD700|white[waves];"
    # Background image
    f"[2:v]scale=1280:720[bg];"
    # Overlay waves on background
    f"[bg][waves]overlay=format=auto:0:((H-h)/2)[v];"
    # Text: podcaste abdo
    f"[v]drawtext=text='podcaste abdo':fontsize=32:fontcolor=white:"
    f"x=(w-text_w)/2:y=H-100:shadowy=2:shadowcolor=black@0.5,"
    # Text: episode title
    f"drawtext=text='{safe_title}':fontsize=18:fontcolor=#CCCCCC:"
    f"x=(w-text_w)/2:y=H-60:shadowy=1:shadowcolor=black@0.3"
)

cmd = ["ffmpeg","-y",
       "-i","input.mp4",           # 0: video + voice
       "-i", MUSIC_PATH,           # 1: background music
       "-i", BG_PATH,              # 2: background image
       "-filter_complex",filt,
       "-map","[v]","-map","[a_out]",
       "-c:v","libx264","-preset","fast","-crf","23",
       "-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","192k",
       "-movflags","+faststart",
       "-shortest","podcast_episode.mp4"]

r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stderr[-800:])
    sys.exit(1)
size_mb = os.path.getsize("podcast_episode.mp4")/(1024*1024)
print(f"✅ podcast_episode.mp4 ({size_mb:.1f} MB)")

# ====== رفع لـ Facebook ======
print("📤 رفع لـ Facebook...")
r = requests.post(
    f"https://graph.facebook.com/v22.0/{FB_PAGE_ID}/videos",
    files={"source": open("podcast_episode.mp4","rb")},
    data={
        "title": generated_title[:100],
        "description": generated_desc[:1000],
        "access_token": FB_ACCESS_TOKEN
    }
)
res = r.json()
if "id" in res:
    print(f"✅ تم الرفع! https://facebook.com/{res['id']}")
    state["downloaded"].append(video["id"])
    save_state()
else:
    print("❌ فشل الرفع:", json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(1)

print("🎉 البوت خلص!")