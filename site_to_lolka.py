import requests
import os
import json
import re
from datetime import datetime

WEBHOOK = os.environ["WEBHOOK_URL"]
SITE_JSON = "https://rr4farmtrof.com/assets/data/points-preview.json"
BASE_URL = "https://rr4farmtrof.com"
FILE = "last_site_post.txt"

print("Bot started...")

try:
    r = requests.get(SITE_JSON, timeout=15)
    posts = r.json()
except Exception as e:
    print("Site error:", e)
    exit()

if not posts:
    print("No data.")
    exit()

post = posts[0]
pid = post.get("site_post_id")
last = 0

if os.path.exists(FILE):
    with open(FILE, "r") as f:
        try:
            last = int(f.read().strip())
        except:
            pass

if int(pid) <= last:
    print("No new posts.")
    exit()

lake = post.get("display_lake", "Unknown")
point = post.get("location", "Unknown")
fish = "Unknown"
if post.get("fish_list"):
    fish = post["fish_list"][0].get("name", "Unknown")

text = post.get("post_text", "")
bait = post.get("bait", "")
if not bait and text:
    m = re.search(r'(Приманка|Наживка)[:\s]+([^\n]+)', text, re.IGNORECASE)
    if m:
        bait = m.group(2).strip()
if not bait:
    bait = "См. комментарий"

desc = f"📍 Локация: {lake}\n🎯 Точка: {point}\n🐟 Рыба: {fish}\n🪱 Приманка: {bait}\n"
if text and "Комментарий" in text:
    desc += f"\n💬 {text.split('Комментарий')[-1].strip()}"

payload = {
    "content": "📌 Новая точка!",
    "embeds": [{
        "title": "Открыть сайт",
        "url": "https://rr4farmtrof.com/pages/points.php",
        "description": desc,
        "color": 65280,
        "footer": {"text": f"ID: {pid}"},
        "timestamp": datetime.now().astimezone().isoformat()
    }]
}

# Собираем все картинки
imgs = post.get("photos", [])
img_urls = []
for p in imgs:
    img_url = BASE_URL + p if p.startswith("/") else p
    img_urls.append(img_url)

# Первую картинку ставим в саму карточку
if img_urls:
    payload["embeds"][0]["image"] = {"url": img_urls[0]}

try:
    # 1. Отправляем карточку с текстом и первой картинкой
    res = requests.post(WEBHOOK, json=payload, timeout=20)
    
    if res.status_code in (200, 204):
        print(f"Success! Card {pid} sent.")
        
        # 2. Если есть другие картинки, отправляем их пачкой (сеткой)
        if len(img_urls) > 1:
            print(f"Sending {len(img_urls)-1} more images...")
            files = {}
            for i, url in enumerate(img_urls[1:]):
                files[f"files[{i}]"] = (f"img_{i}.jpg", requests.get(url).content, "image/jpeg")
            
            # Отправляем пустой payload, чтобы Lolka просто показала картинки сеткой
            res_imgs = requests.post(WEBHOOK, data={"payload_json": "{}"}, files=files, timeout=20)
            if res_imgs.status_code not in (200, 204):
                print("Error sending images grid:", res_imgs.status_code, res_imgs.text)
        
        # Сохраняем ID, чтобы не отправлять снова
        with open(FILE, "w") as f:
            f.write(str(pid))
    else:
        print("Lolka error:", res.status_code, res.text)
except Exception as e:
    print("Network error:", e)
