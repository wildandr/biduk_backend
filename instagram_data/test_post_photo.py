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

# Konfigurasi foto
caption = "Caption postingan foto otomatis!"

# OPSI 1: Gunakan foto tunggal (foto PNG) daripada album
print("Mengalihkan ke upload foto tunggal karena format album tidak didukung")
foto_path = "/Users/owwl/Desktop/age distribution.png"
print(f"Mengunggah foto tunggal dari {foto_path}")
media = cl.photo_upload(
    path=foto_path,
    caption=caption
)

print(f"foto berhasil diunggah dengan ID: {media.pk}")
