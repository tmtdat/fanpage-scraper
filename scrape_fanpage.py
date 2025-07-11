import os
import json
import datetime
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import hashlib

# Thiết lập biến môi trường từ secret GOOGLE_CREDS
creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
with open("credentials.json", "w") as f:
    json.dump(creds_dict, f)

# Cấu hình Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet_name = "doantruongcddaklak"
spreadsheet = client.open(sheet_name)

# Selenium headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

# Truy cập fanpage
url = "https://www.facebook.com/doantruongcddaklak"
driver.get(url)
time.sleep(5)

# Cuộn để tải nhiều bài viết hơn
SCROLL_TIMES = 20
for _ in range(SCROLL_TIMES):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

# Lấy bài viết & ngày đăng
posts = driver.find_elements(By.XPATH, '//div[@data-ad-preview="message"]')
links = driver.find_elements(By.XPATH, '//a[contains(@href,"/doantruongcddaklak/posts/")]')

# Tạo bộ nhớ bài đã ghi để tránh trùng
recorded_links = {}

# Duyệt từng bài
for i in range(min(len(posts), len(links))):
    content = posts[i].text.strip().replace("\n", " ").replace("\r", " ")
    if not content:
        continue

    link = links[i].get_attribute("href")
    date_attr = links[i].get_attribute("aria-label") or ""
    try:
        post_date = datetime.datetime.strptime(date_attr.split("lúc")[0].strip(), "%d tháng %m, %Y")
    except:
        continue

    year_sheet = str(post_date.year)

    # Tạo sheet theo năm nếu chưa có
    try:
        worksheet = spreadsheet.worksheet(year_sheet)
    except:
        worksheet = spreadsheet.add_worksheet(title=year_sheet, rows="1000", cols="10")
        worksheet.append_row(["STT", "Ngày đăng", "Người đăng", "Chủ đề", "Tóm tắt nội dung", "Link bài viết"])

    # Tải toàn bộ link đã lưu để kiểm tra trùng
    if year_sheet not in recorded_links:
        data = worksheet.get_all_records()
        recorded_links[year_sheet] = set(row["Link bài viết"] for row in data)

    if link in recorded_links[year_sheet]:
        continue

    summary = content[:15] + "..." if len(content) > 15 else content
    topic = "Sự kiện" if "hội" in content.lower() else "Khác"  # Tạm dùng logic đơn giản, có thể thay bằng AI sau

    worksheet.append_row([
        len(recorded_links[year_sheet]) + 1,
        post_date.strftime("%d-%m-%Y"),
        "doantruongcddaklak",
        topic,
        summary,
        link
    ])

    recorded_links[year_sheet].add(link)

driver.quit()
print("✅ Đã ghi toàn bộ dữ liệu vào Google Sheets theo từng năm.")
