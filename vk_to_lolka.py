import requests
import os
from datetime import datetime

# Берем токены из переменных окружения (в GitHub они называются Secrets)
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
    else:
        print(f"❌ Ошибка ID группы: {response}")
        return None

def get_latest_post(group_id, token):
    url = "https://api.vk.com/method/wall.get"
    # Берем сразу 5 постов, чтобы точно захватить реальные новые, а не только закреп
    params = {"owner_id": -group_id, "count": 5, "access_token": token, "v": "5.131"}
    response = requests.get(url, params=params).json()
    
    if "response" in response and response["response"]["items"]:
        posts = response["response"]["items"]
        # Сортируем по дате (сначала самые новые). Закрепленный пост улетит в конец списка.
        posts.sort(key=lambda x: x["date"], reverse=True)
        return posts[0]
    else:
        print(f"❌ Ошибка постов: {response}")
        return None

def send_to_lolka(post):
    post_id = post["id"]
    text = post.get("text", "Без текста")
    if len(text) > 1000:
        text = text[:1000] + "..."
        
    post_url = f"https://vk.com/wall-{post['owner_id']}_{post_id}"
    image_url = None
    
    if "attachments" in post:
        for attach in post["attachments"]:
            if attach["type"] == "photo":
                sizes = attach["photo"]["sizes"]
                max_size = max(sizes, key=lambda x: x["width"])
                image_url = max_size["url"]
                break

    payload = {
        "content": "🎣 **Новый пост в группе РР4!**",
        "embeds": [{
            "title": "Нажмите, чтобы открыть пост ВК",
            "url": post_url,
            "description": text,
            "color": 3447003,
            "footer": {"text": "Группа rr4pepper"},
            "timestamp": datetime.now().astimezone().isoformat()
        }]
    }

    if image_url:
        payload["embeds"][0]["image"] = {"url": image_url}

    try:
        res = requests.post(WEBHOOK_URL, json=payload)
        if res.status_code in (200, 204):
            print(f"✅ Пост #{post_id} отправлен!")
            return True
        else:
            print(f"❌ Ошибка Lolka: {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка сети: {e}")
        return False

def main():
    print("🔍 Проверяем ВК...")
    if not WEBHOOK_URL or not VK_SERVICE_TOKEN:
        print("❌ Ошибка: Не заданы секреты WEBHOOK_URL или VK_SERVICE_TOKEN!")
        return

    group_id = get_group_id(VK_GROUP_DOMAIN, VK_SERVICE_TOKEN)
    if not group_id: return

    latest_post = get_latest_post(group_id, VK_SERVICE_TOKEN)
    if not latest_post: return

    post_id = latest_post["id"]
    last_sent_id = 0
    
    # Читаем ID последнего поста
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            try:
                last_sent_id = int(f.read().strip())
            except ValueError:
                pass

    # Сравниваем ID
    if post_id > last_sent_id:
        print(f"🆕 Новый пост! ID: {post_id}")
        if send_to_lolka(latest_post):
            # Записываем новый ID
            with open(LAST_POST_FILE, "w") as f:
                f.write(str(post_id))
            print("💾 ID сохранен.")
    else:
        print(f"💤 Новых постов нет (последний в ВК: {post_id}, в памяти: {last_sent_id}).")

if __name__ == "__main__":
    main()
