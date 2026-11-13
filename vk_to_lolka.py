import requests
import os
import json
from datetime import datetime
 
# Берем секреты напрямую из GitHub
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
VK_SERVICE_TOKEN = os.environ["VK_SERVICE_TOKEN"]
VK_GROUP_DOMAIN = "rr4pepper"
LAST_POST_FILE = "last_post.txt"
 
print("Bot started. Checking VK...")
 
# 1. Get group ID
r_id = requests.get("https://api.vk.com/method/groups.getById", params={"group_id": VK_GROUP_DOMAIN, "access_token": VK_SERVICE_TOKEN, "v": "5.131"}).json()
if "response" not in r_id:
    print("Error ID group", r_id)
    exit()
group_id = r_id["response"][0]["id"]
 
# 2. Get posts
r_posts = requests.get("https://api.vk.com/method/wall.get", params={"owner_id": -group_id, "count": 5, "access_token": VK_SERVICE_TOKEN, "v": "5.131"}).json()
if "response" not in r_posts or not r_posts["response"]["items"]:
    print("Error posts", r_posts)
    exit()
 
posts = r_posts["response"]["items"]
posts.sort(key=lambda x: x["date"], reverse=True)
post = posts[0]
post_id = post["id"]
 
# 3. Check if already sent
last_sent_id = 0
if os.path.exists(LAST_POST_FILE):
    with open(LAST_POST_FILE, "r") as f:
        try:
            last_sent_id = int(f.read().strip())
        except:
            pass
 
if post_id <= last_sent_id:
    print(f"No new posts (last {post_id}, in memory {last_sent_id})")
    exit()
 
print(f"New post {post_id}! Processing...")
 
# 4. Collect images
image_urls = []
if "attachments" in post:
    for attach in post["attachments"]:
        if attach["type"] == "photo":
            sizes = attach["photo"]["sizes"]
            max_size = max(sizes, key=lambda x: x["width"])
            image_urls.append(max_size["url"])
 
text = post.get("text", "No text")
post_url = f"https://vk.com/wall-{post['owner_id']}_{post_id}"
 
# 5. Download images
files = {}
for i, url in enumerate(image_urls):
    try:
        res_img = requests.get(url, timeout=10)
        files[f"files[{i}]"] = (f"image_{i}.jpg", res_img.content, "image/jpeg")
    except Exception as e:
        print(f"Error downloading {url}: {e}")
 
# 6. Send text card
payload_text = {
    "content": f"New post in RR4 group!\n{post_url}",
    "embeds": [{
        "description": text,
        "color": 3447003,
        "footer": {"text": "Group rr4pepper"},
        "timestamp": datetime.now().astimezone().isoformat()
    }]
}
 
try:
    res = requests.post(WEBHOOK_URL, json=payload_text)
    if res.status_code not in (200, 204):
        print(f"Error Lolka (text): {res.status_code} - {res.text}")
        exit()
        
    # 7. Send images
    if files:
        print(f"Sending {len(files)} images...")
        payload_images = {}
        res_images = requests.post(WEBHOOK_URL, data={"payload_json": json.dumps(payload_images)}, files=files)
        
        if res_images.status_code not in (200, 204):
            print(f"Error sending images: {res_images.status_code} - {res_images.text}")
    
    print(f"Post #{post_id} sent successfully!")
    with open(LAST_POST_FILE, "w") as f:
        f.write(str(post_id))
        
except Exception as e:
    print(f"Network error: {e}")
