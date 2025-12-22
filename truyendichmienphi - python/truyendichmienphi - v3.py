import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
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
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def get_chapter_content(self, url):
        """
        Lấy nội dung từ một chapter
        """
        print(f"Đang truy cập: {url}")
        self.driver.get(url)
        time.sleep(3)  # Tăng thời gian chờ để trang load đầy đủ
        
        content = []
        chapter_title = ""
        
        # Lấy tiêu đề chương
        try:
            title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.text-lg.font-bold")
            chapter_title = title_elem.text.strip()
            print(f"Tiêu đề: {chapter_title}")
        except Exception as e:
            print(f"Không tìm thấy tiêu đề: {e}")
        
        # Tìm container chứa nội dung chương
        # Thử nhiều selector khác nhau
        content_selectors = [
            ".chapter-content",
            "#chapter-content", 
            "[class*='chapter']",
            "[class*='content']",
            "article",
            ".prose",
            "main"
        ]
        
        chapter_container = None
        for selector in content_selectors:
            try:
                chapter_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                print(f"Tìm thấy container với selector: {selector}")
                break
            except:
                continue
        
        if not chapter_container:
            print("Không tìm thấy container chứa nội dung, thử lấy toàn bộ body")
            chapter_container = self.driver.find_element(By.TAG_NAME, "body")
        
        # Lấy tất cả text elements trong container
        try:
            # Lấy tất cả các thẻ có thể chứa text
            text_elements = chapter_container.find_elements(
                By.CSS_SELECTOR, 
                "p, div, span, h1, h2, h3, h4, h5, h6"
            )
            
            seen_texts = set()  # Tránh trùng lặp
            
            for elem in text_elements:
                # Bỏ qua các element ẩn
                if not elem.is_displayed():
                    continue
                
                # Lấy text trực tiếp của element (không lấy của children)
                text = elem.text.strip()
                
                # Lọc bỏ text rỗng, trùng lặp và text của header/navigation
                if (text and 
                    text not in seen_texts and 
                    len(text) > 5 and  # Lọc text quá ngắn
                    not self._is_navigation_text(text)):
                    
                    content.append(text)
                    seen_texts.add(text)
                    
        except Exception as e:
            print(f"Lỗi khi lấy text: {e}")
        
        # Lấy nội dung từ canvas (nếu có) - cho các trang dùng anti-scraping
        try:
            canvases = chapter_container.find_elements(By.TAG_NAME, "canvas")
            if canvases:
                print(f"Phát hiện {len(canvases)} canvas elements")
                
                for i, canvas in enumerate(canvases):
                    try:
                        print(f"Đang xử lý canvas {i+1}/{len(canvases)}")
                        
                        # Chụp screenshot canvas
                        canvas_png = canvas.screenshot_as_png
                        image = Image.open(io.BytesIO(canvas_png))
                        
                        # OCR để lấy text
                        text = pytesseract.image_to_string(image, lang='vie+eng')
                        if text.strip():
                            content.append(f"\n[Nội dung từ canvas {i+1}]\n{text.strip()}")
                    except Exception as e:
                        print(f"Lỗi khi xử lý canvas {i+1}: {e}")
                        
        except Exception as e:
            print(f"Lỗi khi tìm canvas: {e}")
        
        # Nếu không lấy được nội dung, thử phương pháp dự phòng
        if not content:
            print("Không lấy được nội dung, thử phương pháp dự phòng...")
            try:
                # Lấy toàn bộ innerText của body
                body_text = self.driver.execute_script("return document.body.innerText;")
                if body_text:
                    content.append(body_text)
            except Exception as e:
                print(f"Lỗi phương pháp dự phòng: {e}")
        
        # Kết hợp content
        final_content = f"{chapter_title}\n\n" if chapter_title else ""
        final_content += "\n\n".join(content)
        
        print(f"Đã lấy được {len(content)} đoạn text")
        return final_content
    
    def _is_navigation_text(self, text):
        """
        Kiểm tra xem text có phải là navigation/header không
        """
        nav_keywords = [
            "chương trước", "chương sau", "mục lục", 
            "trang chủ", "đăng nhập", "đăng ký",
            "menu", "tìm kiếm", "thể loại"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in nav_keywords)
    
    def get_chapter_links(self, story_url):
        """
        Lấy danh sách link các chapter
        """
        print(f"Đang lấy danh sách chapter từ: {story_url}")
        self.driver.get(story_url)
        time.sleep(3)
        
        chapter_links = []
        
        # Thử nhiều selector khác nhau để tìm link chapter
        link_selectors = [
            "a[href*='chuong']",
            "a[href*='chapter']",
            "a[href*='chap']",
            ".chapter-list a",
            ".list-chapter a"
        ]
        
        for selector in link_selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    href = link.get_attribute("href")
                    if href and href not in chapter_links:
                        chapter_links.append(href)
                
                if chapter_links:
                    print(f"Tìm thấy links với selector: {selector}")
                    break
            except Exception as e:
                continue
        
        return chapter_links
    
    def download_story(self, story_url, output_file="ebook.txt", start_chapter=1, end_chapter=None):
        """
        Download toàn bộ truyện
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
        
        # Tạo thư mục output nếu chưa có
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        # Download từng chapter
        with open(output_file, "w", encoding="utf-8") as f:
            for i, chapter_url in enumerate(chapters_to_download, start=start_chapter):
                print(f"\n{'='*60}")
                print(f"Chapter {i}/{end_idx}")
                print(f"{'='*60}")
                
                try:
                    content = self.get_chapter_content(chapter_url)
                    
                    if content.strip():
                        f.write(f"\n\n{'='*60}\n")
                        f.write(f"CHƯƠNG {i}\n")
                        f.write(f"{'='*60}\n\n")
                        f.write(content)
                        f.flush()
                        
                        print(f"✓ Hoàn thành chapter {i} - {len(content)} ký tự")
                    else:
                        print(f"⚠ Chapter {i} không có nội dung")
                    
                except Exception as e:
                    print(f"✗ Lỗi chapter {i}: {e}")
                    continue
                
                # Delay để tránh bị block
                time.sleep(2)
        
        print(f"\n{'='*60}")
        print(f"Hoàn thành! Đã lưu vào: {output_file}")
        print(f"{'='*60}")
    
    def close(self):
        """
        Đóng browser
        """
        self.driver.quit()


# Sử dụng
if __name__ == "__main__":
    # Cấu hình
    STORY_URL = "https://truyendichmienphi.com/truyen/ac-mong-kinh-tap"
    OUTPUT_FILE = "ebook_output.txt"
    START_CHAPTER = 1  # Chapter bắt đầu
    END_CHAPTER = 5    # Chapter kết thúc (None = tất cả)
    
    # Khởi tạo scraper
    scraper = EbookScraper(headless=False)  # Đặt False để debug
    
    try:
        # Download truyện
        scraper.download_story(
            story_url=STORY_URL,
            output_file=OUTPUT_FILE,
            start_chapter=START_CHAPTER,
            end_chapter=END_CHAPTER
        )
    finally:
        scraper.close()