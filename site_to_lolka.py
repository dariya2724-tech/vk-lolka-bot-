import requests
import os
import json
import re
from datetime import datetime
from PIL import Image
from io import BytesIO

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

last = 0
if os.path.exists(FILE):
    with open(FILE, "r") as f:
        try:
            last = int(f.read().strip())
        except:
            pass

posts_to_check = posts[:10]
posts_to_check.reverse()

new_posts_sent = 0

for post in posts_to_check:
    pid = int(post.get("site_post_id"))
    
    if pid > last:
        print(f"New post found! ID: {pid}")
        
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
            "content": f"📌 Новая точка!\n🔎 {lake} | {fish}",
            "embeds": [{
                "title": "Открыть сайт",
                "url": "https://rr4farmtrof.com/pages/points.php",
                "description": desc,
                "color": 65280,
                "footer": {"text": f"ID: {pid}"},
                "timestamp": datetime.now().astimezone().isoformat()
            }]
        }

        imgs = post.get("photos", [])
        files = {}
        
        # Скачиваем и обрабатываем все картинки
        for i, p in enumerate(imgs):
            img_url = BASE_URL + p if p.startswith("/") else p
            try:
                # Скачиваем
                res_img = requests.get(img_url, timeout=10)
                img = Image.open(BytesIO(res_img.content)).convert('RGB')
                
                # Обрезаем нижние 15% (убираем красный баннер)
                w, h = img.size
                img = img.crop((0, 0, w, int(h * 0.85)))
                
                # Сохраняем в память
                output = BytesIO()
                img.save(output, format='JPEG', quality=95) # Высокое качество
                output.seek(0)
                
                files[f"files[{i}]"] = (f"img_{i}.jpg", output, "image/jpeg")
                
                # Первую картинку ставим в карточку
                if i == 0:
                    payload["embeds"][0]["image"] = {"url": f"attachment://img_{i}.jpg"}
            except Exception as e:
                print(f"Error processing image {img_url}: {e}")

        try:
            # Если есть картинки, отправляем как multipart/form-data
            if files:
                res = requests.post(WEBHOOK, data={"payload_json": json.dumps(payload)}, files=files, timeout=30)
            else:
                res = requests.post(WEBHOOK, json=payload, timeout=20)
                
            if res.status_code in (200, 204):
                print(f"Success! Card {pid} sent.")
                new_posts_sent += 1
                last = pid
            else:
                print("Lolka error:", res.status_code, res.text)
        except Exception as e:
            print("Network error:", e)

if new_posts_sent > 0:
    with open(FILE, "w") as f:
        f.write(str(last))
    print(f"Done! Sent {new_posts_sent} posts.")
else:
    print("No new posts.")
