import requests
import os
import re
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
        
        lake = latest_post.get("display_lake", "Неизвестно")
        point = latest_post.get("location", "Неизвестно")
        
        fish_name = "Неизвестная рыба"
        if latest_post.get("fish_list") and len(latest_post["fish_list"]) > 0:
            fish_name = latest_post["fish_list"][0].get("name", "Неизвестная рыба")
            
        # Берем текст автора и пытаемся вытащить оттуда приманку
        original_text = latest_post.get("post_text", "")
        bait = latest_post.get("bait", "")
        
        # Если в базе пусто, ищем в тексте слово "Приманка" или "Наживка"
        if not bait and original_text:
            match = re.search(r'(Приманка|Наживка|Блесна|Воблер)[:\s]+([^\n]+)', original_text, re.IGNORECASE)
            if match:
                bait = match.group(2).strip()
        
        if not bait:
            bait = "См. комментарий ниже"
            
        # Оставляем только комментарий игрока (если есть)
        comment_text = ""
        if original_text:
            if "Комментарий" in original_text:
                comment_text = original_text.split("Комментарий")[-1].strip()
            elif "Всем НХНЧ" in original_text:
                comment_text = original_text.split("Точка клева")[-1].strip()
        
        description = (
            f"📍 **Локация:** {lake}\n"
            f"🎯 **Точка:** {point}\n"
            f"🐟 **Рыба:** {fish_name}\n"
            f"🪱 **Приманка:** {bait}\n"
        )
        
        if comment_text:
            description += f"\n💬 **Комментарий:** {comment_text}"
        
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
                "color": 65280,
                "footer": {"text": f"ID: {post_id}"},
                "timestamp": datetime.now().astimezone().isoformat()
            }]
        }

        # Пытаемся обрезать картинку прямо через URL (убираем 15% снизу)
        if image_url:
            cropped_url = f"https://images.weserv.nl/?url={image_url}&w=800&h=500&fit=cover&a=top"
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
