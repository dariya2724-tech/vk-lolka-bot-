import requests
import os
import json
from datetime import datetime
from PIL import Image
from io import BytesIO
import re
 
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
SITE_URL = "https://rr4farmtrof.com/assets/data/points-preview.json"
SITE_BASE_URL = "https://rr4farmtrof.com"
LAST_SITE_POST_FILE = "last_site_post.txt"
 
print("Bot started. Checking site...")
 
# 1. Получаем данные с сайта
try:
    response = requests.get(SITE_URL, timeout=15)
    response.raise_for_status()
    posts = response.json()
except Exception as e:
    print(f"Error loading site: {e}")
    exit()
 
if not posts:
    print("Site returned empty list.")
    exit()
 
latest_post = posts[0]
post_id = latest_post.get("site_post_id")
 
last_sent_id = 0
if os.path.exists(LAST_SITE_POST_FILE):
    with open(LAST_SITE_POST_FILE, "r") as f:
        try:
            last_sent_id = int(f.read().strip())
        except:
            pass
 
if int(post_id) <= last_sent_id:
    print(f"No new site posts (last {post_id}).")
    exit()
 
print(f"New site post! ID: {post_id}")
 
# 2. Обрабатываем данные
lake = latest_post.get("display_lake", "Неизвестно")
point = latest_post.get("location", "Неизвестно")
 
fish_name = "Неизвестная рыба"
if latest_post.get("fish_list") and len(latest_post["fish_list"]) > 0:
    fish_name = latest_post["fish_list"][0].get("name", "Неизвестная рыба")
 
original_text = latest_post.get("post_text", "")
bait = latest_post.get("bait", "")
 
if not bait and original_text:
    match = re.search(r'(Приманка|Наживка|Блесна|Воблер)[:\s]+([^\n]+)', original_text, re.IGNORECASE)
    if match:
        bait = match.group(2).strip()
 
if not bait:
    bait = "См. комментарий ниже"
 
comment_text = ""
if original_text and "Комментарий" in original_text:
    comment_text = original_text.split("Комментарий")[-1].strip()
 
description = f"📍 **Локация:** {lake}\n🎯 **Точка:** {point}\n🐟 **Рыба:** {fish_name}\n🪱 **Приманка:** {bait}\n"
if comment_text:
    description += f"\n💬 **Комментарий:** {comment_text}"
 
# 3. Собираем картинки
image_urls = []
if latest_post.get("photos"):
    for photo_path in latest_post["photos"]:
        if photo_path.startswith("/"):
            image_urls.append(SITE_BASE_URL + photo_path)
        else:
            image_urls.append(photo_path)
 
payload = {
    "content": "📌 **Новая точка клёва на сайте!**",
    "embeds": [{
        "title": "Открыть страницу точек на сайте",
        "url": "https://rr4farmtrof.com/pages/points.php",
        "description": description,
        "color": 65280,
        "footer": {"text": f"ID: {post_id}"},
        "timestamp": datetime.now().astimezone().isoformat()
    }]
}
 
files = {}
 
# 4. Скачиваем и обрезаем картинки
for i, url in enumerate(image_urls):
    try:
        res_img = requests.get(url, timeout=5)
        img = Image.open(BytesIO(res_img.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        width, height = img.size
        crop_height = int(height * 0.85)
        cropped_img = img.crop((0, 0, width, crop_height))
        
        output = BytesIO()
        cropped_img.save(output, format='JPEG', quality=90)
        output.seek(0)
        
        files[f"files[{i}]"] = (f"image_{i}.jpg", output, "image/jpeg")
        
        if i == 0:
            payload["embeds"][0]["image"] = {"url": f"attachment://image_{i}.jpg"}
    except Exception as e:
        print(f"Skip image {url}: {e}")
 
# 5. Отправляем в Lolka
try:
    if files:
        res = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files, timeout=20)
    else:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=20)
        
    if res.status_code in (200, 204):
        print(f"Site post #{post_id} sent!")
        with open(LAST_SITE_POST_FILE, "w") as f:
            f.write(str(post_id))
    else:
        print(f"Error Lolka: {res.status_code} - {res.text}")
except Exception as e:
    print(f"Network error: {e}")
