from instagrapi import Client
import os
import time

# --- Konfigurasi ---
USERNAME = "fanit52422@fenexy.com"
PASSWORD = "Makanmakan3x**"
SESSION_FILE = "session.json"  # File untuk menyimpan sesi

# --- Inisialisasi klien ---
cl = Client()

# Cek apakah file sesi sudah ada
if os.path.exists(SESSION_FILE):
    print(f"Menggunakan sesi yang tersimpan dari {SESSION_FILE}")
    cl.load_settings(SESSION_FILE)  # Muat sesi yang sudah ada
    cl.login(USERNAME, PASSWORD)  # Login dengan kredensial yang sama
else:
    print("Sesi tidak ditemukan, membuat sesi baru...")
    cl.login(USERNAME, PASSWORD)  # Login biasa untuk membuat sesi baru
    cl.dump_settings(SESSION_FILE)  # Simpan sesi ke file
    print(f"Sesi baru disimpan ke {SESSION_FILE}")

# --- MENU PILIHAN ---
print("\n=== INSTAGRAM STORY UPLOADER ===")
print("1. Upload Story Foto")
print("2. Upload Story Video")
choice = input("Pilih jenis story (1/2): ")

# --- Path file ---
if choice == "1":
    # Path ke file foto
    media_path = "/Users/owwl/Desktop/age distribution.png"
    media_type = "foto"
elif choice == "2":
    # Path ke file video
    media_path = "/Users/owwl/Downloads/object_counting/output_video_5fps_counting_test.mp4"
    media_type = "video"
else:
    print("Pilihan tidak valid!")
    exit(1)

# --- Teks/caption untuk story ---
story_text = input(f"Masukkan teks untuk story {media_type} (opsional): ")

# --- Upload Story ---
try:
    print(f"\nMengunggah {media_type} ke story...")
    
    if media_type == "foto":
        # Upload foto ke story
        result = cl.photo_upload_to_story(
            path=media_path,
            caption=story_text
        )
        print(f"Story foto berhasil diunggah dengan ID: {result.pk}")
        
    else:  # video
        # Upload video ke story
        # Untuk video, kita perlu thumbnail
        thumbnail_path = "/Users/owwl/Desktop/age distribution.png"  # Bisa gunakan file yang sama atau berbeda
        
        print(f"Menggunakan thumbnail: {thumbnail_path}")
        result = cl.video_upload_to_story(
            path=media_path,
            caption=story_text,
            thumbnail=thumbnail_path
        )
        print(f"Story video berhasil diunggah dengan ID: {result.pk}")
    
    print("\nStory berhasil dipublikasikan!")
    print("Story akan otomatis hilang setelah 24 jam.")
    
except Exception as e:
    print(f"Gagal mengunggah story: {e}")

# --- Informasi tambahan ---
print("\nInformasi Tambahan Story:")
