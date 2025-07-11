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

# Thiết lập biến môi trường từ secret GOOGLE_CREDS
creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
with open("credentials.json", "w") as f:
    json.dump(creds_dict, f)

# Cấu hình Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet_name = "doantruongcddaklak"

# Lấy tháng/năm hiện tại
now = datetime.datetime.now()
month_year = now.strftime("%m-%Y")

# Mở hoặc tạo Google Sheet
spreadsheet = client.open(sheet_name)
try:
    worksheet = spreadsheet.worksheet(month_year)
except:
    worksheet = spreadsheet.add_worksheet(title=month_year, rows="1000", cols="10")
    worksheet.append_row(["STT", "Ngày đăng", "Người đăng", "Chủ đề", "Tóm tắt nội dung"])

# Thiết lập Selenium headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

# Truy cập fanpage Facebook
url = "https://www.facebook.com/doantruongcddaklak"
driver.get(url)
time.sleep(5)

# Cuộn trang để lấy thêm bài viết (tùy chỉnh số lần cuộn)
SCROLL_TIMES = 3
for _ in range(SCROLL_TIMES):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

# Thu thập bài viết
posts = driver.find_elements(By.XPATH, '//div[@data-ad-preview="message"]')
dates = driver.find_elements(By.XPATH, '//a[contains(@href,"/doantruongcddaklak/posts/")]')

for i in range(min(len(posts), len(dates))):
    content = posts[i].text.strip().replace("\n", " ").replace("\r", " ")
    if not content:
        continue
    date_text = dates[i].get_attribute("aria-label") or "Không rõ ngày"
    short_content = content[:100] + "..." if len(content) > 100 else content
    worksheet.append_row([i+1, date_text, "doantruongcddaklak", "Không xác định", short_content])

driver.quit()
print("✅ Đã ghi dữ liệu vào Google Sheets")
