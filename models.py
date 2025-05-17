# Import library SQLAlchemy untuk definisi model database
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, LargeBinary, Float  # Tipe kolom database
from sqlalchemy.orm import relationship  # Untuk relasi antar tabel
from database import Base  # Base class dari modul database.py
from datetime import datetime  # Untuk manipulasi tanggal dan waktu
import numpy as np  # Untuk operasi array dan matriks
import sqlite3  # Untuk interaksi langsung dengan SQLite jika diperlukan

class Karyawan(Base):
    """
    Model untuk menyimpan data karyawan

    Atribut:
    - id: Primary key
    - nama: Nama lengkap karyawan
    - email: Email karyawan (unik)
    - no_telepon: Nomor telepon karyawan
    - jabatan: Jabatan karyawan
    - departemen: Departemen karyawan
    - alamat: Alamat karyawan
    - tanggal_bergabung: Tanggal karyawan bergabung
    - status: Status aktif karyawan (True/False)
    - foto: Foto karyawan dalam format biner

    Relasi:
    - absensi: Relasi one-to-many ke tabel Absensi
    - face_encoding: Relasi one-to-one ke tabel FaceEncoding
    """
    __tablename__ = "karyawan"  # Nama tabel di database

    # Definisi kolom-kolom tabel
    id = Column(Integer, primary_key=True)  # ID unik karyawan
    nama = Column(String(100), nullable=False)  # Nama karyawan, tidak boleh kosong
    email = Column(String(100), unique=True, nullable=False)  # Email karyawan, harus unik
    no_telepon = Column(String(20), nullable=False)  # Nomor telepon karyawan
    jabatan = Column(String(50), nullable=False)  # Jabatan karyawan
    departemen = Column(String(50), nullable=False)  # Departemen karyawan
    alamat = Column(String(200), nullable=False)  # Alamat karyawan
    tanggal_bergabung = Column(DateTime, nullable=False, default=datetime.now)  # Tanggal bergabung
    status = Column(Boolean, default=True)  # Status aktif karyawan
    foto = Column(LargeBinary, nullable=True)  # Foto karyawan dalam format biner

    # Definisi relasi
    absensi = relationship("Absensi", back_populates="karyawan")  # Relasi ke tabel Absensi
    face_encoding = relationship("FaceEncoding", back_populates="karyawan", uselist=False)  # Relasi ke tabel FaceEncoding

class FaceEncoding(Base):
    """
    Model untuk menyimpan encoding wajah karyawan

    Atribut:
    - id: Primary key
    - karyawan_id: Foreign key ke tabel karyawan
    - encoding: Encoding wajah dalam format string JSON
    - created_at: Waktu pembuatan encoding
    - updated_at: Waktu terakhir update encoding

    Relasi:
    - karyawan: Relasi many-to-one ke tabel Karyawan

    Metode:
    - get_encoding_array: Konversi string encoding ke numpy array
    - set_encoding_array: Konversi numpy array ke string untuk penyimpanan
    """
    __tablename__ = "face_encoding"  # Nama tabel di database

    # Definisi kolom-kolom tabel
    id = Column(Integer, primary_key=True)  # ID unik encoding
    karyawan_id = Column(Integer, ForeignKey("karyawan.id"), unique=True)  # ID karyawan, harus unik
    encoding = Column(String, nullable=False)  # Encoding wajah sebagai string JSON
    created_at = Column(DateTime, default=datetime.now)  # Waktu pembuatan
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # Waktu update

    # Definisi relasi
    karyawan = relationship("Karyawan", back_populates="face_encoding")  # Relasi ke tabel Karyawan

    def get_encoding_array(self):
        """
        Konversi string encoding yang tersimpan kembali ke numpy array

        Returns:
            numpy.ndarray: Array encoding wajah
        """
        import json
        return np.array(json.loads(self.encoding))

    def set_encoding_array(self, encoding_array):
        """
        Konversi numpy array ke string untuk penyimpanan

        Args:
            encoding_array (numpy.ndarray): Array encoding wajah
        """
        import json
        self.encoding = json.dumps(encoding_array.tolist())

class Absensi(Base):
    """
    Model untuk menyimpan data absensi karyawan

    Atribut:
    - id: Primary key
    - karyawan_id: Foreign key ke tabel karyawan
    - tanggal: Tanggal absensi (default: tanggal hari ini)
    - jam_masuk: Waktu absen masuk dalam format DateTime
    - jam_keluar: Waktu absen keluar dalam format DateTime
    - waktu: Waktu absensi dalam format string (untuk kompatibilitas)
    - hari: Hari absensi dalam format string (untuk kompatibilitas)
    - status: Status absensi (Hadir, Terlambat, dll)
    - keterangan: Keterangan tambahan
    - foto_masuk: Foto karyawan saat absen masuk
    - foto_keluar: Foto karyawan saat absen keluar
    - alamat: Lokasi saat absen masuk
    - alamat_keluar: Lokasi saat absen keluar
    - latitude: Latitude lokasi absen masuk
    - longitude: Longitude lokasi absen masuk
    - uang_makan: Status uang makan (sudah diberikan atau belum)
    """
    __tablename__ = "absensi"

    id = Column(Integer, primary_key=True)  # ID unik untuk setiap record absensi
    karyawan_id = Column(Integer, ForeignKey("karyawan.id"))  # ID karyawan yang melakukan absensi
    tanggal = Column(DateTime, default=datetime.now)  # Tanggal absensi, default hari ini
    jam_masuk = Column(DateTime)  # Waktu absen masuk dalam format DateTime
    jam_keluar = Column(DateTime)  # Waktu absen keluar dalam format DateTime
    waktu = Column(String(20), nullable=True)  # Waktu absensi dalam format string (untuk kompatibilitas)
    hari = Column(String(20), nullable=True)  # Hari absensi dalam format string (untuk kompatibilitas)
    status = Column(String(20))  # Status absensi: Hadir, Terlambat, dll
    keterangan = Column(String(200), nullable=True)  # Keterangan tambahan jika diperlukan
    foto_masuk = Column(LargeBinary, nullable=True)  # Foto karyawan saat absen masuk
    foto_keluar = Column(LargeBinary, nullable=True)  # Foto karyawan saat absen keluar
    alamat = Column(String(255), nullable=True)  # Lokasi saat absen masuk
    alamat_keluar = Column(String(255), nullable=True)  # Lokasi saat absen keluar
    latitude = Column(Float, nullable=True)  # Latitude lokasi absen masuk
    longitude = Column(Float, nullable=True)  # Longitude lokasi absen masuk
    uang_makan = Column(Boolean, default=False)  # Status uang makan (sudah diberikan atau belum)
    uang_transport = Column(Boolean, default=False)  # Status uang transportasi (sudah diberikan atau belum)

    # Relasi ke tabel karyawan
    karyawan = relationship("Karyawan", back_populates="absensi")

class Pengaturan(Base):
    """
    Model untuk menyimpan pengaturan sistem absensi

    Atribut:
    - id: Primary key
    - jam_masuk: Jam masuk kerja (format HH:MM)
    - jam_keluar: Jam keluar kerja (format HH:MM)
    - toleransi_keterlambatan: Toleransi keterlambatan dalam menit
    """
    __tablename__ = "pengaturan"  # Nama tabel di database

    # Definisi kolom-kolom tabel
    id = Column(Integer, primary_key=True)  # ID unik pengaturan
    jam_masuk = Column(String(5))  # Jam masuk kerja (format HH:MM)
    jam_keluar = Column(String(5))  # Jam keluar kerja (format HH:MM)
    toleransi_keterlambatan = Column(Integer)  # Toleransi keterlambatan dalam menit