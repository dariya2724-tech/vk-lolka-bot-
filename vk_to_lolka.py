import requests
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import json

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

def make_grid(image_urls):
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
            print(f"⚠️ Ошибка загрузки {url}: {e}")

    if not images:
        return None
    
    if len(images) == 1:
        output = BytesIO()
        images[0].save(output, format='JPEG', quality=85)
        output.seek(0)
        return output

    padding = 10
    col_width = 800
    total_width = col_width * 2 + padding * 3

    resized_images = []
    for img in images:
        ratio = col_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((col_width, new_height), Image.Resampling.LANCZOS)
        resized_images.append(img)

    rows = [resized_images[i:i+2] for i in range(0, len(resized_images), 2)]
    row_heights = []
    for row in rows:
        row_heights.append(max(img.height for img in row))

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
    return output
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

    payload = {
        "content": f"🎣 **Новый пост в группе РР4!**\n{post_url}",
        "embeds": [{
            "description": text,
            "color": 3447003,
            "footer": {"text": "Группа rr4pepper"},
            "timestamp": datetime.now().astimezone().isoformat()
        }]
    }

    files = {}
    if image_urls:
        if len(image_urls) == 1:
            payload["embeds"][0]["image"] = {"url": image_urls[0]}
        else:
            print(f"🖼️ Создаем сетку из {len(image_urls)} картинок...")
            grid_stream = make_grid(image_urls)
            if grid_stream:
                files = {"file": ("grid.jpg", grid_stream, "image/jpeg")}
                payload["embeds"][0]["image"] = {"url": "attachment://grid.jpg"}

    try:
        if files:
            res = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload)}, files=files)
        else:
            res = requests.post(WEBHOOK_URL, json=payload)
            
        if res.status_code in (200, 204):
            print(f"✅ Пост #{post_id} отправлен!")
            return True
        else:
            print(f"❌ Ошибка Lolka: {res.status_code} — {res.text}")
            return False
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
    main()
