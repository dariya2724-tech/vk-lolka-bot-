import requests
import os
from datetime import datetime

WEBHOOK_URL = os.environ["WEBHOOK_URL"]
SITE_URL = "https://rr4farmtrof.com/assets/data/points-preview.json"
SITE_BASE_URL = "https://rr4farmtrof.com"
LAST_SITE_POST_FILE = "last_site_post.txt"

print("Bot started. Checking site...")

try:
    response = requests.get(SITE_URL, timeout=15)
    response.raise_for_status()
    posts = response.json()
    
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

    if int(post_id) > last_sent_id:
        print(f"New site post! ID: {post_id}")
        
        # Берем данные из поста
        lake = latest_post.get("display_lake", "Неизвестно")
        point = latest_post.get("location", "Неизвестно")
        
        fish_name = "Неизвестная рыба"
        if latest_post.get("fish_list") and len(latest_post["fish_list"]) > 0:
            fish_name = latest_post["fish_list"][0].get("name", "Неизвестная рыба")
            
        # Ищем приманку во всех возможных полях, которые отдает сайт
        bait = latest_post.get("bait", "")
        if not bait:
            bait = latest_post.get("lure", "")
        if not bait:
            bait = latest_post.get("bait_name", "")
        if not bait:
            bait = "Не указана"
        
        description = (
            f"📍 **Локация:** {lake}\n"
            f"🎯 **Точка:** {point}\n"
            f"🐟 **Рыба:** {fish_name}\n"
            f"🪱 **Приманка:** {bait}\n"
        )
        
        image_url = None
        if latest_post.get("photos") and len(latest_post["photos"]) > 0:
            photo_path = latest_post["photos"][0]
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
                "color": 65280, # Зеленый цвет
                "footer": {"text": f"ID: {post_id}"},
                "timestamp": datetime.now().astimezone().isoformat()
            }]
        }

        if image_url:
            # Используем сервис wsrv.nl для обрезки нижней части (убираем красный баннер)
            # 0,0,100,85 означает: обрезать снизу 15% картинки
            cropped_url = f"https://wsrv.nl/?url={image_url}&crop=0,0,100,85"
            payload["embeds"][0]["image"] = {"url": cropped_url}

        res = requests.post(WEBHOOK_URL, json=payload)
        if res.status_code in (200, 204):
            print(f"Site post #{post_id} sent!")
            with open(LAST_SITE_POST_FILE, "w") as f:
                f.write(str(post_id))
        else:
            print(f"Error Lolka: {res.status_code} - {res.text}")
    else:
        print(f"No new site posts (last {post_id}).")

except Exception as e:
    print(f"Error: {e}")
