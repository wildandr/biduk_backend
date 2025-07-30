from instagrapi import Client
import os
import json
import datetime

# --- Konfigurasi ---
# Ganti dengan username dan password Anda
USERNAME = "fanit52422@fenexy.com"
PASSWORD = "Makanmakan3x*"
TARGET_USERNAME = "bidukbidukberlabuh"
SESSION_FILE = "session.json"
OUTPUT_FILE = "instagram_analytics.json"

# --- Helper Function untuk JSON serialization ---
def json_serial(obj):
    """JSON serializer untuk objek datetime, URL, dan objek lainnya"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    # Handle pydantic URL objects
    try:
        # Jika objek memiliki metode __str__, gunakan itu
        if hasattr(obj, '__str__'):
            return str(obj)
    except:
        pass
    # Jika objek dari pydantic, coba konversi ke dict
    try:
        if hasattr(obj, 'dict'):
            return obj.dict()
    except:
        pass
    raise TypeError(f'Type {type(obj)} not serializable')

# --- Inisialisasi Klien ---
cl = Client()

# Menggunakan kembali sesi yang ada jika memungkinkan untuk menghindari login berulang
if os.path.exists(SESSION_FILE):
    cl.load_settings(SESSION_FILE)
    cl.login(USERNAME, PASSWORD)
else:
    cl.login(USERNAME, PASSWORD)
    cl.dump_settings(SESSION_FILE)

try:
    # --- Mendapatkan Informasi Profil ---
    print(f"Mengambil data untuk akun: {TARGET_USERNAME}")
    user_info = cl.user_info_by_username(TARGET_USERNAME)

    # Buat struktur data JSON untuk informasi profil
    profile_data = {
        "username": user_info.username,
        "full_name": user_info.full_name,
        "biography": user_info.biography,
        "profile_pic_url": str(user_info.profile_pic_url),  # Konversi URL ke string
        "follower_count": user_info.follower_count,
        "following_count": user_info.following_count,
        "media_count": user_info.media_count
    }

    # --- Mendapatkan Informasi Postingan ---
    print("Mengambil data postingan...")
    
    posts_data = []
    
    # Langsung gunakan API mobile (v1) untuk mendapatkan postingan
    try:
        medias = cl.user_medias_v1(user_info.pk, amount=50)  # Batasi jumlah postingan yang diambil
    except Exception as e:
        print(f"Error saat mengambil media dengan API v1: {e}")
        print("Mencoba metode alternatif...")
        # Jika masih gagal, coba dengan user_medias yang akan otomatis memilih metode yang tepat
        medias = cl.user_medias(user_info.pk, amount=50)

    if medias:
        for media in medias:
            # Ekstraksi data yang diperlukan untuk menghindari masalah serialisasi
            post = {
                "id": str(media.pk),  # Konversi ke string untuk memastikan keamanan JSON
                "taken_at": media.taken_at,
                "like_count": media.like_count if hasattr(media, 'like_count') else 0,
                "comment_count": media.comment_count if hasattr(media, 'comment_count') else 0
            }
            posts_data.append(post)
    
    # Gabungkan semua data
    instagram_data = {
        "profile": profile_data,
        "posts": posts_data
    }
    
    # Simpan ke file JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(instagram_data, f, default=json_serial, indent=4, ensure_ascii=False)
    
    print(f"Data berhasil disimpan ke {OUTPUT_FILE}")
    
    # Tampilkan ringkasan
    print(f"\nRINGKASAN ANALISIS:")
    print(f"Nama Akun: {profile_data['username']} ({profile_data['full_name']})")
    print(f"Jumlah Followers: {profile_data['follower_count']}")
    print(f"Jumlah Postingan: {profile_data['media_count']}")
    print(f"Jumlah Postingan yang Diambil: {len(posts_data)}")
    
except Exception as e:
    print(f"Terjadi kesalahan: {e}")
