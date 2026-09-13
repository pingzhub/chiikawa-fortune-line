"""
ちいかわ占い -> รวมรูปทั้ง 12 ราศีเป็นภาพเดียว

ทำงาน:
  1. เปิดหน้า page 1-5 ด้วย Playwright, scroll ให้ lazy-load ทำงาน
  2. เก็บ src ของรูปทุกใบใน article
  3. ตัดรูปที่ซ้ำข้ามหลายหน้าออก (= eyecatch/ไอคอน ไม่ใช่รูปดวง)
  4. ต่อรูปแนวตั้งเป็นไฟล์เดียว -> images/YYYY-MM-DD.jpg

ใช้: python scrape.py
"""

import io
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from PIL import Image
from playwright.sync_api import sync_playwright

BASE = "https://mezamashi.media/feature/chiikawa-fortune-daily"
PAGES = [BASE] + [f"{BASE}?page={n}" for n in range(2, 6)]
JST = timezone(timedelta(hours=9))
OUT_DIR = Path("images")

# รูปดวงมาจาก CDN นี้ ส่วนไอคอน/โลโก้อยู่ใต้ /common/
CDN_RE = re.compile(r"mezamashi\.ismcdn\.jp/mwimgs/")
SKIP_RE = re.compile(r"/common/|\.svg$")


def collect_image_urls() -> list[str]:
    """คืน src ของรูปดวงตามลำดับหน้า 1->5"""
    per_page: list[list[str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 900, "height": 1200},
            locale="ja-JP",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        for url in PAGES:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(2000)
            # scroll ทีละหน้าจอให้ lazy-load ยิงครบ
            for _ in range(12):
                page.mouse.wheel(0, 900)
                page.wait_for_timeout(350)
            page.wait_for_timeout(1500)

            srcs = page.eval_on_selector_all(
                "img",
                "els => els.map(e => e.currentSrc || e.src || '')",
            )
            keep = [
                s for s in srcs
                if s and CDN_RE.search(s) and not SKIP_RE.search(s)
            ]
            per_page.append(keep)
            print(f"  {url} -> {len(keep)} รูป", file=sys.stderr)

        browser.close()

    # รูปที่โผล่ตั้งแต่ 3 หน้าขึ้นไป = eyecatch / related articles
    counts = Counter(u for pg in per_page for u in set(pg))
    ordered: list[str] = []
    seen: set[str] = set()
    for pg in per_page:
        for u in pg:
            if counts[u] >= 3 or u in seen:
                continue
            seen.add(u)
            ordered.append(u)
    return ordered


def download(urls: list[str]) -> list[Image.Image]:
    sess = requests.Session()
    sess.headers["Referer"] = BASE
    sess.headers["User-Agent"] = "Mozilla/5.0"
    imgs = []
    for u in urls:
        r = sess.get(u, timeout=30)
        if r.ok and r.headers.get("content-type", "").startswith("image/"):
            imgs.append(Image.open(io.BytesIO(r.content)).convert("RGB"))
    return imgs


def stitch(imgs: list[Image.Image], gap: int = 16) -> Image.Image:
    """ต่อแนวตั้ง ปรับความกว้างให้เท่ากันหมด"""
    w = max(i.width for i in imgs)
    scaled = [
        i if i.width == w else i.resize((w, round(i.height * w / i.width)), Image.LANCZOS)
        for i in imgs
    ]
    h = sum(i.height for i in scaled) + gap * (len(scaled) - 1)
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    y = 0
    for i in scaled:
        canvas.paste(i, (0, y))
        y += i.height + gap

    # LINE จำกัด 10MB และด้านยาวไม่ควรเกิน ~4000px
    if canvas.height > 4000:
        ratio = 4000 / canvas.height
        canvas = canvas.resize((round(w * ratio), 4000), Image.LANCZOS)
    return canvas


def main() -> int:
    today = datetime.now(JST).strftime("%Y-%m-%d")
    print(f"ดึงข้อมูลของวันที่ {today} (JST)", file=sys.stderr)

    urls = collect_image_urls()
    if not urls:
        print("ไม่เจอรูปดวงเลย — เว็บอาจเปลี่ยนโครงสร้าง", file=sys.stderr)
        return 1

    imgs = download(urls)
    if not imgs:
        print("โหลดรูปไม่สำเร็จ", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"{today}.jpg"
    stitch(imgs).save(out, "JPEG", quality=88, optimize=True)

    size_mb = out.stat().st_size / 1e6
    print(f"บันทึก {out} ({len(imgs)} รูป, {size_mb:.2f} MB)", file=sys.stderr)

    # ส่งค่าออกให้ GitHub Actions ใช้ต่อ
    print(f"date={today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
