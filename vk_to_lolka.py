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

payload = {
    "content": f"🎣 **Новый пост в группе РР4!**\n{post_url}",
    "embeds": [{
        "description": text,
        "color": 3447003,
        "footer": {"text": "Группа rr4pepper"},
        "timestamp": datetime.now().astimezone().isoformat()
    }]
}

if image_urls:
    payload["embeds"][0]["image"] = {"url": image_urls[0]}

# 6. Отправляем в Lolka
try:
    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code in (200, 204):
        print(f"✅ Пост #{post_id} успешно отправлен!")
        with open(LAST_POST_FILE, "w") as f:
            f.write(str(post_id))
    else:
        print(f"❌ Ошибка Lolka: {res.status_code} — {res.text}")
except Exception as e:
    print(f"❌ Ошибка сети: {e}")
