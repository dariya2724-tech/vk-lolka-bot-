import requests
import os
import json
from datetime import datetime

# Берем URL вебхука из секретов GitHub
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
SITE_URL = "https://rr4farmtrof.com/assets/data/points-preview.json"
SITE_BASE_URL = "https://rr4farmtrof.com"
LAST_SITE_POST_FILE = "last_site_post.txt"

def send_to_lolka(post):
    post_id = post.get("site_post_id")
    lake = post.get("display_lake", "Неизвестно")
    point = post.get("location", "Неизвестно")
    
    # Достаем рыбу (в JSON это список)
    fish_name = "Неизвестная рыба"
    if post.get("fish_list") and len(post["fish_list"]) > 0:
        fish_name = post["fish_list"][0].get("name", "Неизвестная рыба")
        
    bait = post.get("bait", "Не указана")
    
    # Формируем красивый текст
    description = (
        f"📍 **Локация:** {lake}\n"
        f"🎯 **Точка:** `{point}`\n"
        f"🐟 **Рыба:** {fish_name}\n"
        f"🪱 **Приманка:** {bait}\n"
    )
    
    # Ищем картинку
    image_url = None
    if post.get("photos") and len(post["photos"]) > 0:
        photo_path = post["photos"][0]
        # Если путь не начинается с http, добавляем базовый адрес
        if photo_path.startswith("/"):
            image_url = SITE_BASE_URL + photo_path
        else:
            image_url = photo_path

    payload = {
        "content": "📌 **Новая точка клёва на сайте!**",
        "embeds": [{
            "title": "Открыть страницу точек на сайте",
            "url": "https://rr4farmtrof.com/pages/points.php",
            "description": description,
            "color": 65280, # Зеленый цвет для сайта
            "footer": {"text": f"ID: {post_id}"},
            "timestamp": datetime.now().astimezone().isoformat()
        }]
    }

    if image_url:
        payload["embeds"][0]["image"] = {"url": image_url}

    try:
        res = requests.post(WEBHOOK_URL, json=payload)
        if res.status_code in (200, 204):
            print(f"✅ Точка с сайта #{post_id} отправлена!")
            return True
        else:
            print(f"❌ Ошибка Lolka: {res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка сети: {e}")
        return False

def main():
    print("🔍 Проверяем сайт...")
    if not WEBHOOK_URL:
        print("❌ Ошибка: Не задан секрет WEBHOOK_URL!")
        return

    try:
        # Скачиваем JSON с сайта
        response = requests.get(SITE_URL, timeout=10)
        response.raise_for_status()
        posts = response.json()
        
        if not posts:
            print("💤 Сайт вернул пустой список.")
            return

        # В файле посты идут от новых к старым, берем самый первый (последний добавленный)
        latest_post = posts[0]
        post_id = latest_post.get("site_post_id")
        
        last_sent_id = 0
        if os.path.exists(LAST_SITE_POST_FILE):
            with open(LAST_SITE_POST_FILE, "r") as f:
                try:
                    last_sent_id = int(f.read().strip())
                except ValueError:
                    pass

        # Проверяем, новый ли это ID
        if int(post_id) > last_sent_id:
            print(f"🆕 Новая точка! ID: {post_id}")
            if send_to_lolka(latest_post):
                # Сохраняем ID
                with open(LAST_SITE_POST_FILE, "w") as f:
                    f.write(str(post_id))
                print("💾 ID сохранен.")
        else:
            print(f"💤 Новых точек нет (последняя: {post_id}).")

    except Exception as e:
        print(f"❌ Ошибка при парсинге сайта: {e}")

if __name__ == "__main__":
    main()
