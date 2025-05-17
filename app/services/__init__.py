# File: app/services/__init__.py
# Deskripsi: File inisialisasi untuk package services.
#            Memungkinkan direktori services diimpor sebagai package Python.
#            Mengekspos layanan GPS untuk digunakan di modul lain.

# Mengekspos kelas GPSService dari modul gps_service
from app.services.gps_service import GPSService

# Daftar komponen yang tersedia saat mengimpor package
__all__ = [
    'GPSService'
]
