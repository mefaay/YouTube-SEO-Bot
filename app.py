import tkinter as tk
from tkinter import messagebox
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager

# Global flag to control the video watching loop
stop_flag = False
browser_open_count = 0  # Tarayıcı açılma sayacı
total_browsers_to_open = 0  # Kullanıcı tarafından belirlenen toplam açılacak tarayıcı sayısı


# Utility functions for video ID extraction
def get_video_id_from_url(url):
    video_id = url.split("v=")[-1].split("&")[0]
    return video_id


# Main function to watch video
def watch_video(driver, video_url, search_keywords):
    global stop_flag, browser_open_count
    driver.get("https://www.youtube.com")
    print("YouTube sayfasına gidildi.")
    log_to_text_widget("YouTube sayfasına gidildi.")

    search_box = driver.find_element(By.NAME, "search_query")
    search_box.send_keys(search_keywords)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)

    video_found = False
    while not video_found:
        if stop_flag:  # Stop flag check
            log_to_text_widget("Durdurma komutu alındı.")
            return

        log_to_text_widget("Sayfa taranıyor...")
        time.sleep(2)

        videos = driver.find_elements(By.XPATH, '//*[@id="video-title"]')

        if not videos:
            log_to_text_widget("Video bulunamadı, sayfa kaydırılacak...")
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(1)
            continue

        for video in videos:
            video_url_in_result = video.get_attribute('href')
            print("Bulunan video URL'si:", video_url_in_result)

            video_id_in_result = get_video_id_from_url(video_url_in_result)
            video_id = get_video_id_from_url(video_url)

            if video_id_in_result == video_id:
                video_found = True
                video.click()
                log_to_text_widget("Video bulundu ve izlenmeye başlandı.")
                break

        if not video_found:
            log_to_text_widget("Video bulunamadı, sayfa aşağı kaydırılıyor...")
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(3)

    total_time_watched = 0
    watch_durations = [20, 55, 120]  # İzlenecek süreler
    current_target_duration = watch_durations[0]  # İlk hedef süre 20 saniye olacak

    while total_time_watched < watch_durations[-1]:
        if stop_flag:  # Stop flag check
            log_to_text_widget("Durdurma komutu alındı.")
            return

        current_time = float(driver.execute_script("return document.querySelector('video').currentTime"))
        is_ad_playing = driver.execute_script("return document.querySelector('video').classList.contains('ad-showing')")
        if is_ad_playing:
            log_to_text_widget("Reklam oynuyor, bekleniyor...")
            while is_ad_playing and not stop_flag:
                time.sleep(1)
                is_ad_playing = driver.execute_script(
                    "return document.querySelector('video').classList.contains('ad-showing')"
                )
            continue

        if current_time >= current_target_duration:
            log_to_text_widget(f"Video {current_target_duration} saniye izlendi, duraklatılıyor...")
            driver.execute_script("document.querySelector('video').pause()")  # Videoyu duraklat

            time.sleep(3)  # 3 saniye bekleme

            log_to_text_widget("Video devam ediyor...")
            driver.execute_script("document.querySelector('video').play()")  # Videoyu oynatmaya devam et

            total_time_watched = current_time

            if current_target_duration == 20:
                current_target_duration = watch_durations[1]
            elif current_target_duration == 55:
                current_target_duration = watch_durations[2]
            else:
                break

        time.sleep(1)

    log_to_text_widget(f"Toplam {total_time_watched} saniye izlendi, tarayıcı kapatılıyor.")
    driver.quit()
    browser_open_count += 1
    counter_label.config(text=f"Tarayıcı Açılma Sayısı: {browser_open_count}")

    if browser_open_count >= total_browsers_to_open:
        log_to_text_widget("Belirtilen tarayıcı açılma sayısına ulaşıldı.")
        stop_flag = True  # Video izleme durduruluyor


def log_to_text_widget(message):
    text_widget.insert(tk.END, message + '\n')  # Add message to the Text widget
    text_widget.yview(tk.END)  # Scroll to the bottom


# Start browser and watch video function
def start_browser_and_watch(video_url, search_keywords):
    global stop_flag, total_browsers_to_open, browser_open_count
    stop_flag = False  # Reset the flag when starting

    try:
        total_browsers_to_open = int(entry_browsers_to_open.get())
    except ValueError:
        messagebox.showerror("Hata", "Lütfen geçerli bir sayı girin.")
        return

    while browser_open_count < total_browsers_to_open and not stop_flag:
        options = Options()
        options.headless = False  # Tarayıcıyı görünür açıyoruz (headless değil)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            log_to_text_widget("Yeni tarayıcı başlatılıyor...")
            browser_open_count += 1
            counter_label.config(text=f"Tarayıcı Açılma Sayısı: {browser_open_count}")

            watch_video(driver, video_url, search_keywords)
        except Exception as e:
            log_to_text_widget(f"Hata oluştu: {e}")
        finally:
            driver.quit()

        time.sleep(2)

    if browser_open_count >= total_browsers_to_open:
        messagebox.showinfo("Tamamlandı", "Tüm işlemler başarıyla tamamlandı!")
        start_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)


# Start button click handler
def on_start_button_click():
    video_url = entry_video_url.get()
    search_keywords = entry_keywords.get()

    if not video_url or not search_keywords:
        messagebox.showerror("Hata", "Lütfen anahtar kelimeleri ve video URL'sini girin.")
        return

    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    thread = Thread(target=start_browser_and_watch, args=(video_url, search_keywords))
    thread.start()


# Stop button click handler
def on_stop_button_click():
    global stop_flag
    stop_flag = True
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    messagebox.showinfo("Durduruldu", "Program başarıyla durduruldu!")


# GUI Design
root = tk.Tk()
root.title("YouTube Seo Programı")
root.geometry("600x500")  # Arayüzü genişlettik
root.configure(bg="#f0f0f0")

# Font settings
label_font = ("Helvetica", 12)
entry_font = ("Helvetica", 10)

# Entry Widgets
label_keywords = tk.Label(root, text="Anahtar Kelimeler (Hashtagsız veya hashtagli):", font=label_font, bg="#f0f0f0")
label_keywords.pack(pady=10)

entry_keywords = tk.Entry(root, width=50, font=entry_font)
entry_keywords.pack(pady=5)

label_video_url = tk.Label(root, text="Video URL'si:", font=label_font, bg="#f0f0f0")
label_video_url.pack(pady=10)

entry_video_url = tk.Entry(root, width=50, font=entry_font)
entry_video_url.pack(pady=5)

label_browsers_to_open = tk.Label(root, text="Hedef İzlenme Sayısı:", font=label_font, bg="#f0f0f0")
label_browsers_to_open.pack(pady=10)

entry_browsers_to_open = tk.Entry(root, width=50, font=entry_font)
entry_browsers_to_open.pack(pady=5)

# Start and Stop Buttons
button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=20)

start_button = tk.Button(button_frame, text="Başlat", font=label_font, command=on_start_button_click)
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(button_frame, text="Durdur", font=label_font, command=on_stop_button_click, state=tk.DISABLED)
stop_button.grid(row=0, column=1, padx=10)

# Counter Label
counter_label = tk.Label(root, text="Toplam İzlenme Sayısı: 0", font=label_font, bg="#f0f0f0")
counter_label.pack(pady=10)

# Text Widget for Logs
log_frame = tk.Frame(root, bg="#f0f0f0")
log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

text_widget = tk.Text(log_frame, height=10, font=("Helvetica", 9), wrap=tk.WORD)
text_widget.pack(fill=tk.BOTH, expand=True)

root.mainloop()
