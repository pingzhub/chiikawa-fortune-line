"""
ส่งรูปดวงเข้า LINE ผ่าน Messaging API (push message)

env ที่ต้องมี:
  LINE_CHANNEL_ID      - Channel ID ตัวเลข 10 หลัก
  LINE_CHANNEL_SECRET  - Channel secret 32 ตัวอักษร
  LINE_USER_ID         - userId ของตัวเอง (U...)
  IMAGE_URL            - HTTPS URL ของรูปที่ commit ขึ้นไปแล้ว
  FORTUNE_DATE         - YYYY-MM-DD (optional)
"""

import os
import sys

import requests

PUSH_ENDPOINT = "https://api.line.me/v2/bot/message/push"
TOKEN_ENDPOINT = "https://api.line.me/oauth2/v3/token"


def get_token() -> str:
    """แลก stateless channel access token จาก channel ID + secret (อายุ 15 นาที)"""
    r = requests.post(
        TOKEN_ENDPOINT,
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["LINE_CHANNEL_ID"],
            "client_secret": os.environ["LINE_CHANNEL_SECRET"],
        },
        timeout=30,
    )
    if not r.ok:
        print(f"ขอ token ไม่ได้ {r.status_code}: {r.text}", file=sys.stderr)
        r.raise_for_status()
    return r.json()["access_token"]


def main() -> int:
    token = get_token()
    user_id = os.environ["LINE_USER_ID"]
    image_url = os.environ["IMAGE_URL"]
    date = os.environ.get("FORTUNE_DATE", "")

    caption = (
        f"ちいかわ占い {date}\n"
        "ราศีกุมภ์ = みずがめ座 (อันดับ 1 อยู่บนสุด ไล่ลงไปถึงอันดับ 12)\n"
        "https://mezamashi.media/feature/chiikawa-fortune-daily"
    )

    body = {
        "to": user_id,
        "messages": [
            {"type": "text", "text": caption},
            {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url,
            },
        ],
    }

    r = requests.post(
        PUSH_ENDPOINT,
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if not r.ok:
        print(f"LINE push ล้มเหลว {r.status_code}: {r.text}", file=sys.stderr)
        return 1
    print("ส่งเข้าไลน์เรียบร้อย", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
