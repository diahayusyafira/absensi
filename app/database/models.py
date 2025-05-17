# File: app/database/models.py
# Deskripsi: Modul ini berisi definisi model-model database untuk aplikasi absensi karyawan.
#            Model-model ini merepresentasikan tabel-tabel dalam database dan relasi antar tabel.

# Import tipe-tipe kolom dan fungsi-fungsi dari SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey  # Tipe-tipe kolom database
from sqlalchemy.ext.declarative import declarative_base  # Untuk membuat base class model
from sqlalchemy.orm import relationship  # Untuk mendefinisikan relasi antar model
from datetime import datetime, timezone  # Untuk nilai default timestamp dan timezone

# Membuat base class untuk model-model ORM
# Semua model/class yang merepresentasikan tabel database akan mewarisi Base
Base = declarative_base()

class Employee(Base):
    """
    Model untuk tabel karyawan (employees).

    Menyimpan data karyawan termasuk informasi pribadi, departemen, posisi,
    dan data embedding wajah untuk pengenalan wajah.

    Attributes:
        id (int): Primary key, ID unik karyawan
        name (str): Nama lengkap karyawan
        nik (str): Nomor Induk Karyawan, unik untuk setiap karyawan
        email (str): Email karyawan, unik
        password (str): Password karyawan (sebaiknya dalam bentuk hash)
        position (str): Posisi/jabatan karyawan
        department (str): Departemen karyawan
        face_embedding (str): Data embedding wajah untuk pengenalan wajah
        created_at (datetime): Waktu pembuatan record
        updated_at (datetime): Waktu terakhir update record

    Relationships:
        attendances: Relasi one-to-many ke tabel Attendance
    """
    __tablename__ = "employees"  # Nama tabel di database

    # Definisi kolom-kolom tabel
    id = Column(Integer, primary_key=True, index=True)  # Primary key, auto-increment
    name = Column(String(100), nullable=False)  # Nama karyawan, tidak boleh null
    nik = Column(String(20), unique=True, nullable=False)  # NIK, harus unik dan tidak boleh null
    email = Column(String(100), unique=True, nullable=False)  # Email, harus unik dan tidak boleh null
    password = Column(String(100), nullable=False)  # Password karyawan (sebaiknya dalam bentuk hash)
    position = Column(String(100))  # Posisi/jabatan karyawan
    department = Column(String(100))  # Departemen karyawan
    face_embedding = Column(String(1000))  # Data embedding wajah untuk pengenalan wajah
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Waktu pembuatan record (UTC)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))  # Waktu update record (UTC)

    # Definisi relasi
    # Relasi one-to-many ke tabel Attendance (satu karyawan bisa memiliki banyak absensi)
    attendances = relationship("Attendance", back_populates="employee")

class Attendance(Base):
    """
    Model untuk tabel absensi (attendances).

    Menyimpan data absensi karyawan termasuk waktu check-in, check-out,
    lokasi, dan status kehadiran.

    Attributes:
        id (int): Primary key, ID unik absensi
        employee_id (int): Foreign key ke tabel employees
        check_in_time (datetime): Waktu absen masuk
        check_out_time (datetime): Waktu absen keluar
        latitude (float): Koordinat latitude lokasi absen
        longitude (float): Koordinat longitude lokasi absen
        location_address (str): Alamat lokasi absen
        status (str): Status kehadiran (Present, Late, Absent)
        created_at (datetime): Waktu pembuatan record

    Relationships:
        employee: Relasi many-to-one ke tabel Employee
    """
    __tablename__ = "attendances"  # Nama tabel di database

    # Definisi kolom-kolom tabel
    id = Column(Integer, primary_key=True, index=True)  # Primary key, auto-increment
    employee_id = Column(Integer, ForeignKey("employees.id"))  # Foreign key ke tabel employees
    check_in_time = Column(DateTime)  # Waktu absen masuk
    check_out_time = Column(DateTime)  # Waktu absen keluar
    latitude = Column(Float)  # Koordinat latitude lokasi absen
    longitude = Column(Float)  # Koordinat longitude lokasi absen
    location_address = Column(String(255))  # Alamat lokasi absen
    status = Column(String(20))  # Status kehadiran (Present, Late, Absent)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Waktu pembuatan record (UTC)

    # Definisi relasi
    # Relasi many-to-one ke tabel Employee (banyak absensi bisa dimiliki oleh satu karyawan)
    employee = relationship("Employee", back_populates="attendances")

class Admin(Base):
    """
    Model untuk tabel admin (admins).

    Menyimpan data admin yang mengelola sistem absensi.

    Attributes:
        id (int): Primary key, ID unik admin
        username (str): Username admin, unik
        password (str): Password admin (sebaiknya dalam bentuk hash)
        email (str): Email admin, unik
        is_active (bool): Status aktif admin
        created_at (datetime): Waktu pembuatan record
        updated_at (datetime): Waktu terakhir update record
    """
    __tablename__ = "admins"  # Nama tabel di database

    # Definisi kolom-kolom tabel
    id = Column(Integer, primary_key=True, index=True)  # Primary key, auto-increment
    username = Column(String(100), unique=True, nullable=False)  # Username admin, harus unik
    password = Column(String(100), nullable=False)  # Password admin (sebaiknya dalam bentuk hash)
    email = Column(String(100), unique=True, nullable=False)  # Email admin, harus unik
    is_active = Column(Boolean, default=True)  # Status aktif admin, default True
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Waktu pembuatan record (UTC)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))  # Waktu update record (UTC)