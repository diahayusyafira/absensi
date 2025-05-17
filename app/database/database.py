# File: app/database/database.py
# Deskripsi: Modul ini berisi konfigurasi dan setup database untuk aplikasi absensi karyawan.
#            Menyediakan koneksi database, session, dan base class untuk model ORM.

# Import library SQLAlchemy untuk ORM (Object Relational Mapping)
from sqlalchemy import create_engine  # Untuk membuat engine database
from sqlalchemy.ext.declarative import declarative_base  # Untuk membuat base class model
from sqlalchemy.orm import sessionmaker  # Untuk membuat session database
import os  # Untuk mengakses variabel lingkungan
from dotenv import load_dotenv  # Untuk memuat variabel dari file .env

# Memuat variabel lingkungan dari file .env
load_dotenv()

# URL koneksi database dari variabel lingkungan atau menggunakan default jika tidak ada
# Format: dialect+driver://username:password@host:port/database
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost/matura_jaya_attendance")

# Membuat engine database SQLAlchemy
# Engine adalah titik masuk ke database, bertanggung jawab untuk koneksi pool dan dialek
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Membuat session factory
# autocommit=False: Perubahan tidak otomatis di-commit
# autoflush=False: Perubahan tidak otomatis di-flush ke database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Membuat base class untuk model-model ORM
# Semua model/class yang merepresentasikan tabel database akan mewarisi Base
Base = declarative_base()

# Fungsi dependency untuk mendapatkan session database
def get_db():
    """
    Fungsi generator untuk mendapatkan session database.

    Digunakan sebagai dependency di FastAPI untuk menyediakan session database ke endpoint.
    Session akan otomatis ditutup setelah request selesai diproses.

    Yields:
        Session: Session database SQLAlchemy
    """
    # Membuat session baru
    db = SessionLocal()
    try:
        # Yield session ke endpoint yang membutuhkan
        yield db
    finally:
        # Pastikan session selalu ditutup, bahkan jika terjadi error
        db.close()