# Import library FastAPI untuk membuat API
from fastapi import FastAPI, Request, Form, HTTPException, Depends, File, UploadFile
# Import StaticFiles untuk menyajikan file statis (CSS, JS, gambar)
from fastapi.staticfiles import StaticFiles
# Import Jinja2Templates untuk merender template HTML
from fastapi.templating import Jinja2Templates
# Import CORSMiddleware untuk menangani Cross-Origin Resource Sharing
from fastapi.middleware.cors import CORSMiddleware
# Import berbagai jenis response dari FastAPI
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse, FileResponse
# Import untuk autentikasi HTTP Basic
from fastapi.security import HTTPBasic, HTTPBasicCredentials
# Import Session dari SQLAlchemy untuk interaksi dengan database
from sqlalchemy.orm import Session
# Import fungsi-fungsi database dari modul database.py
from database import engine, get_db, init_db
# Import model-model database dari modul models.py
from models import Base, Karyawan, Absensi, Pengaturan, FaceEncoding
# Import secrets untuk keamanan
import secrets
# Import datetime untuk manipulasi tanggal dan waktu
from datetime import datetime, timedelta
# Import logging untuk pencatatan log
import logging
# Import OpenCV untuk pemrosesan gambar dan deteksi wajah
import cv2
# Import numpy untuk operasi array dan matriks
import numpy as np
# Import PIL untuk manipulasi gambar
from PIL import Image
# Import io untuk operasi input/output
import io
# Import json untuk manipulasi data JSON
import json
# Import base64 untuk encoding/decoding data
import base64
# Import uvicorn untuk menjalankan server
import uvicorn
# Import face_recognition untuk pengenalan wajah
import face_recognition

# Konfigurasi logging untuk mencatat aktivitas aplikasi
logging.basicConfig(
    level=logging.DEBUG,  # Level logging: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Format pesan log
)
logger = logging.getLogger(__name__)  # Membuat logger untuk modul ini

# Inisialisasi database dan membuat tabel jika belum ada
try:
    # Pastikan Base memiliki semua model yang diperlukan
    from models import Karyawan, Absensi, Pengaturan, FaceEncoding
    logger.info("Models imported successfully")

    # Membuat tabel berdasarkan model yang telah didefinisikan
    Base.metadata.create_all(bind=engine)  # Membuat tabel di database
    logger.info("Database tables created/verified successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}", exc_info=True)
    raise  # Raise exception jika terjadi error

# Menggunakan library face_recognition untuk deteksi dan pengenalan wajah
# Library ini menggunakan model deep learning (CNN) untuk deteksi dan pengenalan wajah

# Membuat instance aplikasi FastAPI
app = FastAPI(title="Sistem Absensi Karyawan PT Matura Jaya")

# Konfigurasi CORS (Cross-Origin Resource Sharing) middleware
# Ini memungkinkan aplikasi frontend di domain berbeda mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mengizinkan semua origin (domain)
    allow_credentials=True,  # Mengizinkan credentials (cookies, auth headers)
    allow_methods=["*"],  # Mengizinkan semua HTTP methods (GET, POST, dll)
    allow_headers=["*"],  # Mengizinkan semua HTTP headers
)

# Menyajikan file statis (CSS, JavaScript, gambar) dari direktori "static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Endpoint untuk favicon.ico
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Endpoint untuk menyajikan favicon.ico dari root directory

    Returns:
        FileResponse: File favicon.ico
    """
    return FileResponse("favicon.ico")

# Konfigurasi template engine Jinja2 untuk merender halaman HTML
templates = Jinja2Templates(directory="templates")

# Mendaftarkan filter b64encode untuk template Jinja2
# Filter ini digunakan untuk mengkonversi data biner (foto) ke format base64 untuk ditampilkan di HTML
def b64encode_filter(data):
    """
    Mengkonversi data biner ke format base64 string

    Args:
        data: Data biner yang akan dikonversi

    Returns:
        String base64 dari data biner, atau string kosong jika data kosong
    """
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''

# Mendaftarkan filter ke template engine
templates.env.filters['b64encode'] = b64encode_filter

# Kredensial admin untuk login
# Dalam aplikasi produksi, ini seharusnya disimpan dengan aman (misalnya di environment variables)
ADMIN_USERNAME = "admin"  # Username admin
ADMIN_PASSWORD = "adminmatura"  # Password admin

@app.get("/")
async def root():
    """
    Endpoint untuk halaman utama aplikasi

    Returns:
        dict: Pesan selamat datang
    """
    return {"message": "Welcome to PT Matura Jaya Attendance System"}

@app.get("/admin/login")
async def admin_login(request: Request):
    """
    Endpoint untuk menampilkan halaman login admin

    Args:
        request (Request): Request object dari FastAPI

    Returns:
        TemplateResponse: Halaman login admin
    """
    return templates.TemplateResponse("admin-login.html", {"request": request})

@app.post("/admin/login")
async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Endpoint untuk memproses login admin

    Args:
        request (Request): Request object dari FastAPI
        username (str): Username yang diinput user
        password (str): Password yang diinput user

    Returns:
        RedirectResponse: Redirect ke dashboard jika login berhasil
        TemplateResponse: Kembali ke halaman login dengan pesan error jika gagal
    """
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Login berhasil, redirect ke dashboard
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    else:
        # Login gagal, tampilkan pesan error
        return templates.TemplateResponse(
            "admin-login.html",
            {"request": request, "error": "Username atau password salah"}
        )

@app.get("/admin/dashboard")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint untuk menampilkan dashboard admin dengan ringkasan data absensi hari ini

    Args:
        request (Request): Request object dari FastAPI
        db (Session): Session database dari dependency

    Returns:
        TemplateResponse: Halaman dashboard admin dengan data absensi
    """
    try:
        # Mendapatkan total jumlah karyawan
        total_karyawan = db.query(Karyawan).count()  # Hitung jumlah karyawan
        logger.debug(f"Total karyawan: {total_karyawan}")

        # Mendapatkan data absensi hari ini
        today = datetime.now().date()  # Tanggal hari ini
        absensi_hari_ini = db.query(Absensi).filter(
            Absensi.tanggal >= today  # Filter absensi untuk hari ini
        ).all()
        logger.debug(f"Total absensi hari ini: {len(absensi_hari_ini)}")

        # Menghitung jumlah karyawan berdasarkan status kehadiran
        hadir = len([a for a in absensi_hari_ini if a.status == "Hadir"])  # Jumlah karyawan hadir
        terlambat = len([a for a in absensi_hari_ini if a.status == "Terlambat"])  # Jumlah karyawan terlambat
        tidak_hadir = total_karyawan - (hadir + terlambat)  # Jumlah karyawan tidak hadir

        logger.debug(f"Hadir: {hadir}, Terlambat: {terlambat}, Tidak Hadir: {tidak_hadir}")

        # Render template dashboard dengan data
        return templates.TemplateResponse(
            "admin-dashboard.html",
            {
                "request": request,
                "total_karyawan": total_karyawan,
                "hadir": hadir,
                "terlambat": terlambat,
                "tidak_hadir": tidak_hadir
            }
        )
    except Exception as e:
        # Tangani error jika terjadi
        logger.error(f"Error in admin_dashboard: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin-dashboard.html",
            {
                "request": request,
                "error": f"Terjadi kesalahan saat memuat data: {str(e)}",
                "total_karyawan": 0,
                "hadir": 0,
                "terlambat": 0,
                "tidak_hadir": 0
            }
        )

@app.get("/admin/datakaryawan")
async def admin_datakaryawan(request: Request, db: Session = Depends(get_db)):
    try:
        logger.debug("Starting to fetch karyawan data")
        karyawan_list = db.query(Karyawan).order_by(Karyawan.id.asc()).all()
        logger.debug(f"Successfully fetched {len(karyawan_list)} karyawan records")

        # Log each karyawan's data for debugging
        for karyawan in karyawan_list:
            logger.debug(f"Karyawan data being sent to template:")
            logger.debug(f"  ID: {karyawan.id}")
            logger.debug(f"  Nama: {karyawan.nama}")
            logger.debug(f"  Email: {karyawan.email}")
            logger.debug(f"  Status: {karyawan.status}")
            logger.debug(f"  Has Foto: {bool(karyawan.foto)}")

        template_data = {
            "request": request,
            "karyawan_list": karyawan_list,
            "b64encode": lambda x: base64.b64encode(x).decode('utf-8') if x else ''
        }

        logger.debug(f"Rendering template with {len(karyawan_list)} karyawan")
        return templates.TemplateResponse("admin-datakaryawan.html", template_data)
    except Exception as e:
        logger.error(f"Error in admin_datakaryawan: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin-datakaryawan.html",
            {
                "request": request,
                "error": f"Terjadi kesalahan saat memuat data karyawan: {str(e)}",
                "karyawan_list": []
            }
        )

@app.get("/admin/datakaryawan/tambah")
async def admin_tambahkaryawan(request: Request):
    try:
        return templates.TemplateResponse("admin-tambahkaryawan.html", {"request": request})
    except Exception as e:
        logger.error(f"Error in admin_tambahkaryawan: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin-tambahkaryawan.html",
            {
                "request": request,
                "error": f"Terjadi kesalahan saat memuat halaman: {str(e)}"
            }
        )

@app.post("/admin/tambah_karyawan")
async def tambah_karyawan(
    request: Request,  # Request object dari FastAPI
    nama: str = Form(...),  # Nama karyawan
    email: str = Form(...),  # Email karyawan
    no_telepon: str = Form(...),  # Nomor telepon karyawan
    jabatan: str = Form(...),  # Jabatan karyawan
    departemen: str = Form(...),  # Departemen karyawan
    alamat: str = Form(...),  # Alamat karyawan
    tanggal_bergabung: str = Form(...),  # Tanggal bergabung karyawan (format YYYY-MM-DD)
    foto: UploadFile = File(None),  # Foto karyawan (opsional)
    db: Session = Depends(get_db)  # Session database
):
    """
    Endpoint untuk menambahkan data karyawan baru

    Args:
        request (Request): Request object dari FastAPI
        nama (str): Nama karyawan
        email (str): Email karyawan
        no_telepon (str): Nomor telepon karyawan
        jabatan (str): Jabatan karyawan
        departemen (str): Departemen karyawan
        alamat (str): Alamat karyawan
        tanggal_bergabung (str): Tanggal bergabung karyawan (format YYYY-MM-DD)
        foto (UploadFile, optional): Foto karyawan
        db (Session): Session database

    Returns:
        JSONResponse: Response dengan status dan pesan hasil operasi
    """
    try:
        # Log data yang diterima
        logging.info("Received data for new karyawan:")
        logging.info(f"nama: {nama}")
        logging.info(f"email: {email}")
        logging.info(f"no_telepon: {no_telepon}")
        logging.info(f"jabatan: {jabatan}")
        logging.info(f"departemen: {departemen}")
        logging.info(f"alamat: {alamat}")
        logging.info(f"tanggal_bergabung: {tanggal_bergabung}")

        # Cek apakah email sudah terdaftar
        existing_email = db.query(Karyawan).filter(Karyawan.email == email.lower().strip()).first()
        if existing_email:
            # Email sudah terdaftar, kembalikan error
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"Email {email} sudah terdaftar. Silakan gunakan email lain."
                }
            )

        # Baca dan proses foto jika disediakan
        foto_data = None
        if foto:
            # Validasi tipe file
            if not foto.content_type.startswith('image/'):
                # Format file tidak didukung
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "Format file tidak didukung. Harap unggah file gambar (JPG, JPEG, PNG)"
                    }
                )

            # Baca konten file
            foto_data = await foto.read()

            # Validasi ukuran file (batas 2MB)
            if len(foto_data) > 2 * 1024 * 1024:
                # Ukuran file terlalu besar
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "Ukuran file terlalu besar. Maksimal 2MB"
                    }
                )

        # Buat objek Karyawan baru
        try:
            new_karyawan = Karyawan(
                nama=nama,
                email=email.lower().strip(),
                no_telepon=no_telepon,
                jabatan=jabatan,
                departemen=departemen,
                alamat=alamat,
                tanggal_bergabung=datetime.strptime(tanggal_bergabung, "%Y-%m-%d"),
                foto=foto_data,
                status=True  # Set status ke aktif secara default
            )
            logging.info("Created Karyawan object successfully")

            # Tambahkan ke database
            db.add(new_karyawan)  # Tambahkan objek ke session
            db.commit()  # Simpan perubahan ke database
            db.refresh(new_karyawan)  # Refresh objek dengan data dari database
            logging.info("Committed to database successfully")

            # Simpan juga foto ke folder face_data jika ada
            if foto_data:
                try:
                    # Import os jika belum diimpor
                    import os

                    # Pastikan direktori face_data ada
                    FACE_DIR = "face_data"
                    if not os.path.exists(FACE_DIR):
                        os.makedirs(FACE_DIR)
                        logger.info(f"Direktori {FACE_DIR} berhasil dibuat")

                    # Simpan foto ke file
                    img_path = os.path.join(FACE_DIR, f"employee_{new_karyawan.id}.jpg")

                    # Konversi bytes ke gambar dan simpan
                    image = Image.open(io.BytesIO(foto_data))
                    image.save(img_path)

                    logger.info(f"Foto karyawan ID {new_karyawan.id} berhasil disimpan di {img_path}")
                except Exception as e:
                    # Tangani error jika terjadi saat menyimpan file
                    logger.error(f"Error saat menyimpan foto ke folder face_data: {str(e)}")
                    # Tidak perlu mengembalikan error ke client karena foto sudah tersimpan di database

            # Generate dan simpan encoding wajah
            if foto_data:
                try:
                    # Load gambar dari bytes
                    image = face_recognition.load_image_file(io.BytesIO(foto_data))

                    # Deteksi wajah terlebih dahulu
                    face_locations = face_recognition.face_locations(image)
                    logger.info(f"Jumlah wajah terdeteksi dalam foto karyawan baru: {len(face_locations)}")

                    if face_locations:
                        # Dapatkan encoding wajah
                        encodings = face_recognition.face_encodings(image, face_locations)

                        if encodings:
                            # Jika wajah terdeteksi, simpan encoding
                            face_encoding_array = encodings[0]

                            # Buat objek FaceEncoding baru
                            new_encoding = FaceEncoding(karyawan_id=new_karyawan.id)

                            # Gunakan metode set_encoding_array untuk menyimpan encoding sebagai JSON
                            new_encoding.set_encoding_array(face_encoding_array)

                            # Tambahkan ke database
                            db.add(new_encoding)
                            db.commit()

                            logger.info(f"Encoding wajah berhasil disimpan untuk karyawan baru (ID: {new_karyawan.id})")
                        else:
                            logger.warning(f"Tidak dapat mengekstrak encoding wajah untuk karyawan baru (ID: {new_karyawan.id})")
                    else:
                        logger.warning(f"Tidak ada wajah yang terdeteksi dalam foto karyawan baru (ID: {new_karyawan.id})")
                except Exception as e:
                    logger.error(f"Error saat memproses encoding wajah: {str(e)}")
                    # Lanjutkan meskipun ada error dalam pemrosesan wajah

            # Kembalikan response sukses
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Data karyawan berhasil ditambahkan",
                    "data": {
                        "id": new_karyawan.id,
                        "nama": new_karyawan.nama,
                        "email": new_karyawan.email
                    }
                }
            )

        except Exception as e:
            # Rollback jika terjadi error saat menyimpan data
            db.rollback()  # Batalkan semua perubahan
            logging.error(f"Error creating karyawan: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Terjadi kesalahan saat menyimpan data: {str(e)}"
                }
            )

    except Exception as e:
        # Tangani error umum
        logging.error(f"Error in tambah_karyawan: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Terjadi kesalahan: {str(e)}"
            }
        )

@app.put("/admin/datakaryawan/{karyawan_id}")
async def update_karyawan(
    karyawan_id: int,  # ID karyawan yang akan diupdate
    request: Request,  # Request object dari FastAPI
    nama: str = Form(...),  # Nama karyawan
    email: str = Form(...),  # Email karyawan
    no_telepon: str = Form(...),  # Nomor telepon karyawan
    jabatan: str = Form(...),  # Jabatan karyawan
    departemen: str = Form(...),  # Departemen karyawan
    alamat: str = Form(...),  # Alamat karyawan
    tanggal_bergabung: str = Form(...),  # Tanggal bergabung karyawan (format YYYY-MM-DD)
    db: Session = Depends(get_db)  # Session database
):
    """
    Endpoint untuk mengupdate data karyawan yang sudah ada

    Args:
        karyawan_id (int): ID karyawan yang akan diupdate
        request (Request): Request object dari FastAPI
        nama (str): Nama karyawan
        email (str): Email karyawan
        no_telepon (str): Nomor telepon karyawan
        jabatan (str): Jabatan karyawan
        departemen (str): Departemen karyawan
        alamat (str): Alamat karyawan
        tanggal_bergabung (str): Tanggal bergabung karyawan (format YYYY-MM-DD)
        db (Session): Session database

    Returns:
        JSONResponse: Response dengan status dan pesan hasil operasi
    """
    try:
        # Log data yang diterima
        logging.info(f"Updating karyawan {karyawan_id} with data:")
        logging.info(f"nama: {nama}")
        logging.info(f"email: {email}")
        logging.info(f"no_telepon: {no_telepon}")
        logging.info(f"jabatan: {jabatan}")
        logging.info(f"departemen: {departemen}")
        logging.info(f"alamat: {alamat}")
        logging.info(f"tanggal_bergabung: {tanggal_bergabung}")

        # Dapatkan data karyawan yang ada
        karyawan = db.query(Karyawan).filter(Karyawan.id == karyawan_id).first()
        if not karyawan:
            # Karyawan tidak ditemukan
            logging.error(f"Karyawan with id {karyawan_id} not found")
            return JSONResponse(
                status_code=404,
                content={"message": "Karyawan tidak ditemukan"}
            )

        # Cek apakah email diubah dan email baru sudah terdaftar
        if email.lower().strip() != karyawan.email and db.query(Karyawan).filter(Karyawan.email == email.lower().strip()).first():
            # Email sudah terdaftar oleh karyawan lain
            logging.error(f"Email {email} already exists")
            return JSONResponse(
                status_code=400,
                content={"message": "Email sudah terdaftar"}
            )

        # Update data karyawan
        karyawan.nama = nama
        karyawan.email = email.lower().strip()
        karyawan.no_telepon = no_telepon
        karyawan.jabatan = jabatan
        karyawan.departemen = departemen
        karyawan.alamat = alamat
        karyawan.tanggal_bergabung = datetime.strptime(tanggal_bergabung, "%Y-%m-%d")

        try:
            # Simpan perubahan ke database
            db.commit()  # Simpan perubahan ke database
            logging.info(f"Successfully updated karyawan {karyawan_id}")
            return JSONResponse(content={"message": "Data berhasil diperbarui"})
        except Exception as e:
            # Rollback jika terjadi error saat menyimpan data
            db.rollback()  # Batalkan semua perubahan
            logging.error(f"Error updating karyawan: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=400,
                content={"message": f"Terjadi kesalahan saat memperbarui data: {str(e)}"}
            )

    except Exception as e:
        # Tangani error umum
        logging.error(f"Unexpected error in update_karyawan: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "Terjadi kesalahan yang tidak terduga"}
        )

@app.get("/admin/datakaryawan/{karyawan_id}")
async def get_karyawan(karyawan_id: int, db: Session = Depends(get_db)):
    """
    Endpoint untuk mendapatkan data karyawan berdasarkan ID

    Args:
        karyawan_id (int): ID karyawan yang akan diambil
        db (Session): Session database

    Returns:
        dict: Data karyawan

    Raises:
        HTTPException: Jika karyawan tidak ditemukan
    """
    # Cari karyawan berdasarkan ID
    karyawan = db.query(Karyawan).filter(Karyawan.id == karyawan_id).first()
    if not karyawan:
        # Karyawan tidak ditemukan, raise exception
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")

    # Format tanggal bergabung ke string YYYY-MM-DD untuk form input date
    tanggal_bergabung = karyawan.tanggal_bergabung.strftime("%Y-%m-%d") if karyawan.tanggal_bergabung else None

    # Kembalikan data karyawan dalam format JSON
    return {
        "id": karyawan.id,
        "nama": karyawan.nama,
        "email": karyawan.email,
        "no_telepon": karyawan.no_telepon,
        "jabatan": karyawan.jabatan,
        "departemen": karyawan.departemen,
        "alamat": karyawan.alamat,
        "tanggal_bergabung": tanggal_bergabung,
        "status": karyawan.status
    }

@app.delete("/admin/datakaryawan/{karyawan_id}")
async def delete_karyawan(karyawan_id: int, db: Session = Depends(get_db)):
    """
    Endpoint untuk menghapus data karyawan

    Args:
        karyawan_id (int): ID karyawan yang akan dihapus
        db (Session): Session database

    Returns:
        dict: Status hasil operasi

    Raises:
        HTTPException: Jika karyawan tidak ditemukan
    """
    # Cari karyawan berdasarkan ID
    karyawan = db.query(Karyawan).filter(Karyawan.id == karyawan_id).first()
    if not karyawan:
        # Karyawan tidak ditemukan, raise exception
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")

    # Hapus karyawan dari database
    db.delete(karyawan)  # Hapus objek dari database
    db.commit()  # Simpan perubahan ke database
    return {"status": "success"}

@app.get("/admin/laporanabsensi")
async def admin_laporanabsensi(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint untuk menampilkan laporan absensi karyawan

    Args:
        request (Request): Request object dari FastAPI
        db (Session): Session database dari dependency

    Returns:
        TemplateResponse: Halaman laporan absensi dengan data absensi
    """
    try:
        # Log the start of the function
        logger.info("Fetching attendance data for admin report")

        # Ambil semua data absensi dari database
        absensi_list = db.query(Absensi).all()  # Dapatkan semua data absensi
        logger.info(f"Retrieved {len(absensi_list)} attendance records")

        # Log some details about the records for debugging
        for absensi in absensi_list:
            logger.debug(f"Attendance ID: {absensi.id}, Employee: {absensi.karyawan.nama if absensi.karyawan else 'Unknown'}")
            logger.debug(f"  Date: {absensi.tanggal}")
            logger.debug(f"  Check-in time: {absensi.jam_masuk}")
            logger.debug(f"  Check-out time: {absensi.jam_keluar}")
            logger.debug(f"  Check-in location: {absensi.alamat}")
            logger.debug(f"  Check-out location: {absensi.alamat_keluar}")
            logger.debug(f"  Has check-in photo: {bool(absensi.foto_masuk)}")
            logger.debug(f"  Has check-out photo: {bool(absensi.foto_keluar)}")

        # Render template with attendance data
        logger.info("Rendering admin-laporanabsensi.html template")
        return templates.TemplateResponse(
            "admin-laporanabsensi.html",
            {"request": request, "absensi_list": absensi_list}
        )
    except Exception as e:
        # Log any errors that occur
        logger.error(f"Error in admin_laporanabsensi: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "admin-laporanabsensi.html",
            {
                "request": request,
                "error": f"Terjadi kesalahan saat memuat data absensi: {str(e)}",
                "absensi_list": []
            }
        )

@app.get("/admin/pengaturan")
async def admin_pengaturan(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint untuk menampilkan halaman pengaturan sistem absensi

    Args:
        request (Request): Request object dari FastAPI
        db (Session): Session database dari dependency

    Returns:
        TemplateResponse: Halaman pengaturan dengan data pengaturan saat ini
    """
    # Ambil data pengaturan dari database
    pengaturan = db.query(Pengaturan).first()  # Dapatkan pengaturan pertama

    # Render template dengan data pengaturan
    return templates.TemplateResponse(
        "admin-pengaturan.html",
        {"request": request, "pengaturan": pengaturan}
    )

@app.post("/admin/pengaturan")
async def update_pengaturan(
    request: Request,  # Request object dari FastAPI
    jam_masuk: str = Form(...),  # Jam masuk kerja (format HH:MM)
    jam_keluar: str = Form(...),  # Jam keluar kerja (format HH:MM)
    toleransi_keterlambatan: int = Form(...),  # Toleransi keterlambatan dalam menit
    db: Session = Depends(get_db)  # Session database
):
    """
    Endpoint untuk mengupdate pengaturan sistem absensi

    Args:
        request (Request): Request object dari FastAPI
        jam_masuk (str): Jam masuk kerja (format HH:MM)
        jam_keluar (str): Jam keluar kerja (format HH:MM)
        toleransi_keterlambatan (int): Toleransi keterlambatan dalam menit
        db (Session): Session database

    Returns:
        RedirectResponse: Redirect kembali ke halaman pengaturan
    """
    # Cari pengaturan yang ada atau buat baru jika belum ada
    pengaturan = db.query(Pengaturan).first()
    if not pengaturan:
        pengaturan = Pengaturan()  # Buat objek pengaturan baru jika belum ada

    # Update data pengaturan
    pengaturan.jam_masuk = jam_masuk
    pengaturan.jam_keluar = jam_keluar
    pengaturan.toleransi_keterlambatan = toleransi_keterlambatan

    # Simpan ke database
    db.add(pengaturan)  # Tambahkan objek ke session
    db.commit()  # Simpan perubahan ke database

    # Redirect kembali ke halaman pengaturan
    return RedirectResponse(url="/admin/pengaturan", status_code=303)

@app.get("/admin/logout")
async def admin_logout():
    """
    Endpoint untuk logout dari halaman admin

    Returns:
        RedirectResponse: Redirect ke halaman login admin
    """
    # Redirect ke halaman login admin
    return RedirectResponse(url="/admin/login", status_code=303)

@app.post("/admin/datakaryawan/{karyawan_id}/upload-foto")
async def upload_foto(
    karyawan_id: int,  # ID karyawan yang akan diupdate fotonya
    foto: UploadFile = File(...),  # File foto yang diupload
    db: Session = Depends(get_db)  # Session database
):
    """
    Endpoint untuk mengupload foto karyawan dan menghasilkan encoding wajah

    Args:
        karyawan_id (int): ID karyawan yang akan diupdate fotonya
        foto (UploadFile): File foto yang diupload
        db (Session): Session database

    Returns:
        JSONResponse: Response dengan status dan pesan hasil operasi
    """
    try:
        # Cari karyawan berdasarkan ID
        karyawan = db.query(Karyawan).filter(Karyawan.id == karyawan_id).first()
        if not karyawan:
            # Karyawan tidak ditemukan
            return JSONResponse(status_code=404, content={"message": "Karyawan tidak ditemukan"})

        # Validasi tipe file
        if not foto.content_type.startswith('image/'):
            # Format file tidak didukung
            return JSONResponse(status_code=400, content={"message": "Format file tidak didukung. Harap unggah file gambar (JPG, JPEG, PNG)"})

        # Baca konten file
        foto_data = await foto.read()

        # Validasi ukuran file (batas 2MB)
        if len(foto_data) > 2 * 1024 * 1024:
            # Ukuran file terlalu besar
            return JSONResponse(status_code=400, content={"message": "Ukuran file terlalu besar. Maksimal 2MB"})

        # Update foto karyawan di database
        karyawan.foto = foto_data  # Simpan data foto ke kolom foto
        db.commit()  # Simpan perubahan ke database

        # Simpan juga foto ke folder face_data
        try:
            # Import os jika belum diimpor
            import os

            # Pastikan direktori face_data ada
            FACE_DIR = "face_data"
            if not os.path.exists(FACE_DIR):
                os.makedirs(FACE_DIR)
                logger.info(f"Direktori {FACE_DIR} berhasil dibuat")

            # Simpan foto ke file
            img_path = os.path.join(FACE_DIR, f"employee_{karyawan_id}.jpg")

            # Konversi bytes ke gambar dan simpan
            image = Image.open(io.BytesIO(foto_data))
            image.save(img_path)

            logger.info(f"Foto karyawan ID {karyawan_id} berhasil disimpan di {img_path}")
        except Exception as e:
            # Tangani error jika terjadi saat menyimpan file
            logger.error(f"Error saat menyimpan foto ke folder face_data: {str(e)}")
            # Tidak perlu mengembalikan error ke client karena foto sudah tersimpan di database

        # Generate encoding wajah dari foto
        try:
            # Load gambar dari bytes
            image = face_recognition.load_image_file(io.BytesIO(foto_data))

            # Deteksi wajah terlebih dahulu
            face_locations = face_recognition.face_locations(image)
            logger.info(f"Jumlah wajah terdeteksi dalam foto update: {len(face_locations)}")

            if not face_locations:
                # Wajah tidak terdeteksi pada foto
                logger.warning(f"Tidak ada wajah yang terdeteksi dalam foto update untuk karyawan ID: {karyawan_id}")
                return JSONResponse(
                    status_code=400,
                    content={"message": "Wajah tidak terdeteksi pada foto yang diupload. Silakan upload foto yang jelas dengan pencahayaan yang baik."}
                )

            # Dapatkan encoding wajah
            encodings = face_recognition.face_encodings(image, face_locations)

            if not encodings:
                # Tidak dapat mengekstrak encoding wajah
                logger.warning(f"Tidak dapat mengekstrak encoding wajah dari foto update untuk karyawan ID: {karyawan_id}")
                return JSONResponse(
                    status_code=400,
                    content={"message": "Tidak dapat mengekstrak fitur wajah. Coba lagi dengan foto yang lebih jelas."}
                )

            # Jika wajah terdeteksi, simpan encoding
            face_encoding_array = encodings[0]
            logger.info(f"Berhasil mendapatkan encoding wajah dari foto update untuk karyawan ID: {karyawan_id}")

            # Cek apakah encoding sudah ada
            face_encoding_obj = db.query(FaceEncoding).filter(FaceEncoding.karyawan_id == karyawan_id).first()

            if face_encoding_obj:
                # Update encoding yang sudah ada menggunakan metode set_encoding_array
                logger.info(f"Mengupdate encoding wajah yang sudah ada untuk karyawan ID: {karyawan_id}")
                face_encoding_obj.set_encoding_array(face_encoding_array)
            else:
                # Buat encoding baru
                logger.info(f"Membuat encoding wajah baru untuk karyawan ID: {karyawan_id}")
                new_encoding = FaceEncoding(karyawan_id=karyawan_id)
                new_encoding.set_encoding_array(face_encoding_array)
                db.add(new_encoding)  # Tambahkan encoding ke session

            # Simpan perubahan ke database
            db.commit()  # Simpan perubahan ke database
            logger.info(f"Encoding wajah berhasil disimpan untuk karyawan ID: {karyawan_id}")
        except Exception as e:
            # Tangani error jika terjadi
            logger.error(f"Error saat memproses encoding wajah: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"message": f"Terjadi kesalahan saat memproses wajah: {str(e)}"}
            )

        # Kembalikan response sukses
        return JSONResponse(status_code=200, content={"message": "Foto dan encoding wajah berhasil diupdate"})

    except Exception as e:
        # Tangani error jika terjadi
        db.rollback()  # Batalkan semua perubahan
        return JSONResponse(status_code=500, content={"message": f"Terjadi kesalahan saat mengupdate foto: {str(e)}"})

@app.post("/absensi/verify-face")
async def verify_face(
    foto: UploadFile = File(...),  # File foto yang diupload
    db: Session = Depends(get_db)  # Session database (tidak digunakan dalam fungsi ini)
):
    """
    Endpoint untuk memverifikasi apakah foto mengandung wajah yang dapat dideteksi

    Args:
        foto (UploadFile): File foto yang akan diverifikasi
        db (Session): Session database (tidak digunakan dalam fungsi ini)

    Returns:
        JSONResponse: Response dengan status dan pesan hasil verifikasi
    """
    try:
        # Baca dan proses gambar yang diupload
        contents = await foto.read()  # Baca konten file
        nparr = np.frombuffer(contents, np.uint8)  # Konversi ke numpy array
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode gambar

        # Konversi ke RGB untuk face_recognition (face_recognition menggunakan format RGB)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Deteksi wajah menggunakan face_recognition (berbasis CNN)
        # face_recognition menggunakan model deep learning (ResNet) untuk deteksi wajah
        # yang jauh lebih akurat dan fleksibel terhadap variasi pose, jarak, dan pencahayaan
        face_locations = face_recognition.face_locations(rgb_img, model="cnn")

        # Cek apakah ada wajah yang terdeteksi
        if len(face_locations) == 0:
            # Tidak ada wajah terdeteksi
            return JSONResponse(
                status_code=400,
                content={"message": "Tidak ada wajah terdeteksi dalam foto"}
            )

        # Cek apakah ada lebih dari satu wajah
        if len(face_locations) > 1:
            # Lebih dari satu wajah terdeteksi
            return JSONResponse(
                status_code=400,
                content={"message": "Terdeteksi lebih dari satu wajah dalam foto"}
            )

        # Untuk saat ini, hanya verifikasi bahwa wajah terdeteksi
        # Dalam aplikasi nyata, Anda mungkin ingin mengimplementasikan pengenalan wajah di sini
        return JSONResponse(content={
            "message": "Wajah terdeteksi",
            "status": "success"
        })

    except Exception as e:
        # Tangani error jika terjadi
        logging.error(f"Error verifying face: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": f"Terjadi kesalahan saat verifikasi wajah: {str(e)}"}
        )

@app.get("/employee-login", response_class=HTMLResponse)
async def employee_login(request: Request):
    """
    Endpoint untuk menampilkan halaman login karyawan

    Args:
        request (Request): Request object dari FastAPI

    Returns:
        TemplateResponse: Halaman login karyawan
    """
    # Render template halaman login karyawan
    return templates.TemplateResponse("employee-login.html", {"request": request})

@app.post("/employee-login")
async def employee_login_post(
    request: Request,  # Request object dari FastAPI
    imageData: str = Form(...),  # Data gambar dalam format base64
    db: Session = Depends(get_db)  # Session database
):
    """
    Endpoint untuk memproses login karyawan menggunakan pengenalan wajah

    Args:
        request (Request): Request object dari FastAPI
        imageData (str): Data gambar dalam format base64
        db (Session): Session database

    Returns:
        RedirectResponse: Redirect ke halaman absensi jika login berhasil
        TemplateResponse: Kembali ke halaman login dengan pesan error jika gagal
    """
    # Tambahkan logging untuk debugging
    logger.info("Memproses login karyawan dengan pengenalan wajah")

    # Decode gambar dari format base64
    try:
        header, encoded = imageData.split(",", 1)  # Pisahkan header dan data
        img_bytes = base64.b64decode(encoded)  # Decode base64 menjadi bytes
        nparr = np.frombuffer(img_bytes, np.uint8)  # Konversi ke numpy array
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Decode gambar

        # Verifikasi kualitas gambar
        if img is None or img.size == 0:
            logger.error("Gambar tidak valid atau kosong")
            return templates.TemplateResponse(
                "employee-login.html",
                {"request": request, "error": "Gambar tidak valid. Coba lagi dengan pencahayaan yang lebih baik!"}
            )

        # Cek ukuran gambar
        height, width, _ = img.shape
        logger.info(f"Ukuran gambar: {width}x{height} piksel")

        # Konversi ke RGB untuk face_recognition
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        logger.info("Berhasil memproses gambar")
    except Exception as e:
        # Gagal memproses gambar
        logger.error(f"Gagal memproses gambar: {str(e)}")
        return templates.TemplateResponse(
            "employee-login.html",
            {"request": request, "error": "Gagal memproses gambar. Coba lagi dengan pencahayaan yang lebih baik!"}
        )

    # Ekstrak encoding wajah dari gambar yang diambil
    try:
        # Deteksi wajah menggunakan model CNN dari face_recognition
        # Model CNN memberikan deteksi yang lebih akurat dan fleksibel terhadap variasi pose dan jarak
        face_locations = face_recognition.face_locations(rgb_img, model="cnn")
        logger.info(f"Jumlah wajah terdeteksi: {len(face_locations)}")

        if not face_locations:
            logger.warning("Tidak ada wajah yang terdeteksi dalam gambar")
            return templates.TemplateResponse(
                "employee-login.html",
                {"request": request, "error": "Wajah tidak terdeteksi. Pastikan wajah terlihat jelas dan coba lagi!"}
            )

        # Dapatkan encoding wajah
        unknown_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        if not unknown_encodings:
            logger.warning("Tidak dapat mengekstrak encoding wajah")
            return templates.TemplateResponse(
                "employee-login.html",
                {"request": request, "error": "Tidak dapat mengekstrak fitur wajah. Coba lagi dengan pencahayaan yang lebih baik!"}
            )

        unknown_encoding = unknown_encodings[0]  # Ambil encoding pertama
        logger.info("Berhasil mendapatkan encoding wajah dari gambar")
    except Exception as e:
        logger.error(f"Error saat ekstraksi encoding wajah: {str(e)}")
        return templates.TemplateResponse(
            "employee-login.html",
            {"request": request, "error": "Gagal memproses wajah. Coba lagi!"}
        )

    # Ambil semua face encoding karyawan dari database
    try:
        # Gunakan toleransi yang lebih tinggi untuk meningkatkan tingkat keberhasilan
        # Nilai default adalah 0.6, semakin tinggi semakin toleran
        # Meningkatkan ke 0.7 untuk deteksi yang lebih fleksibel terhadap jarak dan posisi
        tolerance = 0.7

        karyawan_list = db.query(Karyawan).all()
        logger.info(f"Jumlah karyawan dalam database: {len(karyawan_list)}")

        # Siapkan list untuk menyimpan hasil perbandingan
        match_results = []

        for karyawan in karyawan_list:
            # Cari encoding wajah karyawan
            face_encoding_obj = db.query(FaceEncoding).filter(FaceEncoding.karyawan_id == karyawan.id).first()

            if face_encoding_obj:
                try:
                    # Gunakan metode get_encoding_array() untuk mendapatkan encoding dalam format numpy array
                    import json

                    # Coba parse encoding sebagai JSON
                    try:
                        # Jika encoding disimpan sebagai JSON string
                        known_encoding = np.array(json.loads(face_encoding_obj.encoding))
                        logger.info(f"Berhasil parse encoding sebagai JSON untuk karyawan {karyawan.nama}")
                    except json.JSONDecodeError:
                        # Jika encoding disimpan sebagai bytes
                        known_encoding = np.frombuffer(face_encoding_obj.encoding, dtype=np.float64)
                        logger.info(f"Berhasil parse encoding sebagai bytes untuk karyawan {karyawan.nama}")

                    # Bandingkan encoding wajah
                    face_distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
                    match = face_distance <= tolerance

                    logger.info(f"Perbandingan dengan {karyawan.nama}: jarak={face_distance}, cocok={match}")
                    match_results.append((karyawan, face_distance, match))

                    if match:
                        # Login berhasil, redirect ke halaman absensi dengan ID
                        logger.info(f"Login berhasil untuk karyawan: {karyawan.nama} (ID: {karyawan.id})")
                        response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
                        response.set_cookie("notif_login", f"Selamat datang, {karyawan.nama}!")
                        return response
                except Exception as e:
                    logger.error(f"Error saat membandingkan wajah untuk karyawan {karyawan.nama}: {str(e)}")
            else:
                logger.warning(f"Tidak ada encoding wajah untuk karyawan: {karyawan.nama} (ID: {karyawan.id})")

        # Log hasil perbandingan
        if match_results:
            # Urutkan berdasarkan jarak (terkecil = paling mirip)
            match_results.sort(key=lambda x: x[1])
            best_match = match_results[0]
            logger.info(f"Perbandingan terbaik: {best_match[0].nama}, jarak={best_match[1]}, cocok={best_match[2]}")

            # Jika jarak terbaik cukup dekat tapi masih di atas threshold, coba dengan toleransi yang lebih tinggi
            if best_match[1] <= 0.7:  # Toleransi yang lebih tinggi untuk kasus edge
                logger.info(f"Mencoba dengan toleransi yang lebih tinggi untuk {best_match[0].nama}")
                response = RedirectResponse(url=f"/employee-absensi?id={best_match[0].id}", status_code=303)
                response.set_cookie("notif_login", f"Selamat datang, {best_match[0].nama}!")
                return response
    except Exception as e:
        logger.error(f"Error saat memproses pengenalan wajah: {str(e)}")

    # Jika tidak ada wajah yang cocok
    logger.warning("Tidak ada wajah yang cocok dalam database")
    return templates.TemplateResponse(
        "employee-login.html",
        {"request": request, "error": "Wajah tidak dikenali. Silakan daftar atau coba lagi dengan pencahayaan yang lebih baik!"}
    )

@app.get("/employee-absensi", response_class=HTMLResponse)
async def employee_absensi(request: Request, id: int = None, db: Session = Depends(get_db)):
    """
    Endpoint untuk menampilkan halaman absensi karyawan

    Args:
        request (Request): Request object dari FastAPI
        id (int, optional): ID karyawan
        db (Session): Session database

    Returns:
        RedirectResponse: Redirect ke halaman login jika ID tidak valid
        TemplateResponse: Halaman absensi karyawan
    """
    # Cek apakah ID karyawan disediakan
    if not id:
        # ID tidak disediakan, redirect ke halaman login
        return RedirectResponse(url="/employee-login", status_code=303)

    # Ambil data karyawan dari database
    karyawan = db.query(Karyawan).filter(Karyawan.id == id).first()
    if not karyawan:
        # Karyawan tidak ditemukan, redirect ke halaman login
        return RedirectResponse(url="/employee-login", status_code=303)

    # Ambil notifikasi dari cookies
    notif_login = request.cookies.get("notif_login", "")  # Notifikasi login
    notif_absen = request.cookies.get("notif_absen", "")  # Notifikasi absensi

    # Render template dengan data karyawan dan notifikasi
    response = templates.TemplateResponse(
        "employee-absensi.html",
        {"request": request, "nama": karyawan.nama, "notif_login": notif_login, "notif_absen": notif_absen}
    )

    # Hapus cookies notifikasi setelah ditampilkan
    response.delete_cookie("notif_login")  # Hapus cookie notif_login
    response.delete_cookie("notif_absen")  # Hapus cookie notif_absen

    return response

@app.get("/employee-logout")
async def employee_logout():
    """
    Endpoint untuk logout dari halaman karyawan

    Returns:
        RedirectResponse: Redirect ke halaman login karyawan
    """
    # Buat response redirect ke halaman login
    response = RedirectResponse(url="/employee-login", status_code=303)

    # Hapus cookies
    response.delete_cookie("notif_login")  # Hapus cookie notif_login
    response.delete_cookie("notif_absen")  # Hapus cookie notif_absen

    return response

@app.post("/absen-masuk")
async def absen_masuk(
    request: Request,
    waktu: str = Form(...),
    hari: str = Form(...),
    lat: float = Form(None),
    lon: float = Form(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk memproses absen masuk karyawan tanpa webcam (versi lama)

    Args:
        request (Request): Request object dari FastAPI
        waktu (str): Waktu absen
        hari (str): Hari absen
        lat (float): Koordinat latitude lokasi
        lon (float): Koordinat longitude lokasi
        db (Session): Session database

    Returns:
        RedirectResponse: Redirect ke halaman absensi dengan notifikasi
    """
    # Ambil nama karyawan dari query parameter atau cookie
    nama = request.query_params.get("nama") or request.cookies.get("nama")
    if not nama:
        return RedirectResponse(url="/employee-login", status_code=303)

    # Ambil data karyawan dari database
    karyawan = db.query(Karyawan).filter(Karyawan.nama == nama).first()
    if not karyawan:
        return RedirectResponse(url="/employee-login", status_code=303)

    # Dapatkan tanggal hari ini
    today = datetime.now().date()

    # Cek apakah karyawan sudah absen masuk hari ini
    existing_attendance = db.query(Absensi).filter(
        Absensi.karyawan_id == karyawan.id,
        Absensi.tanggal >= today,
        Absensi.tanggal < today + timedelta(days=1)
    ).first()

    if existing_attendance:
        # Jika sudah ada absensi dan belum ada jam keluar, berarti karyawan perlu absen keluar
        if existing_attendance.jam_masuk and not existing_attendance.jam_keluar:
            response = RedirectResponse(url=f"/employee-absensi?nama={nama}", status_code=303)
            response.set_cookie("notif_absen", "Anda sudah absen masuk hari ini. Silakan lakukan absen keluar.")
            return response

        # Jika sudah ada absensi lengkap (masuk dan keluar), berarti karyawan sudah melakukan absensi penuh hari ini
        elif existing_attendance.jam_masuk and existing_attendance.jam_keluar:
            response = RedirectResponse(url=f"/employee-absensi?nama={nama}", status_code=303)
            response.set_cookie("notif_absen", "Anda sudah melakukan absensi masuk dan keluar hari ini.")
            return response

    # Jika belum ada absensi hari ini, buat absensi baru
    try:
        # Buat objek absensi baru
        current_time = datetime.now()
        alamat_str = f"{lat}, {lon}" if lat and lon else "Lokasi tidak tersedia"

        absensi = Absensi(
            karyawan_id=karyawan.id,
            tanggal=today,
            jam_masuk=current_time,
            waktu=waktu,
            hari=hari,
            latitude=lat,
            longitude=lon,
            status="Hadir",
            alamat=alamat_str,
            foto_masuk=None,  # Tidak ada foto untuk absen tanpa webcam
            keterangan=None,  # Tidak ada keterangan
            uang_makan=False  # Default uang makan: False
        )

        # Simpan ke database
        db.add(absensi)
        db.commit()

        # Set cookie notif dan redirect
        response = RedirectResponse(url=f"/employee-absensi?nama={nama}", status_code=303)
        response.set_cookie("notif_absen", "Absen masuk berhasil!")
        return response
    except Exception as e:
        # Tangani error jika terjadi
        db.rollback()
        response = RedirectResponse(url=f"/employee-absensi?nama={nama}", status_code=303)
        response.set_cookie("notif_absen", f"Gagal menyimpan absensi: {str(e)}")
        return response

@app.post("/absen-masuk-webcam")
async def absen_masuk_webcam_post(
    request: Request,  # Request object dari FastAPI (tidak digunakan dalam fungsi ini)
    id: int = Form(...),  # ID karyawan
    imageData: str = Form(...),  # Data gambar dalam format base64
    waktu: str = Form(...),  # Waktu absen (tidak digunakan, diganti dengan datetime.now())
    hari: str = Form(...),  # Hari absen (tidak digunakan)
    alamat: str = Form(...),  # Alamat/lokasi absen
    db: Session = Depends(get_db)  # Session database
):
    """
    Endpoint untuk memproses absen masuk karyawan menggunakan webcam

    Args:
        request (Request): Request object dari FastAPI (tidak digunakan dalam fungsi ini)
        id (int): ID karyawan
        imageData (str): Data gambar dalam format base64
        waktu (str): Waktu absen (tidak digunakan, diganti dengan datetime.now())
        hari (str): Hari absen (tidak digunakan)
        alamat (str): Alamat/lokasi absen
        uang_makan (bool, optional): Status uang makan (default: False)
        db (Session): Session database

    Returns:
        RedirectResponse: Redirect ke halaman absensi dengan notifikasi sukses atau error
    """
    # Tambahkan logging untuk debugging
    logger.info(f"Processing check-in for employee ID: {id}")
    logger.info(f"Check-in location: {alamat}")

    # Ambil data karyawan dari database berdasarkan ID
    karyawan = db.query(Karyawan).filter(Karyawan.id == id).first()
    if not karyawan:
        # Karyawan tidak ditemukan, redirect ke halaman login
        logger.warning(f"Employee with ID {id} not found")
        return RedirectResponse(url="/employee-login", status_code=303)

    logger.info(f"Found employee: {karyawan.nama} (ID: {karyawan.id})")

    # Dapatkan tanggal hari ini untuk perbandingan
    today = datetime.now().date()
    logger.info(f"Current date: {today}")

    # Cek apakah karyawan sudah absen masuk hari ini
    existing_attendance = db.query(Absensi).filter(
        Absensi.karyawan_id == karyawan.id,
        Absensi.tanggal >= today,
        Absensi.tanggal < today + timedelta(days=1)
    ).first()

    if existing_attendance:
        logger.warning(f"Employee {karyawan.nama} already has attendance record for today (ID: {existing_attendance.id})")

        # Jika sudah ada absensi dan belum ada jam keluar, berarti karyawan perlu absen keluar
        if existing_attendance.jam_masuk and not existing_attendance.jam_keluar:
            # Redirect ke halaman absensi dengan notifikasi
            response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
            response.set_cookie("notif_absen", "Anda sudah absen masuk hari ini. Silakan lakukan absen keluar.")
            response.set_cookie("nama", karyawan.nama)
            return response

        # Jika sudah ada absensi lengkap (masuk dan keluar), berarti karyawan sudah melakukan absensi penuh hari ini
        elif existing_attendance.jam_masuk and existing_attendance.jam_keluar:
            # Redirect ke halaman absensi dengan notifikasi
            response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
            response.set_cookie("notif_absen", "Anda sudah melakukan absensi masuk dan keluar hari ini.")
            response.set_cookie("nama", karyawan.nama)
            return response

    # Jika belum ada absensi hari ini, lanjutkan proses absen masuk
    try:
        # Decode foto dari format base64 menjadi bytes
        header, encoded = imageData.split(",", 1)  # Pisahkan header dan data
        foto_bytes = base64.b64decode(encoded)  # Decode base64 menjadi bytes
        logger.info(f"Successfully decoded photo, size: {len(foto_bytes)} bytes")
    except Exception as e:
        logger.error(f"Error decoding photo: {str(e)}")
        foto_bytes = None

    # Buat objek absensi baru
    current_time = datetime.now()
    logger.info(f"Creating new attendance record with check-in time: {current_time}")

    absensi = Absensi(
        karyawan_id=karyawan.id,  # ID karyawan
        tanggal=current_time.date(),  # Tanggal absen (hari ini)
        jam_masuk=current_time,  # Jam masuk (waktu saat ini)
        waktu=waktu,  # Waktu dari form (untuk kompatibilitas)
        hari=hari,  # Hari dari form (untuk kompatibilitas)
        status="Hadir",  # Status kehadiran
        alamat=alamat,  # Alamat/lokasi absen
        foto_masuk=foto_bytes,  # Foto saat absen masuk
        uang_makan=False,  # Status uang makan (default: False)
        keterangan=None  # Keterangan (kosong)
    )

    try:
        # Simpan ke database
        db.add(absensi)  # Tambahkan objek ke session
        db.commit()  # Simpan perubahan ke database
        logger.info(f"Successfully saved new attendance record with ID: {absensi.id}")

        # Buat response redirect dengan notifikasi
        response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
        response.set_cookie("notif_absen", "Absen masuk berhasil!")  # Set notifikasi absen
        response.set_cookie("nama", karyawan.nama)  # Set cookie nama karyawan
        return response
    except Exception as e:
        # Tangani error jika terjadi
        logger.error(f"Error saving attendance record: {str(e)}")
        db.rollback()

        # Redirect dengan pesan error
        response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
        response.set_cookie("notif_absen", f"Gagal menyimpan absensi: {str(e)}")
        response.set_cookie("nama", karyawan.nama)
        return response

@app.get("/absen-masuk-webcam", response_class=HTMLResponse)
async def absen_masuk_webcam_get(request: Request, id: int = None, db: Session = Depends(get_db)):
    if not id:
        return RedirectResponse(url="/employee-login", status_code=303)

    # Fetch employee data
    karyawan = db.query(Karyawan).filter(Karyawan.id == id).first()
    if not karyawan:
        return RedirectResponse(url="/employee-login", status_code=303)

    return templates.TemplateResponse(
        "absen-masuk-webcam.html",
        {
            "request": request,
            "id": id,
            "nama": karyawan.nama
        }
    )

@app.post("/absen-keluar-webcam")
async def absen_keluar_webcam_post(
    request: Request,
    id: int = Form(...),  # ID karyawan dari form
    imageData: str = Form(...),  # Data gambar dalam format base64
    waktu: str = Form(...),  # Waktu absen (tidak digunakan, diganti dengan datetime.now())
    alamat: str = Form(...),  # Alamat/lokasi absen keluar
    uang_makan: bool = Form(False),  # Status uang makan (default: False)
    uang_transport: bool = Form(False),  # Status uang transportasi (default: False)
    db: Session = Depends(get_db)
):
    """
    Fungsi untuk memproses absen keluar karyawan menggunakan webcam

    Parameter:
    - request: Request object dari FastAPI
    - id: ID karyawan yang melakukan absen
    - imageData: Foto karyawan dalam format base64
    - waktu: Waktu absen dari form (tidak digunakan)
    - alamat: Alamat/lokasi saat absen keluar
    - db: Database session

    Return:
    - Redirect ke halaman employee-absensi dengan notifikasi sukses
    """
    # Tambahkan logging untuk debugging
    logger.info(f"Processing check-out for employee ID: {id}")
    logger.info(f"Check-out location: {alamat}")
    logger.info(f"Check-out time: {datetime.now()}")

    # Ambil data karyawan berdasarkan ID dari form
    karyawan = db.query(Karyawan).filter(Karyawan.id == id).first()
    if not karyawan:
        logger.error(f"Employee with ID {id} not found")
        return RedirectResponse(url="/employee-login", status_code=303)

    logger.info(f"Found employee: {karyawan.nama} (ID: {karyawan.id})")

    # Decode foto dari format base64 menjadi bytes
    try:
        header, encoded = imageData.split(",", 1)
        foto_bytes = base64.b64decode(encoded)
        logger.info(f"Successfully decoded photo, size: {len(foto_bytes)} bytes")
    except Exception as e:
        logger.error(f"Error decoding photo: {str(e)}")
        foto_bytes = None

    # Get current date for comparison
    today = datetime.now().date()
    logger.info(f"Looking for attendance record for date: {today}")

    # Cari data absensi karyawan untuk hari ini
    try:
        # Log the SQL query for debugging
        query = db.query(Absensi).filter(
            Absensi.karyawan_id == karyawan.id,
            Absensi.tanggal == today
        )
        logger.info(f"SQL Query: {str(query)}")

        # Try to get all records for this employee to see what's available
        all_employee_records = db.query(Absensi).filter(
            Absensi.karyawan_id == karyawan.id
        ).all()

        logger.info(f"Found {len(all_employee_records)} total records for employee {karyawan.id}")
        for record in all_employee_records:
            logger.info(f"Record ID: {record.id}, Date: {record.tanggal}, Type: {type(record.tanggal)}")
            # Check if this record's date matches today
            date_match = record.tanggal.date() == today if hasattr(record.tanggal, 'date') else record.tanggal == today
            logger.info(f"Date match with today ({today})? {date_match}")

        # Try to find the record for today, considering possible date format issues
        absensi = None

        # First try the original query
        absensi = query.first()

        # If not found, try to find the record by checking each record's date
        if not absensi and all_employee_records:
            logger.info("No record found with exact date match, trying alternative approach")
            for record in all_employee_records:
                # Try different ways to compare dates
                if hasattr(record.tanggal, 'date'):
                    # If tanggal is a datetime object
                    if record.tanggal.date() == today:
                        absensi = record
                        logger.info(f"Found matching record using datetime.date() method: {record.id}")
                        break
                elif isinstance(record.tanggal, datetime):
                    # Another way to check if it's a datetime
                    if record.tanggal.date() == today:
                        absensi = record
                        logger.info(f"Found matching record using isinstance check: {record.id}")
                        break
                else:
                    # Direct comparison
                    if record.tanggal == today:
                        absensi = record
                        logger.info(f"Found matching record using direct comparison: {record.id}")
                        break

        # Jika tidak ada absensi hari ini, beritahu karyawan untuk absen masuk terlebih dahulu
        if not absensi:
            logger.warning(f"No attendance record found for employee {karyawan.nama} on {today}")
            response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
            response.set_cookie("notif_absen", "Anda belum melakukan absen masuk hari ini. Silakan lakukan absen masuk terlebih dahulu.")
            response.set_cookie("nama", karyawan.nama)
            return response

        # Jika sudah ada absensi dan sudah ada jam keluar, berarti karyawan sudah absen keluar
        if absensi.jam_keluar:
            logger.warning(f"Employee {karyawan.nama} already has check-out record for today (ID: {absensi.id})")
            response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
            response.set_cookie("notif_absen", "Anda sudah melakukan absen keluar hari ini.")
            response.set_cookie("nama", karyawan.nama)
            return response

        # Jika data absensi ditemukan dan belum ada jam keluar, update dengan data absen keluar
        logger.info(f"Found attendance record with ID: {absensi.id}")
        logger.info(f"Current check-in time: {absensi.jam_masuk}")
        logger.info(f"Current check-out time: {absensi.jam_keluar}")

        # Update data absen keluar
        current_time = datetime.now()
        logger.info(f"Setting check-out time to: {current_time}")

        absensi.jam_keluar = current_time  # Gunakan waktu server untuk konsistensi
        if foto_bytes:
            absensi.foto_keluar = foto_bytes  # Simpan foto saat absen keluar
        absensi.alamat_keluar = alamat  # Simpan lokasi saat absen keluar
        absensi.uang_makan = uang_makan  # Simpan status uang makan
        absensi.uang_transport = uang_transport  # Simpan status uang transportasi

        try:
            db.commit()  # Simpan perubahan ke database
            logger.info("Successfully committed check-out data to database")

            # Verify the update was successful
            db.refresh(absensi)
            logger.info(f"After update - check-out time: {absensi.jam_keluar}")
            logger.info(f"After update - check-out location: {absensi.alamat_keluar}")
            logger.info(f"After update - has check-out photo: {bool(absensi.foto_keluar)}")
        except Exception as commit_error:
            logger.error(f"Error committing to database: {str(commit_error)}")
            db.rollback()
    except Exception as query_error:
        logger.error(f"Error querying attendance record: {str(query_error)}")

    # Redirect ke halaman employee-absensi dengan notifikasi
    response = RedirectResponse(url=f"/employee-absensi?id={karyawan.id}", status_code=303)
    response.set_cookie("notif_absen", "Absen keluar berhasil!")
    logger.info(f"Redirecting to employee-absensi with success notification")
    return response

@app.delete("/admin/absensi/{absensi_id}")
async def delete_absensi(absensi_id: int, db: Session = Depends(get_db)):
    """
    Endpoint untuk menghapus data absensi

    Args:
        absensi_id (int): ID absensi yang akan dihapus
        db (Session): Session database

    Returns:
        dict: Status hasil operasi

    Raises:
        HTTPException: Jika absensi tidak ditemukan
    """
    try:
        # Log permintaan hapus
        logger.info(f"Menghapus data absensi dengan ID: {absensi_id}")

        # Cari data absensi berdasarkan ID
        absensi = db.query(Absensi).filter(Absensi.id == absensi_id).first()

        # Jika data tidak ditemukan, kirim response error
        if not absensi:
            logger.warning(f"Data absensi dengan ID {absensi_id} tidak ditemukan")
            raise HTTPException(status_code=404, detail="Absensi tidak ditemukan")

        # Log informasi absensi yang akan dihapus
        logger.info(f"Data absensi ditemukan: ID={absensi.id}, Karyawan={absensi.karyawan.nama if absensi.karyawan else 'Unknown'}, Tanggal={absensi.tanggal}")

        # Hapus data absensi
        db.delete(absensi)
        db.commit()

        # Log keberhasilan
        logger.info(f"Data absensi dengan ID {absensi_id} berhasil dihapus")

        # Kirim response sukses
        return {"status": "success", "message": "Data absensi berhasil dihapus"}

    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he

    except Exception as e:
        # Log error dan rollback jika terjadi kesalahan
        logger.error(f"Error saat menghapus data absensi: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan saat menghapus data: {str(e)}")

@app.put("/admin/absensi/{absensi_id}/uang-makan")
async def update_uang_makan(
    absensi_id: int,
    data: dict,
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk mengupdate status uang makan

    Args:
        absensi_id (int): ID absensi yang akan diupdate
        data (dict): Data yang berisi status uang makan baru
        db (Session): Session database

    Returns:
        dict: Status hasil operasi

    Raises:
        HTTPException: Jika absensi tidak ditemukan
    """
    # Cari data absensi berdasarkan ID
    absensi = db.query(Absensi).filter(Absensi.id == absensi_id).first()
    if not absensi:
        raise HTTPException(status_code=404, detail="Absensi tidak ditemukan")

    # Update status uang makan
    absensi.uang_makan = data.get("uang_makan", False)

    # Simpan perubahan ke database
    db.commit()

    return {"status": "success", "message": "Status uang makan berhasil diperbarui"}

@app.get("/absen-keluar-webcam", response_class=HTMLResponse)
async def absen_keluar_webcam(request: Request, id: int = None, db: Session = Depends(get_db)):
    if not id:
        return RedirectResponse(url="/employee-absensi", status_code=303)
    karyawan = db.query(Karyawan).filter(Karyawan.id == id).first()
    if not karyawan:
        return RedirectResponse(url="/employee-absensi", status_code=303)
    return templates.TemplateResponse(
        "absen-keluar-webcam.html",
        {"request": request, "id": id, "nama": karyawan.nama}
    )

# Jalankan dengan: uvicorn main:app --reload