import requests
import os
import json
from datetime import datetime
 
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
 
# 4. Собираем ссылки на картинки
image_urls = []
if "attachments" in post:
    for attach in post["attachments"]:
        if attach["type"] == "photo":
            sizes = attach["photo"]["sizes"]
            max_size = max(sizes, key=lambda x: x["width"])
            image_urls.append(max_size["url"])
 
text = post.get("text", "Без текста")
post_url = f"https://vk.com/wall-{post['owner_id']}_{post_id}"
 
# 5. Скачиваем все картинки в память
files = {}
for i, url in enumerate(image_urls):
    try:
        res_img = requests.get(url, timeout=10)
        files[f"files[{i}]"] = (f"image_{i}.jpg", res_img.content, "image/jpeg")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки картинки {url}: {e}")
 
# 6. Отправляем ТЕКСТ (карточку)
payload_text = {
    "content": f"🎣 **Новый пост в группе РР4!**\n{post_url}",
    "embeds": [{
        "description": text,
        "color": 3447003,
        "footer": {"text": "Группа rr4pepper"},
        "timestamp": datetime.now().astimezone().isoformat()
    }]
}
 
try:
    # Отправляем карточку с текстом
    res = requests.post(WEBHOOK_URL, json=payload_text)
    if res.status_code not in (200, 204):
        print(f"❌ Ошибка Lolka (текст): {res.status_code} — {res.text}")
        exit()
        
    # Отправляем картинки сеткой (если они есть)
    if files:
        print(f"🖼️ Отправляем {len(files)} картинок сеткой...")
        payload_images = {} # Пустой пейлоад, чтобы Lolka не ругалась
        res_images = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload_images)}, files=files)
        
        if res_images.status_code not in (200, 204):
            print(f"⚠️ Не удалось отправить сетку картинок (возможно, Lolka не поддерживает).")
    
    print(f"✅ Пост #{post_id} успешно отправлен!")
    with open(LAST_POST_FILE, "w") as f:
        f.write(str(post_id))
        
except Exception as e:
    print(f"❌ Ошибка сети: {e}")
