import requests
import os
import json
from datetime import datetime
from PIL import Image
from io import BytesIO

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
VK_SERVICE_TOKEN = os.environ.get("VK_SERVICE_TOKEN")
VK_GROUP_DOMAIN = "rr4pepper"
LAST_POST_FILE = "last_post.txt"

print("🔍 Бот запущен. Проверяем ВК...")
if not WEBHOOK_URL or not VK_SERVICE_TOKEN:
    print("❌ Ошибка: Нет секретов!")
    exit()

# 1. Получаем ID группы
r_id = requests.get("https://api.vk.com/method/groups.getById", params={"group_id": VK_GROUP_DOMAIN, "access_token": VK_SERVICE_TOKEN, "v": "5.131"}).json()
if "response" not in r_id:
    print("❌ Ошибка ID группы", r_id)
    exit()
group_id = r_id["response"][0]["id"]

# 2. Получаем посты
r_posts = requests.get("https://api.vk.com/method/wall.get", params={"owner_id": -group_id, "count": 5, "access_token": VK_SERVICE_TOKEN, "v": "5.131"}).json()
if "response" not in r_posts or not r_posts["response"]["items"]:
    print("❌ Ошибка получения постов", r_posts)
    exit()

# Берем самый свежий
posts = r_posts["response"]["items"]
posts.sort(key=lambda x: x["date"], reverse=True)
post = posts[0]
post_id = post["id"]

# 3. Проверяем, не отправляли ли уже
last_sent_id = 0
if os.path.exists(LAST_POST_FILE):
    with open(LAST_POST_FILE, "r") as f:
        try:
            last_sent_id = int(f.read().strip())
        except:
            pass

if post_id <= last_sent_id:
    print(f"💤 Новых постов нет (последний {post_id}, в памяти {last_sent_id})")
    exit()

print(f"🆕 Найден новый пост {post_id}! Обрабатываем...")

# 4. Собираем картинки
image_urls = []
if "attachments" in post:
    for attach in post["attachments"]:
        if attach["type"] == "photo":
            sizes = attach["photo"]["sizes"]
            max_size = max(sizes, key=lambda x: x["width"])
            image_urls.append(max_size["url"])

text = post.get("text", "Без текста")
post_url = f"https://vk.com/wall-{post['owner_id']}_{post_id}"

# 5. Склеиваем картинки (если их больше одной)
files = {}
main_image = None

if len(image_urls) == 1:
    main_image = image_urls[0]
elif len(image_urls) > 1:
    print(f"🖼️ Склеиваем {len(image_urls)} картинок в сетку...")
    images = []
    for url in image_urls:
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            img = Image.open(BytesIO(res.content))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            print(f"⚠️ Ошибка скачивания {url}: {e}")
    
    if len(images) > 1:
        padding = 10
        col_width = 800
        total_width = col_width * 2 + padding * 3
        resized = []
        for img in images:
            ratio = col_width / img.width
            new_height = int(img.height * ratio)
            resized.append(img.resize((col_width, new_height), Image.Resampling.LANCZOS))
        
        rows = [resized[i:i+2] for i in range(0, len(resized), 2)]
        row_heights = [max(img.height for img in row) for row in rows]
        total_height = sum(row_heights) + padding * (len(rows) + 1)
        
        grid = Image.new('RGB', (total_width, total_height), (35, 39, 42))
        y_offset = padding
        for i, row in enumerate(rows):
            x_offset = padding
            for img in row:
                grid.paste(img, (x_offset, y_offset))
                x_offset += col_width + padding
            y_offset += row_heights[i] + padding
            
        output = BytesIO()
        grid.save(output, format='JPEG', quality=90)
        output.seek(0)
        files = {"file": ("grid.jpg", output, "image/jpeg")}
        main_image = "attachment://grid.jpg"
    elif len(images) == 1:
        main_image = image_urls[0]

# 6. Отправляем в Lolka
payload = {
    "content": f"🎣 **Новый пост в группе РР4!**\n{post_url}",
    "embeds": [{
        "description": text,
        "color": 3447003,
        "footer": {"text": "Группа rr4pepper"},
        "timestamp": datetime.now().astimezone().isoformat()
    }]
}

if main_image:
    payload[


"][0]["image"] = {"url": main_image}

try:
    if files:
        res = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files)
    else:
        res = requests.post(WEBHOOK_URL, json=payload)
        
    if res.status_code in (200, 204):
        print(f"✅ Пост #{post_id} успешно отправлен!")
        with open(LAST_POST_FILE, "w") as f:
            f.write(str(post_id))
    else:
        print(f"❌ Ошибка Lolka: {res.status_code} — {res.text}")
except Exception as e:
    print(f"❌ Ошибка сети: {e}")"embeds
