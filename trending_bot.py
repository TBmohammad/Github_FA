#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Trending → DeepSeek → Telegram
------------------------------------------------
Repository:
https://github.com/TBmohammad/Github_FA
"""

import os
import re
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------- .env Loader ----------
def load_env(path=None):
    if path is None:
        path = Path(__file__).parent / ".env"
    if not os.path.exists(path):
        print("[⚠️] .env file not found, using defaults.")
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ[key] = val

load_env()

# ---------- Config ----------
BOT_TOKEN    = os.getenv("TG_BOT_TOKEN", "")
CHANNEL_ID   = os.getenv("TG_CHANNEL_ID", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
MAX_POSTS    = int(os.getenv("MAX_POSTS", 1))
TRENDING_URL = os.getenv("TRENDING_URL", "https://github.com/trending")
DEESEEK_URL  = "https://api.deepseek.com/chat/completions"
SEEN_FILE    = Path(__file__).parent / "link.txt"

# ---------- Logging ----------
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ---------- HTTP Utils ----------
def http_get(url, headers=None, timeout=20):
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status >= 400:
                return None
            return res.read().decode("utf-8")
    except Exception as e:
        log(f"⚠️ GET failed: {e}")
        return None


def http_post_json(url, payload, headers=None, timeout=30):
    try:
        data = json.dumps(payload).encode("utf-8")
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, data=data, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status >= 400:
                return None
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        log(f"⚠️ POST failed: {e}")
        return None


# ---------- File Utils ----------
def read_seen(file: Path):
    return file.read_text(encoding="utf-8").splitlines() if file.exists() else []


def append_seen(file: Path, url: str):
    with open(file, "a", encoding="utf-8") as f:
        f.write(url.strip() + "\n")


# ---------- GitHub Trending ----------
def get_trending():
    log("🌐 Fetching GitHub trending...")
    html = http_get(TRENDING_URL)
    if not html:
        log("❌ Failed to fetch trending page.")
        return []

    html = re.sub(r"\s+", " ", html)
    repos = re.findall(r'<a[^>]+href="(/[^/]+/[^/"]+)"[^>]*data-view-component="true"', html)
    results = []
    for path in repos:
        if not re.match(r"^/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", path):
            continue
        author, name = path.strip("/").split("/", 1)
        results.append({
            "author": author,
            "name": name,
            "url": f"https://github.com{path}"
        })
    log(f"✅ Found {len(results)} trending repos.")
    return results[:15]


# ---------- Smart Image Finder ----------
def find_image(repo_url, author):
    log(f"🖼 Finding image for {repo_url}")
    html = http_get(repo_url)
    if not html:
        return f"https://github.com/{author}.png"

    imgs = re.findall(r'<img[^>]+src="([^"]+\.(?:png|jpg|jpeg|webp|gif))"', html, flags=re.I)
    for img in imgs:
        if img.startswith("/"):
            img = "https://github.com" + img
        if img.startswith("http"):
            return img
    return f"https://github.com/{author}.png"


# ---------- DeepSeek Caption ----------
def make_caption(name):
    repo_name = name.split("/")[-1]

    system_prompt = (
        "در قالب زیر پاسخ بده و هیچ متن اضافی ننویس:\n"
        "معرفی ابزار جدید: <نام ابزار>\n"
        "توضیحات: <توضیح کوتاه فارسی>\n"
        "دسته بندی: <یکی از موارد: توسعه نرم‌افزار، هوش مصنوعی، DevOps، فریم‌ورک، کتابخانه، اپلیکیشن، سایر>"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"نام ابزار: {repo_name}"}
        ],
        "temperature": 0.8,
        "max_tokens": 150
    }

    res = http_post_json(DEESEEK_URL, payload, {"Authorization": f"Bearer {DEEPSEEK_KEY}"})
    if not res:
        return fallback_caption(repo_name)

    try:
        txt = res["choices"][0]["message"]["content"].strip()
    except Exception:
        txt = ""

    if not txt or "توضیحات:" not in txt:
        txt = fallback_caption(repo_name)

    txt = re.sub(r"^معرفی ابزار جدید[^\n]*\n?", "", txt, flags=re.M)
    return f"معرفی ابزار جدید: {repo_name}\n{txt}\n🔗 https://github.com/{name}\n🆔 {CHANNEL_ID}"


def fallback_caption(repo_name):
    return (
        f"معرفی ابزار جدید: {repo_name}\n"
        f"توضیحات: اطلاعاتی در دسترس نیست.\n"
        f"دسته بندی: نامشخص\n"
        f"🔗 https://github.com/{repo_name}\n🆔 {CHANNEL_ID}"
    )


# ---------- Telegram ----------
def telegram_send(caption, photo=None):
    import urllib.parse
    try:
        if photo:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            data = urllib.parse.urlencode({"chat_id": CHANNEL_ID, "photo": photo, "caption": caption}).encode()
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": CHANNEL_ID, "text": caption}).encode()

        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.status < 400
    except Exception as e:
        log(f"⚠️ Telegram error: {e}")
        return False


# ---------- Main ----------
def main():
    log("🚀 Script started")
    repos = get_trending()
    if not repos:
        return

    seen = read_seen(SEEN_FILE)
    count = 0
    for repo in repos:
        if repo["url"] not in seen:
            name = f"{repo['author']}/{repo['name']}"
            log(f"📦 New repo detected: {name}")
            caption = make_caption(name)
            image = find_image(repo["url"], repo["author"])

            ok = telegram_send(caption, image)
            if not ok:
                ok = telegram_send(caption)

            if ok:
                append_seen(SEEN_FILE, repo["url"])
                log(f"✅ Posted successfully: {name}")
            else:
                log(f"❌ Telegram failed for {name}")

            count += 1
            if count >= MAX_POSTS:
                break
            time.sleep(5)

    log(f"🏁 Script finished ({count} posts).")


if __name__ == "__main__":
    main()
