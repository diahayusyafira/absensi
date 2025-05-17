"""
Script Migrasi Database untuk Menambahkan Kolom alamat_keluar

Script ini digunakan untuk menambahkan kolom 'alamat_keluar' ke tabel 'absensi'
jika kolom tersebut belum ada. Kolom ini diperlukan untuk menyimpan lokasi
karyawan saat melakukan absen keluar.

Penggunaan:
    python migrate_add_alamat_keluar.py
"""

import sqlite3
import logging

# Setup logging untuk mencatat proses migrasi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_database():
    """
    Menambahkan kolom alamat_keluar ke tabel absensi jika belum ada

    Fungsi ini akan:
    1. Terhubung ke database SQLite
    2. Memeriksa apakah kolom alamat_keluar sudah ada
    3. Jika belum ada, tambahkan kolom tersebut
    4. Jika sudah ada, tidak melakukan apa-apa

    Returns:
        bool: True jika migrasi berhasil, False jika gagal
    """
    try:
        # Terhubung ke database SQLite
        conn = sqlite3.connect('absensi.db')
        cursor = conn.cursor()

        # Memeriksa apakah kolom alamat_keluar sudah ada
        cursor.execute("PRAGMA table_info(absensi)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        # Jika kolom belum ada, tambahkan kolom baru
        if 'alamat_keluar' not in column_names:
            logger.info("Menambahkan kolom alamat_keluar ke tabel absensi")
            cursor.execute("ALTER TABLE absensi ADD COLUMN alamat_keluar TEXT")
            conn.commit()
            logger.info("Migrasi berhasil dilakukan")
        else:
            logger.info("Kolom alamat_keluar sudah ada, tidak perlu migrasi")

        # Tutup koneksi database
        conn.close()
        return True
    except Exception as e:
        # Catat error jika terjadi masalah
        logger.error(f"Error selama proses migrasi: {str(e)}", exc_info=True)
        return False

# Jalankan migrasi jika script dijalankan langsung
if __name__ == "__main__":
    migrate_database()
