# Import library SQLAlchemy untuk interaksi dengan database
from sqlalchemy import create_engine, inspect  # Engine dan inspector database
from sqlalchemy.ext.declarative import declarative_base  # Base class untuk model ORM
from sqlalchemy.orm import sessionmaker  # Pembuat session database
import logging  # Untuk pencatatan log
import os  # Untuk operasi sistem

# Konfigurasi logging untuk mencatat aktivitas database
logging.basicConfig(
    level=logging.DEBUG,  # Level logging: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Format pesan log
)
logger = logging.getLogger(__name__)  # Membuat logger untuk modul ini

# URL database SQLite
# SQLite adalah database file-based yang disimpan di direktori yang sama dengan aplikasi
SQLALCHEMY_DATABASE_URL = "sqlite:///./absensi.db"

# Membuat Base class untuk model ORM
# Base class ini akan digunakan untuk mendefinisikan model-model database
Base = declarative_base()

def init_db():
    """
    Inisialisasi database, membuat engine dan tabel-tabel.

    Fungsi ini membuat engine SQLAlchemy, membuat tabel-tabel berdasarkan model yang didefinisikan,
    dan memverifikasi bahwa tabel-tabel telah dibuat dengan benar.

    Returns:
        Engine: SQLAlchemy engine yang telah dikonfigurasi

    Raises:
        Exception: Jika terjadi error saat inisialisasi database
    """
    try:
        # Membuat engine SQLAlchemy
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,  # URL database
            connect_args={"check_same_thread": False},  # Argumen koneksi khusus SQLite
            echo=True  # Aktifkan logging SQL
        )
        logger.info("Database engine created successfully")

        # Membuat tabel jika belum ada
        Base.metadata.create_all(bind=engine)  # Membuat tabel berdasarkan model
        logger.info("Database tables created successfully")

        # Verifikasi tabel telah dibuat
        inspector = inspect(engine)  # Membuat inspector untuk memeriksa database
        tables = inspector.get_table_names()  # Mendapatkan daftar nama tabel
        logger.info(f"Available tables: {tables}")

        return engine
    except Exception as e:
        # Tangani error jika terjadi
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise  # Re-raise exception untuk ditangani di level yang lebih tinggi

# Inisialisasi database dan membuat engine
try:
    # Panggil fungsi init_db untuk membuat engine
    engine = init_db()

    # Membuat SessionLocal class untuk membuat session database
    # autocommit=False: Perubahan tidak otomatis di-commit
    # autoflush=False: Perubahan tidak otomatis di-flush ke database
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Session maker created successfully")
except Exception as e:
    # Tangani error jika terjadi
    logger.error(f"Error setting up database: {str(e)}", exc_info=True)
    raise  # Re-raise exception untuk ditangani di level yang lebih tinggi

def get_db():
    """
    Dependency untuk mendapatkan session database.

    Fungsi ini digunakan sebagai dependency injection di FastAPI untuk menyediakan
    session database ke endpoint-endpoint API. Session akan otomatis ditutup
    setelah request selesai diproses.

    Yields:
        Session: Session database SQLAlchemy

    Raises:
        Exception: Jika terjadi error saat menggunakan session
    """
    # Buat session database baru
    db = SessionLocal()
    try:
        # Log bahwa session telah dimulai
        logger.debug("Database session started")
        # Yield session ke endpoint yang membutuhkan
        yield db
    except Exception as e:
        # Tangani error jika terjadi
        logger.error(f"Error in database session: {str(e)}", exc_info=True)
        raise  # Re-raise exception untuk ditangani di level yang lebih tinggi
    finally:
        # Pastikan session selalu ditutup, bahkan jika terjadi error
        logger.debug("Closing database session")
        db.close()  # Tutup session database