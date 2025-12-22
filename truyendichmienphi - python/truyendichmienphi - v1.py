import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\DELL\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
import io
import base64
import time
import re
import os

class EbookDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Ebook Downloader - truyendichmienphi.com")
        self.root.geometry("900x700")
        
        self.queue = queue.Queue()
        self.is_running = False
        self.threads = []
        
        self.setup_ui()
        self.check_queue()
        
    def setup_ui(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Cấu hình
        config_frame = ttk.LabelFrame(main_frame, text="Cấu hình", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(config_frame, text="URL truyện:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.url_entry = ttk.Entry(config_frame, width=70)
        self.url_entry.grid(row=0, column=1, pady=2, padx=5)
        self.url_entry.insert(0, "https://truyendichmienphi.com/truyen/ac-mong-kinh-tap/chuong/")
        
        ttk.Label(config_frame, text="Từ chương:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.start_chapter = ttk.Entry(config_frame, width=10)
        self.start_chapter.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        self.start_chapter.insert(0, "1")
        
        ttk.Label(config_frame, text="Đến chương:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.end_chapter = ttk.Entry(config_frame, width=10)
        self.end_chapter.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        self.end_chapter.insert(0, "10")
        
        ttk.Label(config_frame, text="Số luồng:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.thread_count = ttk.Spinbox(config_frame, from_=1, to=5, width=10)
        self.thread_count.grid(row=3, column=1, sticky=tk.W, pady=2, padx=5)
        self.thread_count.set(2)
        
        ttk.Label(config_frame, text="Thư mục lưu:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.save_path = ttk.Entry(config_frame, width=60)
        self.save_path.grid(row=4, column=1, pady=2, padx=5, sticky=tk.W)
        self.save_path.insert(0, os.path.join(os.getcwd(), "ebooks"))
        ttk.Button(config_frame, text="...", width=5, command=self.browse_folder).grid(row=4, column=2, padx=2)
        
        # Nút điều khiển
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="Bắt đầu tải", command=self.start_download)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Dừng", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="Xóa log", command=self.clear_log).grid(row=0, column=2, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Nhật ký", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=100, height=25, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Cấu hình grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path.delete(0, tk.END)
            self.save_path.insert(0, folder)
    
    def log(self, message):
        self.queue.put(('log', message))
        
    def update_progress(self, value):
        self.queue.put(('progress', value))
        
    def check_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == 'log':
                    self.log_text.insert(tk.END, data + '\n')
                    self.log_text.see(tk.END)
                elif msg_type == 'progress':
                    self.progress['value'] = data
                elif msg_type == 'complete':
                    self.download_complete()
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def start_download(self):
        try:
            base_url = self.url_entry.get().strip()
            start = int(self.start_chapter.get())
            end = int(self.end_chapter.get())
            num_threads = int(self.thread_count.get())
            save_dir = self.save_path.get().strip()
            
            if not base_url:
                messagebox.showerror("Lỗi", "Vui lòng nhập URL!")
                return
            
            if start > end:
                messagebox.showerror("Lỗi", "Chương bắt đầu phải nhỏ hơn chương kết thúc!")
                return
            
            os.makedirs(save_dir, exist_ok=True)
            
            self.is_running = True
            self.start_btn['state'] = tk.DISABLED
            self.stop_btn['state'] = tk.NORMAL
            self.progress['maximum'] = end - start + 1
            self.progress['value'] = 0
            
            self.log(f"Bắt đầu tải từ chương {start} đến {end} với {num_threads} luồng...")
            
            # Chia chương cho các luồng
            chapters = list(range(start, end + 1))
            chunk_size = len(chapters) // num_threads
            
            for i in range(num_threads):
                start_idx = i * chunk_size
                if i == num_threads - 1:
                    thread_chapters = chapters[start_idx:]
                else:
                    thread_chapters = chapters[start_idx:start_idx + chunk_size]
                
                thread = threading.Thread(
                    target=self.download_worker,
                    args=(base_url, thread_chapters, save_dir, i+1)
                )
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
                
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            self.log(f"Lỗi: {str(e)}")
            
    def download_worker(self, base_url, chapters, save_dir, thread_id):
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            driver = webdriver.Chrome(options=chrome_options)
            self.log(f"[Luồng {thread_id}] Đã khởi động browser")
            
            for chapter in chapters:
                if not self.is_running:
                    break
                    
                try:
                    url = f"{base_url}{chapter}"
                    self.log(f"[Luồng {thread_id}] Đang tải chương {chapter}...")
                    
                    driver.get(url)
                    time.sleep(2)
                    
                    # Lấy tiêu đề
                    try:
                        title_elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "h1"))
                        )
                        title = title_elem.text
                    except:
                        title = f"Chương {chapter}"
                    
                    content = f"{title}\n\n"
                    
                    # Lấy text content
                    try:
                        text_elements = driver.find_elements(By.CSS_SELECTOR, ".chapter-content p, .chapter-content div")
                        for elem in text_elements:
                            text = elem.text.strip()
                            if text:
                                content += text + "\n\n"
                    except Exception as e:
                        self.log(f"[Luồng {thread_id}] Không tìm thấy text content: {str(e)}")
                    
                    # Xử lý canvas nếu có
                    try:
                        canvases = driver.find_elements(By.TAG_NAME, "canvas")
                        for idx, canvas in enumerate(canvases):
                            try:
                                # Lấy dữ liệu từ canvas
                                canvas_base64 = driver.execute_script(
                                    "return arguments[0].toDataURL('image/png').substring(21);", 
                                    canvas
                                )
                                
                                # Chuyển đổi base64 sang image
                                image_data = base64.b64decode(canvas_base64)
                                image = Image.open(io.BytesIO(image_data))
                                
                                # OCR
                                text = pytesseract.image_to_string(image, lang='vie')
                                if text.strip():
                                    content += f"\n[Canvas {idx+1}]\n{text}\n\n"
                                    
                            except Exception as e:
                                self.log(f"[Luồng {thread_id}] Lỗi xử lý canvas {idx+1}: {str(e)}")
                                
                    except Exception as e:
                        self.log(f"[Luồng {thread_id}] Không tìm thấy canvas: {str(e)}")
                    
                    # Lưu file
                    filename = f"chuong_{chapter:03d}.txt"
                    filepath = os.path.join(save_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.log(f"[Luồng {thread_id}] ✓ Đã lưu chương {chapter}")
                    self.update_progress(self.progress['value'] + 1)
                    
                except Exception as e:
                    self.log(f"[Luồng {thread_id}] ✗ Lỗi tải chương {chapter}: {str(e)}")
                    
        except Exception as e:
            self.log(f"[Luồng {thread_id}] Lỗi khởi tạo: {str(e)}")
        finally:
            if driver:
                driver.quit()
            self.log(f"[Luồng {thread_id}] Đã đóng browser")
            
            # Kiểm tra xem tất cả threads đã hoàn thành chưa
            self.threads.remove(threading.current_thread())
            if len(self.threads) == 0:
                self.queue.put(('complete', None))
                
    def download_complete(self):
        self.is_running = False
        self.start_btn['state'] = tk.NORMAL
        self.stop_btn['state'] = tk.DISABLED
        self.log("\n=== Hoàn tất tải xuống! ===")
        messagebox.showinfo("Thành công", "Đã tải xong tất cả các chương!")
        
    def stop_download(self):
        self.is_running = False
        self.log("\nĐang dừng...")
        self.stop_btn['state'] = tk.DISABLED

if __name__ == "__main__":
    root = tk.Tk()
    app = EbookDownloader(root)
    root.mainloop()