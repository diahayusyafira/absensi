# File: app/models/__init__.py
# Deskripsi: File inisialisasi untuk package models.
#            Memungkinkan direktori models diimpor sebagai package Python.
#            Mengekspos model pengenalan wajah untuk digunakan di modul lain.

# Mengekspos kelas FaceRecognitionModel dari modul face_recognition
from app.models.face_recognition import FaceRecognitionModel

# Daftar komponen yang tersedia saat mengimpor package
__all__ = [
    'FaceRecognitionModel'
]
