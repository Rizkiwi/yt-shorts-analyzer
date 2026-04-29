"""
YouTube Shorts Trend Collector & Analyzer — Streamlit App
==========================================================
Setup:
  1. Buat file .env: YOUTUBE_API_KEY=your_api_key_here
  2. pip install google-api-python-client pandas python-dotenv streamlit plotly
  3. streamlit run yt_shorts_app.py
"""

import os, csv, re, time, datetime, io, math, collections
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import plotly.express as px
import plotly.graph_objects as go

load_dotenv()

st.set_page_config(page_title="YT Shorts Analyzer", page_icon="▶", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
  --red:    #FF0000;
  --red-dk: #CC0000;
  --black:  #0F0F0F;
  --border: #E8E8E8;
  --muted:  #606060;
  --white:  #FFFFFF;
  --gray:   #FAFAFA;
}

html, body, [class*="css"], div, p, span, label, button {
  font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
  background: #FFFFFF !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: #FAFAFA !important;
  border-right: 1px solid var(--border) !important;
  padding: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: var(--black) !important; }

.sb-header {
  background: var(--red);
  padding: 0.9rem 1.1rem;
  display: flex; align-items: center; gap: 10px;
}
.sb-header .play-box {
  width: 26px; height: 18px; background: white; border-radius: 3px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sb-header .play-tri {
  width: 0; height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 8px solid var(--red);
  margin-left: 2px;
}
.sb-header .sb-title { font-size: 0.95rem; font-weight: 700; color: white !important; letter-spacing: -0.01em; }

.sb-inner { padding: 0 0.9rem 1rem 0.9rem; }

.sb-label {
  font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--muted) !important;
  padding: 0.85rem 0 0.35rem 0;
  border-top: 1px solid var(--border);
  margin-top: 0.4rem;
  display: block;
}
.sb-label:first-of-type { border-top: none; padding-top: 0.6rem; }

.api-ok  { color: #1b6b3a; background: #e6f4ec; border-radius: 6px; padding: 5px 10px; font-size: 0.78rem; font-weight: 600; display:block; }
.api-err { color: #a31515; background: #fde8e8; border-radius: 6px; padding: 5px 10px; font-size: 0.78rem; font-weight: 600; display:block; }

.kw-pill {
  display: flex; align-items: center; justify-content: space-between;
  background: white; border: 1px solid var(--border);
  border-radius: 7px; padding: 5px 9px;
  margin-bottom: 3px; font-size: 0.8rem; font-weight: 500;
}
.kw-pill .kw-name { color: var(--red); font-weight: 600; }

.quota-bar-bg { background: var(--border); border-radius: 999px; height: 5px; margin: 5px 0 3px; }
.quota-bar-fg { border-radius: 999px; height: 5px; transition: width .3s; }

/* ── Cards ── */
.yt-card {
  background: white; border: 1px solid var(--border);
  border-radius: 12px; padding: 0.9rem 1.1rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: box-shadow .2s; height: 100%;
}
.yt-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.08); }
.yt-card-red { border-left: 3px solid var(--red); }
.yt-lbl { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); margin-bottom: 3px; }
.yt-val { font-size: 1.6rem; font-weight: 700; color: var(--black); line-height: 1.1; }
.yt-sub { font-size: 0.73rem; color: var(--muted); margin-top: 2px; }

/* ── Section head ── */
.sh { display: flex; align-items: center; gap: 6px; border-bottom: 2px solid var(--red); padding-bottom: 5px; margin: 1.4rem 0 0.9rem; }
.sh span { font-size: 0.95rem; font-weight: 700; color: var(--black); }

/* ── Viral cards ── */
.vc {
  background: white; border: 1px solid var(--border);
  border-radius: 9px; padding: 0.8rem 0.95rem;
  margin-bottom: 5px; transition: box-shadow .15s, border-color .15s, transform .1s;
}
.vc:hover { box-shadow: 0 3px 10px rgba(0,0,0,0.07); }
.vc-link {
  border-left: 3px solid transparent;
  transition: box-shadow .15s, border-color .15s, transform .1s !important;
}
.vc-link:hover {
  box-shadow: 0 4px 16px rgba(255,0,0,0.12) !important;
  border-color: var(--red) !important;
  transform: translateY(-1px);
}
.vc-title { font-weight: 600; font-size: 0.87rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--black); }
.vc-ch    { color: var(--muted); font-size: 0.75rem; margin-top: 1px; }
.vc-stats { display: flex; gap: 12px; margin-top: 7px; font-size: 0.77rem; color: var(--muted); flex-wrap: wrap; }

.badge { display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }
.b-hot  { background: #FFE5E5; color: #CC0000; }
.b-warm { background: #FFF3E0; color: #C45000; }
.b-cool { background: #E8F5E9; color: #2E7D32; }

/* ── Tooltip ── */
.tt {
  display: inline-flex; align-items: center; gap: 3px;
  position: relative; cursor: help;
}
.tt-i {
  width: 13px; height: 13px;
  background: #E0E0E0; color: #555;
  border-radius: 50%; font-size: 8px; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  flex-shrink: 0; vertical-align: middle;
}
.tt-b {
  visibility: hidden; opacity: 0;
  position: absolute; z-index: 9999;
  bottom: calc(100% + 7px); left: 50%; transform: translateX(-50%);
  background: #111; color: #eee;
  font-size: 0.74rem; font-weight: 400; line-height: 1.5;
  border-radius: 7px; padding: 8px 11px;
  width: 230px; text-align: left;
  pointer-events: none; transition: opacity .15s;
  box-shadow: 0 6px 18px rgba(0,0,0,0.3);
}
.tt-b::after {
  content: ''; position: absolute;
  top: 100%; left: 50%; transform: translateX(-50%);
  border: 5px solid transparent; border-top-color: #111;
}
.tt:hover .tt-b { visibility: visible; opacity: 1; }

/* ── Log ── */
.log-box {
  background: #0d0d0d; border: 1px solid var(--border);
  border-radius: 8px; padding: 0.85rem;
  font-family: 'Courier New', monospace;
  font-size: 0.77rem; max-height: 210px; overflow-y: auto;
}
.lo { color: #4caf50; } .lw { color: #ff9800; } .le { color: #f44336; } .li { color: #42a5f5; }

/* ── Buttons / controls ── */
.stButton > button {
  background: var(--red) !important; color: white !important;
  border: none !important; border-radius: 4px !important;
  font-weight: 600 !important; font-size: 0.87rem !important;
  transition: background .15s !important;
}
.stButton > button:hover { background: var(--red-dk) !important; }
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { font-weight: 600; color: var(--muted); padding: 0.55rem 1rem; }
.stTabs [aria-selected="true"] { color: var(--black) !important; border-bottom: 2px solid var(--red) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 8px; }
[data-baseweb="slider"] [role="slider"] { background: var(--red) !important; }
[data-testid="stMetric"] { background: white; border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem 0.75rem; }
[data-testid="stMetricValue"] { font-size: 1rem !important; font-weight: 700 !important; color: var(--black) !important; }
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
REGION_CODE = "ID"
OUTPUT_FILE = "yt_shorts_trending.csv"
CATEGORY_MAP = {
    "1":"Film & Animation","2":"Autos & Vehicles","10":"Music",
    "15":"Pets & Animals","17":"Sports","19":"Travel & Events",
    "20":"Gaming","22":"People & Blogs","23":"Comedy",
    "24":"Entertainment","25":"News & Politics","26":"Howto & Style",
    "27":"Education","28":"Science & Technology","29":"Nonprofits & Activism",
}
CSV_FIELDS = [
    "collected_at","video_id","title","channel_id","channel_title",
    "published_at","duration_seconds","view_count","like_count",
    "comment_count","category_id","category_name","tags",
    "description_snippet","thumbnail_url","video_url","search_keyword",
]
DEFAULT_KEYWORDS = ["#shortsIndonesia","#viral","#trending","#fyp","#shortsvideo"]

# ── Tooltip helper ─────────────────────────────────────────────────────────────
def tt(label: str, tip: str) -> str:
    return f'<span class="tt">{label}<span class="tt-i">?</span><span class="tt-b">{tip}</span></span>'

TIPS = {
    "viral_score":      "Skor 0–100 yang menggabungkan Engagement Rate (40%) + Velocity (40%) + Views (20%). Makin tinggi = makin berpotensi viral.",
    "engagement_rate":  "Persentase penonton yang bereaksi aktif. Rumus: (Likes + Comments) ÷ Views. Angka 1–3% sudah bagus untuk Shorts.",
    "velocity":         "Kecepatan penumpukan view sejak upload. Rumus: Views ÷ Jam sejak publish. Makin tinggi = tumbuh makin cepat.",
    "like_ratio":       "Berapa persen penonton yang menekan Like. Rumus: Likes ÷ Views. Indikator seberapa disukai kontennya.",
    "badge_hot":        "🔥 Hot = Viral Score ≥ 70. Video ini punya kombinasi engagement tinggi + kecepatan tumbuh yang sangat kuat.",
    "badge_warm":       "⚡ Warm = Viral Score 40–69. Performa bagus dan berpotensi terus naik.",
    "badge_cool":       "📗 Rising = Viral Score < 40. Masih tumbuh atau baru diupload. Pantau terus.",
    "views":            "Total jumlah kali video ditonton.",
    "likes":            "Jumlah penonton yang menekan tombol Like.",
    "comments":         "Jumlah komentar di video.",
    "duration":         "Durasi video dalam detik. Shorts yang terdeteksi: 5–180 detik.",
    "quota":            "YouTube Data API gratis: 10.000 unit/hari. Search = 100 unit, ambil detail = 1 unit per video.",
    "heatmap":          "Peta warna: kombinasi hari × jam upload vs rata-rata views. Merah tua = performa terbaik.",
    "wib":              "Waktu Indonesia Barat (UTC+7). Timestamp YouTube (UTC) sudah dikonversi otomatis.",
    "max_results":      "Berapa banyak video dicari per keyword. Makin banyak = data makin lengkap, kuota makin besar.",
    "category":         "Kategori konten yang ditetapkan kreator saat upload di YouTube.",
    "best_time":        "Dihitung dari rata-rata views tertinggi per slot waktu dalam dataset ini — bukan riset global YouTube.",
    "vhr":              "Views per Hour — jumlah view yang masuk per jam sejak video diupload.",
}

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in {"keywords": DEFAULT_KEYWORDS.copy(), "logs": [], "results_df": pd.DataFrame()}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Core helpers ───────────────────────────────────────────────────────────────
def parse_duration(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m: return 0
    return int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0)

def is_shorts(sec: int) -> bool: return 5 <= sec <= 180

def fmt_num(n) -> str:
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def add_log(msg: str, kind: str = "info"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    cls = {"ok":"lo","warn":"lw","err":"le","info":"li"}.get(kind,"li")
    st.session_state.logs.append(f'<span class="{cls}">[{ts}] {msg}</span>')

def build_yt(k): return build("youtube","v3",developerKey=k)

def search_shorts_api(yt, keyword, max_results):
    ids, fetched, pt = [], 0, None
    while fetched < max_results:
        bs = min(50, max_results - fetched)
        try:
            resp = yt.search().list(
                part="id", q=keyword, type="video", videoDuration="short",
                regionCode=REGION_CODE, relevanceLanguage="id", order="viewCount",
                maxResults=bs, pageToken=pt,
            ).execute()
            items = resp.get("items", [])
            ids.extend([i["id"]["videoId"] for i in items])
            fetched += len(items); pt = resp.get("nextPageToken")
            if not pt or not items: break
        except HttpError as e:
            add_log(f"Search gagal '{keyword}': {e}", "err"); break
    return ids[:max_results]

def get_details(yt, video_ids):
    out = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        try:
            resp = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(batch)).execute()
            out.extend(resp.get("items", []))
        except HttpError as e:
            add_log(f"Detail gagal: {e}", "err")
    return out

def parse_item(item, keyword, collected_at):
    sn=item.get("snippet",{}); st_=item.get("statistics",{}); cd=item.get("contentDetails",{})
    dur=parse_duration(cd.get("duration","PT0S"))
    if not is_shorts(dur): return None
    cat_id=sn.get("categoryId","")
    thumbs=sn.get("thumbnails",{})
    thumb=(thumbs.get("maxres") or thumbs.get("high") or thumbs.get("default") or {}).get("url","")
    return {
        "collected_at":collected_at,"video_id":item["id"],"title":sn.get("title",""),
        "channel_id":sn.get("channelId",""),"channel_title":sn.get("channelTitle",""),
        "published_at":sn.get("publishedAt",""),"duration_seconds":dur,
        "view_count":int(st_.get("viewCount",0)),"like_count":int(st_.get("likeCount",0)),
        "comment_count":int(st_.get("commentCount",0)),"category_id":cat_id,
        "category_name":CATEGORY_MAP.get(cat_id,"Unknown"),"tags":"|".join(sn.get("tags",[])),
        "description_snippet":sn.get("description","").replace("\n"," ")[:200],
        "thumbnail_url":thumb,"video_url":f"https://www.youtube.com/shorts/{item['id']}",
        "search_keyword":keyword,
    }

def run_collect(api_key, kw_configs):
    yt=build_yt(api_key); collected_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_rows,seen_ids=[],set()
    add_log(f"Mulai koleksi — {len(kw_configs)} keyword(s)","info")
    for cfg in kw_configs:
        kw,mr=cfg["keyword"],cfg["max_results"]
        add_log(f"→ Searching '{kw}' (max {mr}) ...","info")
        ids=search_shorts_api(yt,kw,mr)
        new_ids=[v for v in ids if v not in seen_ids]; seen_ids.update(new_ids)
        if not new_ids: add_log(f"  Tidak ada video baru untuk '{kw}'","warn"); continue
        add_log(f"  {len(new_ids)} video ID, ambil detail ...","info")
        items=get_details(yt,new_ids); count=0
        for item in items:
            row=parse_item(item,kw,collected_at)
            if row: all_rows.append(row); count+=1
        add_log(f"  ✓ {count} Shorts valid dari '{kw}'","ok")
        time.sleep(0.8)
    if not all_rows: add_log("Tidak ada data terkumpul.","warn"); return pd.DataFrame()
    df=pd.DataFrame(all_rows,columns=CSV_FIELDS)
    fe=os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE,"a",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=CSV_FIELDS)
        if not fe: w.writeheader()
        w.writerows(all_rows)
    add_log(f"✓ {len(all_rows)} baris disimpan ke '{OUTPUT_FILE}'","ok")
    return df

def enrich_df(df):
    df=df.copy()
    for c in ["view_count","like_count","comment_count"]:
        df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0)
    df["published_dt"]=pd.to_datetime(df["published_at"],errors="coerce",utc=True)
    df["collected_dt"]=pd.to_datetime(df["collected_at"],errors="coerce",utc=True)
    df["engagement_rate"]=((df["like_count"]+df["comment_count"])/df["view_count"].replace(0,1)).round(4)
    df["like_ratio"]=(df["like_count"]/df["view_count"].replace(0,1)).round(4)
    df["hours_since_publish"]=((df["collected_dt"]-df["published_dt"]).dt.total_seconds()/3600).clip(lower=0.5)
    df["velocity"]=(df["view_count"]/df["hours_since_publish"]).round(1)
    def mm(s): mn,mx=s.min(),s.max(); return (s-mn)/(mx-mn+1e-9)
    df["viral_score"]=((mm(df["engagement_rate"])*0.4+mm(df["velocity"])*0.4+mm(df["view_count"])*0.2)*100).round(1)
    return df

def get_top_words(series, top_n=20):
    stopwords={
        "yang","dan","di","ke","dari","ini","itu","untuk","dengan","adalah","pada","juga",
        "tidak","akan","sudah","bisa","ada","lebih","saya","kamu","aku","nya","pun","lah",
        "kah","ya","iya","yg","dg","dgn","utk","jd","gak","ga","si","nih","tuh","deh",
        "dong","sih","loh","kan","banget","the","a","an","in","of","to","and","is","for",
        "on","at","by","with","i","you","my","me","we","it","this","that","was","are","be",
        "have","shorts","short","shortsid","shortsindo","shortsvideo","fyp","viral","trending","indonesia","id",
    }
    counter=collections.Counter()
    for text in series.dropna():
        for w in re.findall(r"[a-zA-Z]{3,}",str(text).lower()):
            if w not in stopwords: counter[w]+=1
    return counter.most_common(top_n)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Header merah
    st.markdown("""
    <div class="sb-header">
      <div class="play-box"><div class="play-tri"></div></div>
      <span class="sb-title">Shorts Analyzer</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-inner">', unsafe_allow_html=True)

    # API Key
    st.markdown('<span class="sb-label">🔑 API Key</span>', unsafe_allow_html=True)
    api_key_input = os.getenv("YOUTUBE_API_KEY","")
    override = st.text_input("override", value="", type="password",
                             placeholder="Override .env (opsional)", label_visibility="collapsed")
    if override.strip(): api_key_input = override.strip()

    if api_key_input:
        st.markdown('<span class="api-ok">✓ API Key terdeteksi</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="api-err">✗ Belum diset di .env</span>', unsafe_allow_html=True)
        st.caption("Buat file `.env` → `YOUTUBE_API_KEY=AIza...`")

    # Keywords
    st.markdown('<span class="sb-label">🔍 Keywords</span>', unsafe_allow_html=True)
    with st.form("add_kw", clear_on_submit=True):
        new_kw = st.text_input("kw", placeholder="Tambah keyword baru...", label_visibility="collapsed")
        if st.form_submit_button("＋ Tambah", use_container_width=True):
            kw = new_kw.strip()
            if kw and kw not in st.session_state.keywords:
                st.session_state.keywords.append(kw); st.rerun()

    to_remove = None
    for i, kw in enumerate(st.session_state.keywords):
        c1, c2 = st.columns([5,1])
        c1.markdown(f'<div class="kw-pill"><span class="kw-name">{kw}</span></div>', unsafe_allow_html=True)
        if c2.button("✕", key=f"rm_{i}", help=f"Hapus '{kw}'"): to_remove = i
    if to_remove is not None:
        st.session_state.keywords.pop(to_remove); st.rerun()

    # Max Results
    st.markdown(f'<span class="sb-label">{tt("📊 Max Results per Keyword", TIPS["max_results"])}</span>', unsafe_allow_html=True)
    use_global = st.toggle("Sama untuk semua", value=True)
    kw_configs = []
    if use_global:
        g_max = st.slider("g", 5, 100, 30, 5, label_visibility="collapsed")
        st.caption(f"Setiap keyword: **{g_max}** video")
        for kw in st.session_state.keywords:
            kw_configs.append({"keyword": kw, "max_results": g_max})
    else:
        for kw in st.session_state.keywords:
            mr = st.slider(kw, 5, 100, 30, 5, key=f"mr_{kw}")
            kw_configs.append({"keyword": kw, "max_results": mr})

    # Quota
    st.markdown(f'<span class="sb-label">{tt("⚡ Estimasi Kuota", TIPS["quota"])}</span>', unsafe_allow_html=True)
    est_q = len(kw_configs)*100 + sum(math.ceil(c["max_results"]/50) for c in kw_configs)
    pct_q = min(est_q/10000*100, 100)
    bar_c = "#FF0000" if pct_q>70 else ("#FF9800" if pct_q>40 else "#4CAF50")
    st.markdown(f"""
    <div style="font-size:0.78rem;color:var(--muted);margin-bottom:2px;">~{est_q:,} / 10,000 unit per hari</div>
    <div class="quota-bar-bg"><div class="quota-bar-fg" style="width:{pct_q:.1f}%;background:{bar_c};"></div></div>
    <div style="font-size:0.7rem;color:#999;">Search=100 unit/kw · Detail=1 unit/video</div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    run_btn = st.button("▶  Mulai Koleksi", use_container_width=True, type="primary",
                        disabled=not api_key_input or not st.session_state.keywords)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN HEADER
# ══════════════════════════════════════════════════════════════════════════════
cl, ct = st.columns([1,14])
with cl:
    st.markdown("""<div style="background:#FF0000;border-radius:8px;width:40px;height:28px;display:flex;
    align-items:center;justify-content:center;margin-top:8px;">
    <div style="width:0;height:0;border-top:7px solid transparent;border-bottom:7px solid transparent;
    border-left:12px solid white;margin-left:3px;"></div></div>""", unsafe_allow_html=True)
with ct:
    st.markdown("# YouTube Shorts Trend Analyzer")
st.markdown('<p style="color:#606060;margin-top:-0.4rem;font-size:0.88rem;">Kumpulkan & analisa data Shorts trending Indonesia dari YouTube Data API</p>', unsafe_allow_html=True)
st.markdown("---")

# ── Run ────────────────────────────────────────────────────────────────────────
if run_btn:
    st.session_state.logs=[]; st.session_state.results_df=pd.DataFrame()
    prog=st.progress(0,text="Menghubungi YouTube API...")
    with st.spinner(""):
        df_result=run_collect(api_key_input,kw_configs)
        prog.progress(100,text="✓ Selesai!")
    st.session_state.results_df=df_result

if st.session_state.logs:
    st.markdown(f'<div class="log-box">{"<br>".join(st.session_state.logs)}</div>', unsafe_allow_html=True)
    st.markdown("")

# ── Dashboard ──────────────────────────────────────────────────────────────────
raw_df = st.session_state.results_df

if not raw_df.empty:
    df = enrich_df(raw_df)

    # Metric cards row
    c1,c2,c3,c4,c5 = st.columns(5)
    def mcard(col, lbl, val, sub, tip):
        with col:
            st.markdown(f"""<div class="yt-card yt-card-red">
              <div class="yt-lbl">{tt(lbl, tip)}</div>
              <div class="yt-val">{val}</div>
              <div class="yt-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    mcard(c1,"Video",f"{len(df):,}",f"{len(st.session_state.keywords)} keyword",TIPS["views"])
    mcard(c2,"Total Views",fmt_num(df["view_count"].sum()),"semua video",TIPS["views"])
    mcard(c3,"Avg Engagement",f"{df['engagement_rate'].mean():.2%}","(likes+comments)÷views",TIPS["engagement_rate"])
    mcard(c4,"Avg Viral Score",f"{df['viral_score'].mean():.1f}","/100 — potensi viral",TIPS["viral_score"])
    mcard(c5,"Kategori #1",df["category_name"].value_counts().idxmax(),"terbanyak di data",TIPS["category"])
    st.markdown("")

    tab1,tab2,tab3,tab4 = st.tabs(["📊  Data & Top Videos","📈  Viral Score","⏱️  Timing Analysis","🧠  Content Pattern"])

    # ── TAB 1 ──────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="sh"><span>🏆 Top 10 Videos by Views</span></div>', unsafe_allow_html=True)
        top10 = (df[["title","channel_title","view_count","like_count","comment_count",
                      "duration_seconds","viral_score","category_name","video_url"]]
                 .sort_values("view_count",ascending=False).head(10).reset_index(drop=True))
        top10.index += 1
        disp = top10.copy()
        disp["view_count"]       = disp["view_count"].apply(fmt_num)
        disp["like_count"]       = disp["like_count"].apply(fmt_num)
        disp["comment_count"]    = disp["comment_count"].apply(fmt_num)
        disp["duration_seconds"] = disp["duration_seconds"].apply(lambda s: f"{s}s")
        disp["viral_score"]      = disp["viral_score"].apply(lambda s: f"{s:.1f}")
        disp.columns = ["Judul","Channel","Views 👁","Likes ❤","Komentar 💬","Durasi ⏱","Viral Score ⚡","Kategori","URL"]
        st.dataframe(disp, use_container_width=True)

        with st.expander("ℹ️ Keterangan kolom"):
            st.markdown(f"""
| Kolom | Keterangan |
|---|---|
| Views 👁 | {TIPS['views']} |
| Likes ❤ | {TIPS['likes']} |
| Komentar 💬 | {TIPS['comments']} |
| Durasi ⏱ | {TIPS['duration']} |
| Viral Score ⚡ | {TIPS['viral_score']} |
""")

        st.markdown('<div class="sh"><span>📂 Distribusi Kategori</span></div>', unsafe_allow_html=True)
        cat_df=df["category_name"].value_counts().reset_index(); cat_df.columns=["Kategori","Jumlah"]
        fig_cat=px.bar(cat_df,x="Kategori",y="Jumlah",color_discrete_sequence=["#FF0000"],template="plotly_white")
        fig_cat.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",
                              showlegend=False,xaxis_tickangle=-30,margin=dict(t=20,b=70))
        st.plotly_chart(fig_cat,use_container_width=True)

        buf=io.StringIO(); df.to_csv(buf,index=False)
        st.download_button("⬇ Download CSV",data=buf.getvalue().encode("utf-8"),
                           file_name=f"yt_shorts_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",mime="text/csv")

    # ── TAB 2 ──────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown(f"""
        <div class="sh"><span>📈 Viral Score & Growth Potential</span></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:0.8rem;">
          {tt('<span class="badge b-hot">🔥 Hot ≥70</span>', TIPS["badge_hot"])}
          {tt('<span class="badge b-warm">⚡ Warm 40–69</span>', TIPS["badge_warm"])}
          {tt('<span class="badge b-cool">📗 Rising &lt;40</span>', TIPS["badge_cool"])}
          <span style="font-size:0.76rem;color:var(--muted);">— hover untuk penjelasan</span>
        </div>
        <p style="color:#606060;font-size:0.84rem;margin-bottom:0.8rem;">
          {tt("Viral Score", TIPS["viral_score"])} =
          {tt("Engagement Rate", TIPS["engagement_rate"])} ×40% +
          {tt("Velocity", TIPS["velocity"])} ×40% + Views ×20%
        </p>
        """, unsafe_allow_html=True)

        fig_sc=px.scatter(df,x="view_count",y="engagement_rate",size="viral_score",color="viral_score",
                          hover_name="title",hover_data={"channel_title":True,"viral_score":True,"velocity":True,"like_ratio":True},
                          color_continuous_scale=["#FFEEEE","#FF0000"],size_max=40,template="plotly_white",
                          labels={"view_count":"Views","engagement_rate":"Engagement Rate","viral_score":"Viral Score"},
                          title="Views vs Engagement Rate  ·  ukuran titik = Viral Score")
        fig_sc.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",margin=dict(t=50,b=20))
        fig_sc.update_xaxes(tickformat=".2s"); fig_sc.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig_sc,use_container_width=True)

        st.markdown('<div class="sh"><span>🔥 Top 10 Viral Score</span></div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#606060;font-size:0.8rem;margin-bottom:0.7rem;">Klik kartu untuk langsung membuka video Shorts ↗</p>', unsafe_allow_html=True)
        top_viral=df.nlargest(10,"viral_score")[
            ["title","channel_title","viral_score","engagement_rate","velocity","like_ratio","view_count","video_url"]
        ].reset_index(drop=True)

        for i,(_,row) in enumerate(top_viral.iterrows()):
            s=row["viral_score"]
            bcls="b-hot" if s>=70 else ("b-warm" if s>=40 else "b-cool")
            blbl="🔥 Hot" if s>=70 else ("⚡ Warm" if s>=40 else "📗 Rising")
            btip=TIPS["badge_hot"] if s>=70 else (TIPS["badge_warm"] if s>=40 else TIPS["badge_cool"])
            url=row["video_url"]
            rank_color="#FF0000" if i==0 else ("#888" if i>=3 else "#C45000")
            st.markdown(f"""
            <a href="{url}" target="_blank" style="text-decoration:none;">
              <div class="vc vc-link">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">
                  <div style="display:flex;align-items:flex-start;gap:10px;min-width:0;flex:1;">
                    <span style="font-size:0.8rem;font-weight:700;color:{rank_color};min-width:18px;padding-top:1px;">#{i+1}</span>
                    <div style="min-width:0;">
                      <div class="vc-title">{row['title']}</div>
                      <div class="vc-ch">{row['channel_title']}</div>
                    </div>
                  </div>
                  <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                    {tt(f'<span class="badge {bcls}">{blbl} {s:.0f}</span>', btip)}
                    <span style="font-size:0.75rem;color:#999;">↗</span>
                  </div>
                </div>
                <div class="vc-stats">
                  <span>{tt("👁 "+fmt_num(row['view_count']), TIPS["views"])}</span>
                  <span>{tt("❤ "+f"{row['like_ratio']:.1%}", TIPS["like_ratio"])}</span>
                  <span>{tt("💬 Eng "+f"{row['engagement_rate']:.2%}", TIPS["engagement_rate"])}</span>
                  <span>{tt("⚡ "+f"{row['velocity']:,.0f} v/hr", TIPS["vhr"])}</span>
                </div>
              </div>
            </a>""", unsafe_allow_html=True)

        st.markdown('<div class="sh"><span>📊 Distribusi Metrik</span></div>', unsafe_allow_html=True)
        mc1,mc2,mc3=st.columns(3)
        for cw,xc,tip,fmt,lbl in [
            (mc1,"engagement_rate",TIPS["engagement_rate"],".1%","Engagement Rate"),
            (mc2,"velocity",TIPS["vhr"],",","Velocity (views/jam)"),
            (mc3,"like_ratio",TIPS["like_ratio"],".1%","Like Ratio"),
        ]:
            with cw:
                st.markdown(f'<div style="font-size:0.8rem;font-weight:600;margin-bottom:3px;">{tt(lbl,tip)}</div>', unsafe_allow_html=True)
                fh=px.histogram(df,x=xc,nbins=20,color_discrete_sequence=["#FF0000"],template="plotly_white")
                fh.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",
                                 showlegend=False,margin=dict(t=10,b=20),xaxis_title="",yaxis_title="Jumlah")
                fh.update_xaxes(tickformat=fmt)
                st.plotly_chart(fh,use_container_width=True)

    # ── TAB 3 ──────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown(f"""
        <div class="sh"><span>⏱️ Jam & Hari Upload Terbaik</span></div>
        <p style="color:#606060;font-size:0.84rem;margin-bottom:0.8rem;">
          Semua waktu dalam {tt("WIB (UTC+7)", TIPS["wib"])}.
          {tt("Heatmap", TIPS["heatmap"])} menunjukkan avg views per slot waktu — merah tua = terbaik.
        </p>
        """, unsafe_allow_html=True)

        df_t=df.dropna(subset=["published_dt"]).copy()
        df_t["upload_hour_wib"]=(df_t["published_dt"].dt.hour+7)%24
        df_t["upload_day_wib"]=df_t["published_dt"].dt.tz_convert(None).dt.day_name()
        day_order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

        hm=df_t.groupby(["upload_day_wib","upload_hour_wib"])["view_count"].mean().reset_index()
        hm=hm.rename(columns={"upload_day_wib":"Hari","upload_hour_wib":"Jam","view_count":"Avg Views"})
        hmp=hm.pivot(index="Hari",columns="Jam",values="Avg Views").reindex(day_order)

        fig_hm=go.Figure(data=go.Heatmap(
            z=hmp.values, x=[f"{h:02d}:00" for h in hmp.columns], y=hmp.index.tolist(),
            colorscale=[[0,"#FFFFFF"],[0.5,"#FF6B6B"],[1,"#CC0000"]],
            hoverongaps=False,
            hovertemplate="Hari: %{y}<br>Jam: %{x} WIB<br>Avg Views: %{z:,.0f}<extra></extra>",
        ))
        fig_hm.update_layout(title="Heatmap: Jam Upload (WIB) × Hari vs Rata-rata Views",
                             plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",
                             height=330,margin=dict(t=50,b=20,l=100),
                             xaxis_title="Jam Upload (WIB)",yaxis_title="")
        st.plotly_chart(fig_hm,use_container_width=True)

        ct1,ct2=st.columns(2)
        with ct1:
            hp=df_t.groupby("upload_hour_wib").agg(avg_views=("view_count","mean"),avg_eng=("engagement_rate","mean"),count=("video_id","count")).reset_index()
            fhr=px.bar(hp,x="upload_hour_wib",y="avg_views",color="avg_eng",
                       color_continuous_scale=["#FFEEEE","#FF0000"],template="plotly_white",
                       labels={"upload_hour_wib":"Jam WIB","avg_views":"Avg Views","avg_eng":"Avg Eng Rate"},
                       title="Avg Views per Jam Upload")
            fhr.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",margin=dict(t=50,b=20))
            fhr.update_yaxes(tickformat=".2s")
            st.plotly_chart(fhr,use_container_width=True)
        with ct2:
            dp=df_t.groupby("upload_day_wib").agg(avg_views=("view_count","mean"),avg_eng=("engagement_rate","mean"),count=("video_id","count")).reindex(day_order).dropna().reset_index()
            fday=px.bar(dp,x="upload_day_wib",y="avg_views",color="avg_eng",
                        color_continuous_scale=["#FFEEEE","#FF0000"],template="plotly_white",
                        labels={"upload_day_wib":"Hari","avg_views":"Avg Views","avg_eng":"Avg Eng Rate"},
                        title="Avg Views per Hari Upload")
            fday.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",margin=dict(t=50,b=20))
            fday.update_yaxes(tickformat=".2s")
            st.plotly_chart(fday,use_container_width=True)

        if not hp.empty and not dp.empty:
            bh=int(hp.loc[hp["avg_views"].idxmax(),"upload_hour_wib"])
            bd=dp.loc[dp["avg_views"].idxmax(),"upload_day_wib"]
            st.markdown(f"""
            <div class="yt-card yt-card-red" style="text-align:center;padding:1.2rem;">
              <div class="yt-lbl">{tt("🎯 Waktu Upload Terbaik", TIPS["best_time"])}</div>
              <div class="yt-val" style="font-size:1.7rem;">{bd} · {bh:02d}:00 – {bh+1:02d}:00 WIB</div>
              <div class="yt-sub">Dari rata-rata views tertinggi di dataset ini — {tt("baca catatan", TIPS["best_time"])}</div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 4 ──────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="sh"><span>🧠 Content Pattern Analysis</span></div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#606060;font-size:0.84rem;margin-bottom:0.8rem;">Kata & hashtag yang paling sering muncul di video trending — petunjuk tema yang sedang digemari.</p>', unsafe_allow_html=True)

        nc1,nc2=st.columns(2)
        with nc1:
            st.markdown("**Kata Populer dari Judul**")
            tw=get_top_words(df["title"],top_n=20)
            if tw:
                tw_df=pd.DataFrame(tw,columns=["Kata","Frekuensi"])
                ftw=px.bar(tw_df.sort_values("Frekuensi"),x="Frekuensi",y="Kata",orientation="h",
                           color="Frekuensi",color_continuous_scale=["#FFEEEE","#FF0000"],template="plotly_white")
                ftw.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",
                                  showlegend=False,margin=dict(t=5,b=5,l=5,r=5),height=420,coloraxis_showscale=False)
                st.plotly_chart(ftw,use_container_width=True)

        with nc2:
            st.markdown("**Hashtag Populer dari Tags**")
            all_tags=df["tags"].dropna().str.split("|").explode()
            all_tags=all_tags[all_tags.str.len()>1]
            tc=all_tags.str.lower().str.strip().value_counts().head(20).reset_index(); tc.columns=["Hashtag","Frekuensi"]
            if not tc.empty:
                ftg=px.bar(tc.sort_values("Frekuensi"),x="Frekuensi",y="Hashtag",orientation="h",
                           color="Frekuensi",color_continuous_scale=["#FFEEEE","#FF0000"],template="plotly_white")
                ftg.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",
                                  showlegend=False,margin=dict(t=5,b=5,l=5,r=5),height=420,coloraxis_showscale=False)
                st.plotly_chart(ftg,use_container_width=True)

        st.markdown('<div class="sh"><span>📝 Kata Populer dari Deskripsi</span></div>', unsafe_allow_html=True)
        dw=get_top_words(df["description_snippet"],top_n=25)
        if dw:
            dw_df=pd.DataFrame(dw,columns=["Kata","Frekuensi"])
            fdw=px.bar(dw_df,x="Kata",y="Frekuensi",color="Frekuensi",
                       color_continuous_scale=["#FFEEEE","#FF0000"],template="plotly_white")
            fdw.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_family="DM Sans",
                              showlegend=False,margin=dict(t=5,b=65,l=5,r=5),height=270,coloraxis_showscale=False)
            fdw.update_xaxes(tickangle=-35)
            st.plotly_chart(fdw,use_container_width=True)

        st.markdown('<div class="sh"><span>🗂️ Kata per Kategori Teratas</span></div>', unsafe_allow_html=True)
        cats=df["category_name"].value_counts().head(4).index.tolist()
        cat_cols=st.columns(len(cats))
        for col,cat in zip(cat_cols,cats):
            with col:
                st.markdown(f'<div style="font-weight:700;font-size:0.8rem;color:#FF0000;margin-bottom:5px;">{cat}</div>', unsafe_allow_html=True)
                words=get_top_words(df[df["category_name"]==cat]["title"],top_n=8)
                for word,freq in words:
                    pct=int(freq/(words[0][1]+1e-9)*100)
                    st.markdown(f"""<div style="margin-bottom:4px;">
                      <div style="display:flex;justify-content:space-between;font-size:0.77rem;">
                        <span style="color:#0F0F0F;font-weight:500">{word}</span>
                        <span style="color:#606060">{freq}</span>
                      </div>
                      <div style="background:#F0F0F0;border-radius:999px;height:3px;margin-top:1px;">
                        <div style="background:#FF0000;width:{pct}%;height:3px;border-radius:999px;"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:5rem 2rem;">
      <div style="background:#FF0000;border-radius:10px;width:60px;height:40px;display:inline-flex;
      align-items:center;justify-content:center;margin-bottom:1.2rem;">
        <div style="width:0;height:0;border-top:9px solid transparent;border-bottom:9px solid transparent;
        border-left:16px solid white;margin-left:3px;"></div>
      </div>
      <div style="font-size:1.1rem;font-weight:700;color:#0F0F0F;margin-bottom:5px;">Siap menganalisa Shorts Indonesia</div>
      <div style="color:#606060;font-size:0.86rem;">Atur keyword di sidebar, lalu klik <b>▶ Mulai Koleksi</b></div>
    </div>""", unsafe_allow_html=True)