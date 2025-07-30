from instagrapi import Client
import os

USERNAME = "fanit52422@fenexy.com"
PASSWORD = "Makanmakan3x**"
SESSION_FILE = "session.json"  # File untuk menyimpan sesi

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

# Upload video dengan thumbnail kustom
thumbnail_path = "/Users/owwl/Desktop/age distribution.png"
video_path = "/Users/owwl/Downloads/object_counting/output_video_5fps_counting_test.mp4"
caption = "Caption postingan otomatis!"

# Gunakan video_upload dengan parameter thumbnail
print(f"Mengunggah video dengan thumbnail dari {thumbnail_path}")
media = cl.video_upload(
    path=video_path,
    caption=caption,
    thumbnail=thumbnail_path
)

print(f"Video berhasil diunggah dengan ID: {media.pk}")

# Insights hanya tersedia untuk akun bisnis/profesional
# Matikan kode berikut untuk menghindari error
# print(cl.insights_account())