"""
Script untuk menambahkan kolom uang_makan ke tabel absensi

Kolom uang_makan digunakan untuk menandai apakah karyawan sudah menerima uang makan atau belum
"""

import sqlite3
import logging

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate():
    """
    Fungsi untuk menambahkan kolom uang_makan ke tabel absensi
    """
    try:
        # Buka koneksi ke database
        conn = sqlite3.connect('absensi.db')
        cursor = conn.cursor()
        
        # Cek apakah kolom uang_makan sudah ada
        cursor.execute("PRAGMA table_info(absensi)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'uang_makan' not in column_names:
            # Tambahkan kolom uang_makan jika belum ada
            logger.info("Menambahkan kolom uang_makan ke tabel absensi...")
            cursor.execute("ALTER TABLE absensi ADD COLUMN uang_makan BOOLEAN DEFAULT 0")
            conn.commit()
            logger.info("Kolom uang_makan berhasil ditambahkan!")
        else:
            logger.info("Kolom uang_makan sudah ada di tabel absensi.")
        
        # Tutup koneksi
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error saat migrasi: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Memulai migrasi database...")
    success = migrate()
    if success:
        logger.info("Migrasi selesai dengan sukses!")
    else:
        logger.error("Migrasi gagal!")
