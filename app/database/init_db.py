# File: app/database/init_db.py
# Deskripsi: Modul ini berisi fungsi untuk inisialisasi database dan pembuatan tabel-tabel.
#            Dapat dijalankan sebagai script terpisah untuk membuat skema database.

# Import engine database dari modul database.py
from app.database.database import engine

# Import Base class yang berisi definisi model-model
from app.database.models import Base

def init_db():
    """
    Fungsi untuk menginisialisasi database dan membuat semua tabel.

    Fungsi ini akan membuat semua tabel yang didefinisikan dalam model-model
    yang mewarisi Base class. Jika tabel sudah ada, tidak akan dibuat ulang.
    """
    # Membuat semua tabel berdasarkan model yang didefinisikan
    # create_all() akan membuat tabel jika belum ada, tidak akan mengubah jika sudah ada
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

# Blok ini akan dieksekusi jika file dijalankan langsung (bukan diimpor)
if __name__ == "__main__":
    # Panggil fungsi init_db untuk membuat tabel-tabel
    init_db()