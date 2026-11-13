import os
os.system("pip install Pillow")
import requests, json, re, time
from datetime import datetime
from PIL import Image
from io import BytesIO
 
DEFAULT_WEBHOOK = os.environ["WEBHOOK_URL"]
WEBHOOKS = {"комариное": "https://lolka.app/api/webhooks/964904755430400/OTY0OTA0NzU1NDMwNDAw.oL-wEVATLHshhRR2fhfIPC_umnzrh18M1guytMfrFWE", "лосиное": "https://lolka.app/api/webhooks/964905542928384/OTY0OTA1NTQyOTI4Mzg0.4ZlzqvIllCbDSBubSe7C4n_w3cpyJlxQyMr6cpDHCA8", "вьюнок": "https://lolka.app/api/webhooks/964936074872832/OTY0OTM2MDc0ODcyODMy.OI6F38Cd9Bfg683iThF8fLnzC4omUAq4c5cG2jZv9WI", "старый острог": "https://lolka.app/api/webhooks/964936475346944/OTY0OTM2NDc1MzQ2OTQ0.7sbFZpLoVz-hufQCayfB297SUk1wfwC496Wju1WcH-Y", "белая": "https://lolka.app/api/webhooks/964936708851712/OTY0OTM2NzA4ODUxNzEy.vNVQ8t24gMdev78cQSpBQFynOU6WTAiE3kUsGplNn9s", "куори": "https://lolka.app/api/webhooks/964936851458048/OTY0OTM2ODUxNDU4MDQ4.e9jSQPRfj9pGVrFyPjfGPSrqGXQV8brW0iNPXTAn9F0", "медвежье": "https://lolka.app/api/webhooks/964937121908736/OTY0OTM3MTIxOTA4NzM2.VXO9GzIpTs0zn_J2-D9JRTdXEYSN1n-GeSSmy4RDWvI", "волхов": "https://lolka.app/api/webhooks/964937310423040/OTY0OTM3MzEwNDIzMDQw.gCvr31MnxrgG4oct-46loIBLjEvgBOG_rUoqIR0b86Q", "северский донец": "https://lolka.app/api/webhooks/964937585624064/OTY0OTM3NTg1NjI0MDY0.HK9fT78uKhUOiwLn8o98CufALqUGW4bslFvbL-HDqVE", "сура": "https://lolka.app/api/webhooks/964937847997440/OTY0OTM3ODQ3OTk3NDQw.GO6M6Ha3__a7SMEq4Le-XkykM-I9qwgTW-GicxlCN08", "ладожское озеро": "https://lolka.app/api/webhooks/964938041853952/OTY0OTM4MDQxODUzOTUy.tNBHyrlSSXDb44u8YhSQNdAlTL4JBoh_ISUn0xCLC7g", "янтарное": "https://lolka.app/api/webhooks/964938287072256/OTY0OTM4Mjg3MDcyMjU2.EAZgwX6LnriXCANHw4IW5tmBcweNbSg83xV0NL5l5J0", "ладожский архипелаг": "https://lolka.app/api/webhooks/964938627155968/OTY0OTM4NjI3MTU1OTY4.CUHpJRVYa7eTDEmR0_4hg4JWTHe8NfhKsyRwy8sf0lQ", "ахтуба": "https://lolka.app/api/webhooks/964938796681216/OTY0OTM4Nzk2NjgxMjE2.9h_1ItRMwx-irONQLggsvuOhAflDdonlvBZiee5qSRQ", "медное": "https://lolka.app/api/webhooks/964939040621568/OTY0OTM5MDQwNjIxNTY4.rNrMwsSmCZhfz3ueUvNLLNDAVnSQEPdTRJOB1Gh_aME", "нижняя тунгуска": "https://lolka.app/api/webhooks/964939297277952/OTY0OTM5Mjk3Mjc3OTUy.AZksNRLiiE1Dl0bAF4I37k5tylC4H2ALhg4iYVodyaU", "яма": "https://lolka.app/api/webhooks/964939546067968/OTY0OTM5NTQ2MDY3OTY4.f6FC0hYzJscf841e6H4NBuRUmwngR6R4Q8P3LvD_ny0", "норвежское море": "https://lolka.app/api/webhooks/964939724719104/OTY0OTM5NzI0NzE5MTA0.cWU7rJZ43brBzBLNy8QeTC8d5SHdtQfnQaz4bA8UrkA"}
SITE_JSON = "https://rr4farmtrof.com/assets/data/points-preview.json"
BASE_URL = "https://rr4farmtrof.com"
FILE = "last_site_post.txt"
 
print("Bot started...")
posts = None
for attempt in range(3):
    try:
        r = requests.get(SITE_JSON, timeout=15)
        posts = r.json()
        break
    except:
        time.sleep(3)
 
if not posts:
    exit()
 
last = 0
if os.path.exists(FILE):
    with open(FILE, "r") as f:
        try:
            last = int(f.read().strip())
        except:
            pass
 
post = posts[0]
pid = int(post.get("site_post_id"))
 
if pid > last:
    print("New post found! ID:", pid)
    with open(FILE, "w") as f:
        f.write(str(pid))
        
    lake = post.get("display_lake", "Unknown").lower()
    point = post.get("location", "Unknown")
    fish = "Unknown"
    if post.get("fish_list"):
        fish = post["fish_list"][0].get("name", "Unknown")
 
    target_webhook = DEFAULT_WEBHOOK
    color = 0x2F3136 # Темно-серый (без зеленой рамки)
    
    # Умный поиск канала
    found_channel = False
    for key, url in WEBHOOKS.items():
        if key in lake:
            target_webhook = url
            found_channel = True
            print(f"Matched lake '{key}'. Sending to specific channel.")
            break
    
    if not found_channel:
        print(f"No specific channel for '{lake}'. Sending to DEFAULT.")
 
    text = post.get("post_text", "")
    bait = post.get("bait", "")
    
    if not bait and text:
        m = re.search(r'(Приманка|Наживка)[:\s]+([^\n]+)', text, re.IGNORECASE)
        if m:
            bait = m.group(2).strip()
    if not bait:
        bait = "См. комментарий"
 
    # Формируем ПОЛНЫЙ текст без обрезки
    desc = f"📍 **Локация:** {lake.capitalize()}\n🎯 **Точка:** `{point}`\n🐟 **Рыба:** {fish}\n🪱 **Приманка:** {bait}\n"
    
    if text and "Комментарий" in text:
        comment = text.split('Комментарий')[-1].strip()
        desc += f"\n💬 *{comment}*"
 
    payload = {
        "content": f"📌 **Новая точка!**",
        "embeds": [{
            "title": f"🎣 {lake.capitalize()}",
            "url": "https://rr4farmtrof.com/pages/points.php",
            "description": desc,
            "color": color,
            "footer": {"text": f"ID: {pid} | RR4FARMTROF.COM"},
            "timestamp": datetime.now().astimezone().isoformat()
        }]
    }
 
    imgs = post.get("photos", [])
    files = {}
    
    for i, p in enumerate(imgs):
        img_url = BASE_URL + p if p.startswith("/") else p
        try:
            img_data = None
            for _ in range(2):
                try:
                    res_img = requests.get(img_url, timeout=5)
                    img_data = res_img.content
                    break
                except:
                    time.sleep(1)
            
            if not img_data:
                continue
                
            img = Image.open(BytesIO(img_data)).convert('RGB')
            w, h = img.size
            img = img.crop((0, 0, w, int(h * 0.90)))
            
            output = BytesIO()
            img.save(output, format='JPEG', quality=95)
            output.seek(0)
            
            files[f"files[{i}]"] = (f"img_{i}.jpg", output, "image/jpeg")
        except Exception as e:
            print("Error image:", e)
 
    try:
        # 1. Отправляем ТЕКСТ (карточку)
        res_text = requests.post(target_webhook, json=payload, timeout=20)
        
        if res_text.status_code not in (200, 204):
            print("LOLKA ERROR (text):", res_text.status_code, res_text.text)
        else:
            # 2. Отправляем КАРТИНКИ отдельным сообщением
            if files:
                time.sleep(2) # Пауза, чтобы текст встал первым
                res_imgs = requests.post(target_webhook, files=files, timeout=30)
                
                if res_imgs.status_code not in (200, 204):
                    print("LOLKA ERROR (images):", res_imgs.status_code, res_imgs.text)
            
            print("Success! Card sent:", pid)
            
    except Exception as e:
        print("Network error:", e)
 
else:
    print("No new posts.")
 
print("Done!")
