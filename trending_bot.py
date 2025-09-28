#!/usr/bin/env python3
"""
GitHub Trending → DeepSeek Caption → Telegram Bot
------------------------------------------------
Repository:
https://github.com/TBmohammad/Github_FA
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ---------- Load .env ----------
def load_env_file(path=None):
    if path is None:
        path = Path(__file__).parent / ".env" 
    if not os.path.exists(path):
        print(f"[WARN] .env file not found at: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                print(f"[SKIP] invalid line in .env: {line}")
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            os.environ[key] = value
            print(f"[ENV] {key} loaded")

load_env_file()

# ---------- Config ----------
BOT_TOKEN    = os.getenv("TG_BOT_TOKEN")
CHANNEL_ID   = os.getenv("TG_CHANNEL_ID")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

print("DEBUG BOT_TOKEN   =", BOT_TOKEN)
print("DEBUG CHANNEL_ID  =", CHANNEL_ID)
print("DEBUG DEEPSEEK_KEY=", DEEPSEEK_KEY)

SEEN_FILE    = Path(__file__).parent / "link.txt"
TRENDING_URL = "https://github-trending-api.de.a9sapp.eu/repositories?since=daily"
DEESEEK_URL  = "https://api.deepseek.com/chat/completions"


# ---------- Utilities ----------
def http_json_get(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status >= 400:
                return None
            return json.loads(res.read().decode("utf-8"))
    except Exception:
        return None


def http_json_post(url, payload, headers=None, timeout=30):
    try:
        data = json.dumps(payload).encode("utf-8")
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status >= 400:
                return None
            return json.loads(res.read().decode("utf-8"))
    except Exception:
        return None


def read_seen(file: Path):
    if not file.exists():
        return []
    return [x.strip() for x in file.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_seen(file: Path, link: str):
    with open(file, "a", encoding="utf-8") as f:
        f.write(link + "\n")


def make_github_link(name: str) -> str:
    s = name.strip()
    if not s:
        return "https://github.com/"
    if s.startswith("http://") or s.startswith("https://"):
        parts = s.split("/")
        seg = [p for p in parts if p]
        if len(seg) >= 2:
            return f"https://github.com/{seg[-2]}/{seg[-1]}"
        elif len(seg) == 1:
            return f"https://github.com/{seg[-1]}"
        else:
            return "https://github.com/"
    return "https://github.com/" + s.strip("/")


# ---------- Core logic ----------
def pick_trending(data, seen):
    if not data:
        return None
    hour = datetime.now().hour
    h = (hour - 1) if hour <= 16 else (hour - 17)
    count = len(data)
    for i in range(16):
        x = data[(h + i) % count]
        author = x.get("author", "")
        name   = x.get("name", "")
        n      = f"{author}/{name}".strip("/")
        l      = x.get("url") or x.get("href", "")
        p      = x.get("avatar", "")
        if l and l not in seen:
            return n, l, p
    return None


def ds_tool_intro(name: str, api_key: str) -> str:
    if not name.strip():
        return "معرفی ابزار جدید:\nتوضیحات:\nدسته بندی:\nلینک گیت هاب:"

    system = (
        "فقط و فقط در این قالب خروجی بده و هیچ چیز دیگری اضافه نکن:\n"
        "معرفی ابزار جدید: (اسم)\n"
        "توضیحات:\n"
        "دسته بندی:\n"
        "قوانین:\n"
        "1) توضیحات: یک جملهٔ کوتاه و کاربردی (حداکثر 40 کلمه).\n"
        "2) دسته بندی: آزاد است و بر اساس ماهیت ابزار تعیین شود.\n"
        "3) هیچ چیز اضافه (ایموجی/متن اضافی/پیشوند/پسوند) ننویس."
    )

    user = f"نام ابزار: {name}\nهمین قالب را پر کن."

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 70,
        "stream": False,
    }

    resp = http_json_post(
        DEESEEK_URL, payload, {"Authorization": f"Bearer {api_key}"}
    )

    text = ""
    try:
        text = resp["choices"][0]["message"]["content"]
    except Exception:
        pass

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    keys = ["معرفی ابزار جدید:", "توضیحات:", "دسته بندی:", "لینک گیت هاب:"]
    clean = []
    for k in keys:
        found = next((ln for ln in lines if ln.startswith(k)), None)
        clean.append(found or (k + " "))

    clean[3] = f"لینک گیت هاب:\n{make_github_link(name)}\n🆔 {CHANNEL_ID}"
    return "\n".join(clean)


def telegram_send(bot_token, chat_id, caption, photo_url=None):
    import urllib.parse
    try:
        if photo_url:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption}
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": caption}

        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status < 400
    except Exception:
        return False


# ---------- Main ----------
def main():
    if not BOT_TOKEN or not CHANNEL_ID or not DEEPSEEK_KEY:
        print("Missing env vars: TG_BOT_TOKEN, TG_CHANNEL_ID, DEEPSEEK_API_KEY", flush=True)
        return

    data = http_json_get(TRENDING_URL)
    if not data:
        print("Trending API failed or returned empty", flush=True)
        return

    seen = read_seen(SEEN_FILE)
    pick = pick_trending(data, seen)
    if not pick:
        print("No new item to post.", flush=True)
        return

    repo_name, link, photo = pick

    caption = ds_tool_intro(repo_name, DEEPSEEK_KEY)

    ok = telegram_send(BOT_TOKEN, CHANNEL_ID, caption, photo or None)
    if not ok:
        ok = telegram_send(BOT_TOKEN, CHANNEL_ID, caption, None)

    if ok:
        append_seen(SEEN_FILE, link)
        print(f"Posted: {repo_name}", flush=True)
    else:
        print("Telegram send failed", flush=True)


if __name__ == "__main__":
    main()
