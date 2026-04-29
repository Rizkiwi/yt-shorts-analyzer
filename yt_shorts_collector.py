"""
YouTube Shorts Trend Collector — Trending Indonesia
====================================================
Mengambil data Shorts yang trending di Indonesia dan menyimpannya ke CSV.

Setup:
  1. Buat file .env di folder yang sama, isi dengan:
     YOUTUBE_API_KEY=your_api_key_here
  2. pip install google-api-python-client pandas python-dotenv
  3. python yt_shorts_collector.py
"""

import os
import csv
import time
import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY         = os.getenv("YOUTUBE_API_KEY")
REGION_CODE     = "ID"          # Indonesia
MAX_RESULTS     = 50            # per keyword, maks 50 per request
OUTPUT_FILE     = "yt_shorts_trending.csv"

# Kata kunci yang relevan untuk menangkap Shorts Indonesia
# YouTube tidak punya endpoint khusus "trending Shorts", jadi kita pakai
# kombinasi keyword + filter durasi pendek + region
SEARCH_KEYWORDS = [
    "#shortsIndonesia",
    "#shortsvideo",
    "#viral",
    "#trending",
    "#fyp",
]

# Kategori YouTube (opsional, bisa di-filter nanti di dashboard)
# Referensi: https://developers.google.com/youtube/v3/docs/videoCategories
CATEGORY_MAP = {
    "1":  "Film & Animation",
    "2":  "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
}

CSV_FIELDS = [
    "collected_at",
    "video_id",
    "title",
    "channel_id",
    "channel_title",
    "published_at",
    "duration_seconds",
    "view_count",
    "like_count",
    "comment_count",
    "category_id",
    "category_name",
    "tags",
    "description_snippet",
    "thumbnail_url",
    "video_url",
    "search_keyword",
]

# ── YouTube API helper ───────────────────────────────────────────────────────

def build_youtube():
    if not API_KEY:
        raise ValueError(
            "API key tidak ditemukan. Pastikan file .env berisi YOUTUBE_API_KEY=..."
        )
    return build("youtube", "v3", developerKey=API_KEY)


def parse_duration_to_seconds(iso_duration: str) -> int:
    """
    Mengubah durasi ISO 8601 (PT1M30S) ke detik.
    Shorts biasanya <= 60 detik, tapi YouTube kadang return sampai 3 menit.
    """
    import re
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, iso_duration)
    if not match:
        return 0
    hours   = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def search_shorts(youtube, keyword: str, max_results: int = 50) -> list[str]:
    """
    Cari video berdasarkan keyword, filter yang kemungkinan Shorts.
    Return list of video IDs.
    """
    video_ids = []
    try:
        request = youtube.search().list(
            part="id",
            q=keyword,
            type="video",
            videoDuration="short",   # <= 4 menit (filter YouTube, bukan persis Shorts)
            regionCode=REGION_CODE,
            relevanceLanguage="id",  # Bahasa Indonesia
            order="viewCount",       # Prioritas yang banyak ditonton
            maxResults=max_results,
        )
        response = request.execute()
        for item in response.get("items", []):
            video_ids.append(item["id"]["videoId"])
    except HttpError as e:
        print(f"  [ERROR] Search gagal untuk '{keyword}': {e}")
    return video_ids


def get_video_details(youtube, video_ids: list[str]) -> list[dict]:
    """
    Ambil detail lengkap untuk list video ID.
    Bisa batch sampai 50 ID sekaligus (hemat quota).
    """
    if not video_ids:
        return []

    videos = []
    # Proses per 50 (limit API)
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        try:
            request = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch),
            )
            response = request.execute()
            videos.extend(response.get("items", []))
        except HttpError as e:
            print(f"  [ERROR] Gagal ambil video details: {e}")
    return videos


def is_likely_shorts(duration_seconds: int) -> bool:
    """
    Filter video yang kemungkinan Shorts: durasi 5–180 detik.
    YouTube Shorts resminya max 60 detik, tapi di API sering masuk sampai 3 menit.
    """
    return 5 <= duration_seconds <= 180


def parse_video(item: dict, keyword: str, collected_at: str) -> dict | None:
    """
    Ekstrak field yang kita butuhkan dari response API.
    Return None kalau bukan Shorts.
    """
    snippet         = item.get("snippet", {})
    statistics      = item.get("statistics", {})
    content_details = item.get("contentDetails", {})

    duration_sec = parse_duration_to_seconds(content_details.get("duration", "PT0S"))

    if not is_likely_shorts(duration_sec):
        return None

    category_id   = snippet.get("categoryId", "")
    category_name = CATEGORY_MAP.get(category_id, "Unknown")
    tags          = "|".join(snippet.get("tags", []))  # join pakai | biar CSV aman
    description   = snippet.get("description", "").replace("\n", " ")[:200]
    thumbnails    = snippet.get("thumbnails", {})
    thumbnail_url = (
        thumbnails.get("maxres", {}).get("url")
        or thumbnails.get("high", {}).get("url")
        or thumbnails.get("default", {}).get("url", "")
    )

    return {
        "collected_at":       collected_at,
        "video_id":           item["id"],
        "title":              snippet.get("title", ""),
        "channel_id":         snippet.get("channelId", ""),
        "channel_title":      snippet.get("channelTitle", ""),
        "published_at":       snippet.get("publishedAt", ""),
        "duration_seconds":   duration_sec,
        "view_count":         int(statistics.get("viewCount", 0)),
        "like_count":         int(statistics.get("likeCount", 0)),
        "comment_count":      int(statistics.get("commentCount", 0)),
        "category_id":        category_id,
        "category_name":      category_name,
        "tags":               tags,
        "description_snippet": description,
        "thumbnail_url":      thumbnail_url,
        "video_url":          f"https://www.youtube.com/shorts/{item['id']}",
        "search_keyword":     keyword,
    }


# ── Main collector ───────────────────────────────────────────────────────────

def collect():
    youtube      = build_youtube()
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_rows     = []
    seen_ids     = set()  # deduplikasi, satu video bisa muncul di banyak keyword

    print(f"\n{'='*55}")
    print(f"  YouTube Shorts Collector — {collected_at}")
    print(f"  Region: {REGION_CODE} | Keywords: {len(SEARCH_KEYWORDS)}")
    print(f"{'='*55}\n")

    for keyword in SEARCH_KEYWORDS:
        print(f"[→] Searching: '{keyword}' ...")

        video_ids = search_shorts(youtube, keyword, MAX_RESULTS)
        print(f"    Ditemukan {len(video_ids)} video ID")

        # Filter yang sudah pernah kita proses di run ini
        new_ids = [vid for vid in video_ids if vid not in seen_ids]
        seen_ids.update(new_ids)

        if not new_ids:
            print("    Semua sudah ada, skip.\n")
            continue

        videos = get_video_details(youtube, new_ids)
        print(f"    Ambil detail {len(videos)} video ...")

        count = 0
        for item in videos:
            row = parse_video(item, keyword, collected_at)
            if row:
                all_rows.append(row)
                count += 1

        print(f"    ✓ {count} Shorts valid ditambahkan\n")

        # Jeda antar keyword biar tidak kena rate limit
        time.sleep(1)

    # ── Simpan ke CSV ────────────────────────────────────────────────────────
    if not all_rows:
        print("Tidak ada data yang berhasil dikumpulkan.")
        return

    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()  # tulis header hanya jika file baru
        writer.writerows(all_rows)

    print(f"{'='*55}")
    print(f"  ✓ {len(all_rows)} Shorts disimpan ke '{OUTPUT_FILE}'")
    print(f"{'='*55}\n")

    # Preview 5 baris teratas
    print("Preview data:")
    print(f"  {'Title':<40} {'Views':>10} {'Durasi':>8} {'Kategori'}")
    print(f"  {'-'*40} {'-'*10} {'-'*8} {'-'*20}")
    for row in sorted(all_rows, key=lambda x: x["view_count"], reverse=True)[:5]:
        title = row["title"][:38] + ".." if len(row["title"]) > 40 else row["title"]
        print(f"  {title:<40} {row['view_count']:>10,} {row['duration_seconds']:>6}s  {row['category_name']}")
    print()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    collect()