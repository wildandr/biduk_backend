from instagrapi import Client
import os
from PIL import Image  # Memerlukan: pip install Pillow

# --- Konfigurasi ---
USERNAME = "fanit52422@fenexy.com"
PASSWORD = "Makanmakan3x**"
SESSION_FILE = "session.json"  # File untuk menyimpan sesi
CAPTION = "Caption untuk album foto otomatis!"

# Fungsi untuk mengonversi PNG ke JPEG
def convert_png_to_jpg(png_path, quality=95):
    """Mengonversi gambar PNG ke JPEG yang didukung Instagram"""
    # Buat path output dengan mengganti ekstensi
    jpg_path = png_path.replace('.png', '.jpg')
    
    try:
        img = Image.open(png_path).convert('RGB')
        img.save(jpg_path, 'JPEG', quality=quality)
        print(f"✓ Berhasil mengonversi {png_path} ke {jpg_path}")
        return jpg_path
    except Exception as e:
        print(f"✗ Gagal mengonversi gambar: {e}")
        return None

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

# --- Konfigurasi foto album ---
# Sesuaikan paths ini dengan lokasi file PNG Anda
png_paths = [
    "/Users/owwl/Desktop/age distribution.png",
    # Tambahkan path gambar PNG kedua di sini
    "/Users/owwl/Desktop/age distribution.png",  # Menggunakan file yang sama untuk contoh
]

# --- Proses konversi PNG ke JPEG ---
jpg_paths = []
for png_path in png_paths:
    jpg_path = convert_png_to_jpg(png_path)
    if jpg_path:  # Jika konversi berhasil
        jpg_paths.append(jpg_path)

# --- Upload album foto ---
if len(jpg_paths) >= 2:  # Album memerlukan minimal 2 foto
    print(f"Mengunggah album dengan {len(jpg_paths)} foto")
    try:
        media = cl.album_upload(
            paths=jpg_paths,
            caption=CAPTION
        )
        print(f"Album foto berhasil diunggah dengan ID: {media.pk}")
        
        # Hapus file JPEG sementara yang dibuat
        for jpg_path in jpg_paths:
            try:
                os.remove(jpg_path)
                print(f"File sementara {jpg_path} dihapus")
            except:
                print(f"Tidak dapat menghapus file {jpg_path}")
                
    except Exception as e:
        print(f"Gagal mengunggah album: {e}")
else:
    print("Diperlukan minimal 2 foto untuk album. Pastikan konversi berhasil.")
