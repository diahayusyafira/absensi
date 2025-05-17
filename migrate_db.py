"""
Script untuk melakukan migrasi database, menambahkan kolom baru ke tabel Absensi
"""
import sqlite3
import logging

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_database():
    """
    Fungsi untuk melakukan migrasi database, menambahkan kolom baru ke tabel Absensi
    """
    try:
        # Koneksi ke database
        conn = sqlite3.connect('absensi.db')
        cursor = conn.cursor()
        logger.info("Berhasil terhubung ke database")

        # Cek apakah kolom waktu sudah ada
        cursor.execute("PRAGMA table_info(absensi)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Tambahkan kolom waktu jika belum ada
        if 'waktu' not in column_names:
            logger.info("Menambahkan kolom 'waktu' ke tabel absensi")
            cursor.execute("ALTER TABLE absensi ADD COLUMN waktu TEXT")
        else:
            logger.info("Kolom 'waktu' sudah ada di tabel absensi")
        
        # Tambahkan kolom hari jika belum ada
        if 'hari' not in column_names:
            logger.info("Menambahkan kolom 'hari' ke tabel absensi")
            cursor.execute("ALTER TABLE absensi ADD COLUMN hari TEXT")
        else:
            logger.info("Kolom 'hari' sudah ada di tabel absensi")
        
        # Tambahkan kolom latitude jika belum ada
        if 'latitude' not in column_names:
            logger.info("Menambahkan kolom 'latitude' ke tabel absensi")
            cursor.execute("ALTER TABLE absensi ADD COLUMN latitude REAL")
        else:
            logger.info("Kolom 'latitude' sudah ada di tabel absensi")
        
        # Tambahkan kolom longitude jika belum ada
        if 'longitude' not in column_names:
            logger.info("Menambahkan kolom 'longitude' ke tabel absensi")
            cursor.execute("ALTER TABLE absensi ADD COLUMN longitude REAL")
        else:
            logger.info("Kolom 'longitude' sudah ada di tabel absensi")
        
        # Commit perubahan
        conn.commit()
        logger.info("Migrasi database berhasil")
        
        # Tutup koneksi
        conn.close()
        logger.info("Koneksi database ditutup")
        
        return True
    except Exception as e:
        logger.error(f"Error saat melakukan migrasi database: {str(e)}")
        return False

if __name__ == "__main__":
    # Jalankan migrasi
    success = migrate_database()
    if success:
        print("Migrasi database berhasil")
    else:
        print("Migrasi database gagal")
