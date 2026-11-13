import requests
import os
from datetime import datetime

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
VK_SERVICE_TOKEN = os.environ.get("VK_SERVICE_TOKEN")
VK_GROUP_DOMAIN = "rr4pepper"

LAST_POST_FILE = "last_post.txt"

def get_group_id(domain, token):
    url = "https://api.vk.com/method/groups.getById"
    params = {"group_id": domain, "access_token": token, "v": "5.131"}
    response = requests.get(url, params=params).json()
    if "response" in response:
        return response["response"][0]["id"]
    return None

def get_latest_post(group_id, token):
    url = "https://api.vk.com/method/wall.get"
    params = {"owner_id": -group_id, "count": 5, "access_token": token, "v": "5.131"}
    response = requests.get(url, params=params).json()
    
    if "response" in response and response["response"]["items"]:
        posts = response["response"]["items"]
        posts.sort(key=lambda x: x["date"], reverse=True)
        return posts[0]
    return None

def send_to_lolka(post):
    post_id = post["id"]
    text = post.get("text", "Без текста")
    
    image_urls = []
    if "attachments" in post:
        for attach in post["attachments"]:
            if attach["type"] == "photo":
                sizes = attach["photo"]["sizes"]
                max_size = max(sizes, key=lambda x: x["width"])
                image_urls.append(max_size["url"])

    post_url = f"https://vk.com/wall-{post['owner_id']}_{post_id}"

    # 1. Отправляем ТЕКСТОВУЮ карточку (с первой картинкой как обложкой)
    payload_text = {
        "content": f"🎣 **Новый пост в группе РР4!**\n{post_url}",
        "embeds": [{
            "description": text,
            "color": 3447003,
            "footer": {"text": "Группа rr4pepper"},
            "timestamp": datetime.now().astimezone().isoformat()
        }]
    }

    if image_urls:
        payload_text["embeds"][0]["image"] = {"url": image_urls[0]}

    try:
        # Отправляем карточку с текстом
        res = requests.post(WEBHOOK_URL, json=payload_text)
        if res.status_code not in (200, 204):
            print(f"❌ Ошибка Lolka (текст): {res.status_code} — {res.text}")
            return False
            
        # 2. Если картинок больше одной, отправляем их сеткой (альбомом) следом
        if len(image_urls) > 1:
            print("🖼️ Отправляем остальные картинки сеткой...")
            # Чтобы картинки встали в сетку, отправляем их пачкой
            payload_images = {
                "attachments": [{"url": url} for url in image_urls[1:]]
            }
            res_images = requests.post(WEBHOOK_URL, json=payload_images)
            if res_images.status_code not in (200, 204):
                print(f"⚠️ Не удалось отправить сетку картинок (возможно, Lolka не поддерживает).")
        
        print(f"✅ Пост #{post_id} отправлен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сети: {e}")
        return False

def main():
    print("🔍 Проверяем ВК...")
    if not WEBHOOK_URL or not VK_SERVICE_TOKEN:
        print("❌ Ошибка: Не заданы секреты!")
        return

    group_id = get_group_id(VK_GROUP_DOMAIN, VK_SERVICE_TOKEN)
    if not group_id: return

    latest_post = get_latest_post(group_id, VK_SERVICE_TOKEN)
    if not latest_post: return

    post_id = latest_post["id"]
    last_sent_id = 0
    
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            try:
                last_sent_id = int(f.read().strip())
            except ValueError:
                pass

    if post_id > last_sent_id:
        print(f"🆕 Новый пост! ID: {post_id}")
        if send_to_lolka(latest_post):
            with open(LAST_POST_FILE, "w") as f:
                f.write(str(post_id))
            print("💾 ID сохранен.")
    else:
        print(f"💤 Новых постов нет (последний в ВК: {post_id}, в памяти: {last_sent_id}).")

if __name__ == "__main__":
