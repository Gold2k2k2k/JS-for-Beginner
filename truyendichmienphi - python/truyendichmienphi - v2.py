import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\DELL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
import io
import time
import re
import os

class EbookScraper:
    def __init__(self, headless=True):
        """
        Khởi tạo scraper với Selenium
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def ocr_full_page(self, url):
        """
        OCR toàn bộ trang web
        """
        print(f"Đang truy cập: {url}")
        self.driver.get(url)
        time.sleep(3)  # Đợi trang load đầy đủ
        
        content_parts = []
        
        try:
            # Tìm phần tử chứa nội dung chính (thường là .chapter-content, .content, etc.)
            # Thử nhiều selector khác nhau
            content_selectors = [
                ".chapter-content",
                ".content",
                "#chapter-content",
                ".reading-content",
                ".story-detail-content",
                "article",
                ".post-content"
            ]
            
            content_element = None
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        content_element = elements[0]
                        print(f"Tìm thấy nội dung với selector: {selector}")
                        break
                except:
                    continue
            
            if not content_element:
                # Nếu không tìm thấy, lấy toàn bộ body
                print("Không tìm thấy selector cụ thể, sẽ OCR toàn bộ trang")
                content_element = self.driver.find_element(By.TAG_NAME, "body")
            
            # Scroll để đảm bảo tất cả nội dung được load
            self.driver.execute_script("arguments[0].scrollIntoView();", content_element)
            time.sleep(1)
            
            # Lấy kích thước của phần tử
            total_height = content_element.size['height']
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Screenshot từng phần nếu nội dung quá dài
            if total_height > viewport_height * 1.5:
                print(f"Nội dung dài ({total_height}px), sẽ chia nhỏ để OCR")
                num_parts = int(total_height / (viewport_height * 0.8)) + 1
                
                for i in range(num_parts):
                    scroll_position = i * viewport_height * 0.8
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                    time.sleep(0.5)
                    
                    # Screenshot phần hiện tại
                    screenshot = self.driver.get_screenshot_as_png()
                    image = Image.open(io.BytesIO(screenshot))
                    
                    # OCR
                    print(f"Đang OCR phần {i+1}/{num_parts}...")
                    text = pytesseract.image_to_string(image, lang='vie+eng', config='--psm 6')
                    
                    if text.strip():
                        content_parts.append(text.strip())
            else:
                # Screenshot toàn bộ phần tử nội dung
                print("Đang chụp screenshot nội dung...")
                screenshot = content_element.screenshot_as_png
                image = Image.open(io.BytesIO(screenshot))
                
                # Tăng độ tương phản để OCR tốt hơn
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2)
                
                # OCR
                print("Đang OCR...")
                text = pytesseract.image_to_string(
                    image, 
                    lang='vie+eng',
                    config='--psm 6 --oem 3'
                )
                
                if text.strip():
                    content_parts.append(text.strip())
            
        except Exception as e:
            print(f"Lỗi khi OCR trang: {e}")
            # Fallback: screenshot toàn bộ trang
            try:
                print("Thử OCR toàn bộ trang...")
                screenshot = self.driver.get_screenshot_as_png()
                image = Image.open(io.BytesIO(screenshot))
                text = pytesseract.image_to_string(image, lang='vie+eng')
                if text.strip():
                    content_parts.append(text.strip())
            except Exception as e2:
                print(f"Lỗi khi OCR toàn trang: {e2}")
        
        # Làm sạch text
        full_content = "\n\n".join(content_parts)
        full_content = self.clean_text(full_content)
        
        return full_content
    
    def clean_text(self, text):
        """
        Làm sạch text sau OCR
        """
        # Xóa các dòng trống dư thừa
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Xóa khoảng trắng dư thừa
        text = re.sub(r' +', ' ', text)
        
        # Xóa các ký tự lạ
        text = re.sub(r'[^\w\s\.,;:!?\-()""\'…\n\u0080-\uFFFF]', '', text)
        
        return text.strip()
    
    def get_chapter_links(self, story_url):
        """
        Lấy danh sách link các chapter
        """
        print(f"Đang lấy danh sách chapter từ: {story_url}")
        self.driver.get(story_url)
        time.sleep(2)
        
        chapter_links = []
        try:
            # Thử nhiều selector khác nhau cho link chapter
            link_selectors = [
                "a[href*='chuong']",
                "a[href*='chapter']",
                ".chapter-list a",
                ".list-chapter a",
                "#list-chapter a"
            ]
            
            for selector in link_selectors:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if links:
                    print(f"Tìm thấy {len(links)} link với selector: {selector}")
                    for link in links:
                        href = link.get_attribute("href")
                        if href and href not in chapter_links:
                            chapter_links.append(href)
                    break
                    
        except Exception as e:
            print(f"Lỗi khi lấy danh sách chapter: {e}")
        
        return chapter_links
    
    def download_story(self, story_url, output_file="ebook.txt", start_chapter=1, end_chapter=None, save_images=False):
        """
        Download toàn bộ truyện bằng OCR
        """
        # Lấy danh sách chapter
        chapter_links = self.get_chapter_links(story_url)
        
        if not chapter_links:
            print("Không tìm thấy chapter nào!")
            return
        
        print(f"Tìm thấy {len(chapter_links)} chapter")
        
        # Xác định range cần download
        start_idx = max(0, start_chapter - 1)
        end_idx = min(len(chapter_links), end_chapter) if end_chapter else len(chapter_links)
        
        chapters_to_download = chapter_links[start_idx:end_idx]
        
        # Tạo thư mục output
        output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
        os.makedirs(output_dir, exist_ok=True)
        
        if save_images:
            image_dir = os.path.join(output_dir, "screenshots")
            os.makedirs(image_dir, exist_ok=True)
        
        # Download từng chapter
        with open(output_file, "w", encoding="utf-8") as f:
            for i, chapter_url in enumerate(chapters_to_download, start=start_chapter):
                print(f"\n{'='*50}")
                print(f"Chapter {i}/{end_idx}")
                print(f"{'='*50}")
                
                try:
                    # OCR toàn bộ trang
                    content = self.ocr_full_page(chapter_url)
                    
                    # Lưu screenshot nếu cần
                    if save_images:
                        screenshot_path = os.path.join(image_dir, f"chapter_{i}.png")
                        self.driver.save_screenshot(screenshot_path)
                        print(f"Đã lưu screenshot: {screenshot_path}")
                    
                    # Ghi vào file
                    f.write(f"\n\n{'='*50}\n")
                    f.write(f"CHƯƠNG {i}\n")
                    f.write(f"Link: {chapter_url}\n")
                    f.write(f"{'='*50}\n\n")
                    f.write(content)
                    f.flush()
                    
                    print(f"✓ Hoàn thành chapter {i} ({len(content)} ký tự)")
                    
                except Exception as e:
                    print(f"✗ Lỗi chapter {i}: {e}")
                    continue
                
                # Delay để tránh bị block
                time.sleep(2)
        
        print(f"\n{'='*50}")
        print(f"Hoàn thành! Đã lưu vào: {output_file}")
        print(f"{'='*50}")
    
    def close(self):
        """
        Đóng browser
        """
        self.driver.quit()


# Sử dụng
if __name__ == "__main__":
    # Cấu hình
    STORY_URL = "https://truyendichmienphi.com/truyen/ac-mong-kinh-tap"  # Thay đổi URL
    OUTPUT_FILE = "ebook_output.txt"
    START_CHAPTER = 1      # Chapter bắt đầu
    END_CHAPTER = 5        # Chapter kết thúc (None = tất cả)
    SAVE_SCREENSHOTS = True  # Lưu screenshot mỗi chapter
    
    # Khởi tạo scraper
    scraper = EbookScraper(headless=True)
    
    try:
        # Download truyện
        scraper.download_story(
            story_url=STORY_URL,
            output_file=OUTPUT_FILE,
            start_chapter=START_CHAPTER,
            end_chapter=END_CHAPTER,
            save_images=SAVE_SCREENSHOTS
        )
    finally:
        scraper.close()