"""
Script migrasi untuk menambahkan kolom uang_transport ke tabel absensi.

Penggunaan:
    python migrate_add_uang_transport.py

Script ini akan:
1. Menambahkan kolom uang_transport ke tabel absensi
2. Mengatur nilai default uang_transport ke False untuk semua data yang sudah ada
"""

import sqlite3
import os
import logging

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path ke file database
DB_PATH = "absensi.db"

def check_column_exists(cursor, table_name, column_name):
    """
    Memeriksa apakah kolom sudah ada di tabel
    
    Args:
        cursor: Cursor database
        table_name: Nama tabel
        column_name: Nama kolom
        
    Returns:
        bool: True jika kolom sudah ada, False jika belum
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(column[1] == column_name for column in columns)

def add_column(cursor, table_name, column_name, column_type):
    """
    Menambahkan kolom baru ke tabel
    
    Args:
        cursor: Cursor database
        table_name: Nama tabel
        column_name: Nama kolom
        column_type: Tipe data kolom
    """
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        logger.info(f"Kolom {column_name} berhasil ditambahkan ke tabel {table_name}")
    except sqlite3.OperationalError as e:
        logger.error(f"Error saat menambahkan kolom: {str(e)}")
        raise

def migrate_database():
    """
    Melakukan migrasi database untuk menambahkan kolom uang_transport
    """
    # Periksa apakah file database ada
    if not os.path.exists(DB_PATH):
        logger.error(f"File database {DB_PATH} tidak ditemukan")
        return False
    
    # Buka koneksi ke database
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Periksa apakah kolom uang_transport sudah ada
        if check_column_exists(cursor, "absensi", "uang_transport"):
            logger.info("Kolom uang_transport sudah ada di tabel absensi")
            return True
        
        # Tambahkan kolom uang_transport
        add_column(cursor, "absensi", "uang_transport", "BOOLEAN DEFAULT 0")
        
        # Commit perubahan
        conn.commit()
        logger.info("Migrasi database berhasil")
        return True
    
    except Exception as e:
        logger.error(f"Error saat migrasi database: {str(e)}")
        if conn:
            conn.rollback()
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Memulai migrasi database...")
    success = migrate_database()
    
    if success:
        logger.info("Migrasi database selesai dengan sukses")
    else:
        logger.error("Migrasi database gagal")
