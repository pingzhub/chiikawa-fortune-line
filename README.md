# ちいかわ占い → LINE

ดึงรูปดวง 12 ราศีจาก mezamashi.media ทุกเช้า ต่อเป็นภาพเดียว แล้ว push เข้าไลน์ตัวเอง

## ทำไมไม่ตัดเฉพาะราศีกุมภ์

ชื่อราศีบนเว็บอยู่ **ในรูปภาพ** ไม่มีเป็นข้อความ (alt ก็ว่าง) เลย match ไม่ได้ถ้าไม่ทำ OCR
สคริปต์นี้เลยส่งครบทั้ง 12 ราศีเรียงจากอันดับ 1 → 12 ลงมา หาเองในภาพเดียวจบ

ถ้าอยากตัดเฉพาะราศีกุมภ์จริง ๆ ต้องเพิ่ม `pytesseract` + `tesseract-ocr-jpn` แล้ว match คำว่า `みずがめ` — แม่นราว 80-90% กับฟอนต์การ์ตูนแบบนี้ ไม่แนะนำเป็นด่านแรก

## Setup

### 1. LINE Messaging API

1. [LINE Developers Console](https://developers.line.biz/console/) → สร้าง Provider → สร้าง **Messaging API channel**
2. แท็บ Messaging API → **Channel access token (long-lived)** → Issue → เก็บไว้
3. แอดบอทตัวเองเป็นเพื่อนจาก QR ในหน้าเดียวกัน
4. หา `userId` ของตัวเอง: แท็บ Basic settings → **Your user ID** (ขึ้นต้นด้วย `U`)

> ต้องเป็น push message เท่านั้น (reply ใช้ไม่ได้เพราะไม่มี event มาก่อน)
> โควตาฟรีของ Messaging API คือ 200 ข้อความ/เดือน — วันละ 2 ข้อความ = ~60/เดือน พอสบาย

### 2. Repo

สร้าง repo **public** (จำเป็น เพราะ LINE ต้องโหลดรูปจาก raw.githubusercontent ได้)
วางไฟล์ทั้งหมด แล้วใส่ Secrets ที่ Settings → Secrets and variables → Actions:

| Secret | ค่า |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | token จากข้อ 1 |
| `LINE_USER_ID` | `U...` |

### 3. ทดสอบ

```bash
pip install playwright requests pillow
playwright install chromium
python scrape.py          # ได้ images/YYYY-MM-DD.jpg
```

เปิดดูก่อนว่าได้ครบ 12 รูปไหม ถ้าได้เยอะ/น้อยกว่านั้น ปรับ threshold `counts[u] >= 3`
ใน `scrape.py` (บรรทัดตัดรูป eyecatch ออก)

จากนั้นใน GitHub → Actions → **Run workflow** เพื่อยิงมือครั้งแรก

## เวลา

- เว็บอัปเดต จันทร์–เสาร์ หลัง 07:00 JST
- workflow ตั้งไว้ 22:15 UTC = **07:15 JST = 05:15 น. เวลาไทย**
- cron ของ GitHub Actions ดีเลย์ได้ 5–15 นาที ถือว่าปกติ

## ข้อควรระวัง

- repo ต้อง public → รูปลิขสิทธิ์ ©ナガノ/ちいかわ製作委員会 จะเข้าถึงได้จากภายนอก
  step `Prune old images` เลยลบไฟล์เก่าเหลือ 30 วันล่าสุด
  ถ้าไม่สบายใจ เปลี่ยนไปใช้ Vercel Blob แทน (repo เป็น private ได้) — แก้แค่ `IMAGE_URL`
- ถ้าเว็บเปลี่ยนโครงสร้าง สคริปต์จะ exit 1 และ Actions จะขึ้นแดง = รู้ทันที
