"""
Script untuk mengumpulkan dan memproses data training untuk pengenalan wajah karyawan.
Script ini akan:
1. Mengambil gambar wajah karyawan menggunakan webcam
2. Memproses gambar untuk mendeteksi wajah
3. Menyimpan encoding wajah ke database untuk digunakan dalam sistem login

Cara penggunaan:
1. Jalankan script dengan perintah: python face_training.py
2. Ikuti instruksi yang muncul di layar
3. Tekan 'q' untuk keluar dari program
"""

import cv2
import face_recognition
import numpy as np
import os
import sqlite3
import json
import logging
from datetime import datetime

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Direktori untuk menyimpan gambar wajah
FACE_DIR = "face_data"
if not os.path.exists(FACE_DIR):
    os.makedirs(FACE_DIR)
    logger.info(f"Direktori {FACE_DIR} berhasil dibuat")

def connect_to_database():
    """
    Fungsi untuk menghubungkan ke database
    
    Returns:
        tuple: (connection, cursor) - Koneksi dan cursor database
    """
    try:
        conn = sqlite3.connect('absensi.db')
        cursor = conn.cursor()
        logger.info("Berhasil terhubung ke database")
        return conn, cursor
    except Exception as e:
        logger.error(f"Error saat menghubungkan ke database: {str(e)}")
        return None, None

def get_all_employees(cursor):
    """
    Fungsi untuk mendapatkan semua data karyawan dari database
    
    Args:
        cursor: Database cursor
        
    Returns:
        list: Daftar karyawan dengan format [(id, nama), ...]
    """
    try:
        cursor.execute("SELECT id, nama FROM karyawan")
        employees = cursor.fetchall()
        logger.info(f"Berhasil mendapatkan {len(employees)} data karyawan")
        return employees
    except Exception as e:
        logger.error(f"Error saat mengambil data karyawan: {str(e)}")
        return []

def capture_face(employee_id, employee_name):
    """
    Fungsi untuk mengambil gambar wajah karyawan menggunakan webcam
    
    Args:
        employee_id (int): ID karyawan
        employee_name (str): Nama karyawan
        
    Returns:
        numpy.ndarray: Encoding wajah karyawan, atau None jika gagal
    """
    logger.info(f"Memulai pengambilan gambar wajah untuk {employee_name} (ID: {employee_id})")
    
    # Inisialisasi webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Tidak dapat membuka webcam")
        return None
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    face_encoding = None
    captured = False
    
    while not captured:
        # Baca frame dari webcam
        ret, frame = cap.read()
        if not ret:
            logger.error("Tidak dapat membaca frame dari webcam")
            break
        
        # Konversi ke grayscale untuk deteksi wajah
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Deteksi wajah
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Gambar kotak di sekitar wajah yang terdeteksi
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        # Tampilkan instruksi
        cv2.putText(frame, f"Karyawan: {employee_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Tekan 'c' untuk mengambil gambar", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Tekan 'q' untuk keluar", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Tampilkan frame
        cv2.imshow('Face Training', frame)
        
        # Tunggu input keyboard
        key = cv2.waitKey(1)
        
        # Jika 'q' ditekan, keluar dari loop
        if key == ord('q'):
            logger.info("Pengambilan gambar dibatalkan")
            break
        
        # Jika 'c' ditekan, ambil gambar
        if key == ord('c'):
            # Cek apakah ada wajah yang terdeteksi
            if len(faces) == 0:
                logger.warning("Tidak ada wajah yang terdeteksi. Coba lagi.")
                continue
            
            if len(faces) > 1:
                logger.warning("Terdeteksi lebih dari satu wajah. Pastikan hanya ada satu wajah dalam frame.")
                continue
            
            # Konversi frame ke RGB (face_recognition menggunakan RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Dapatkan encoding wajah
            encodings = face_recognition.face_encodings(rgb_frame)
            if not encodings:
                logger.warning("Tidak dapat mengekstrak encoding wajah. Coba lagi.")
                continue
            
            face_encoding = encodings[0]
            
            # Simpan gambar
            img_path = os.path.join(FACE_DIR, f"employee_{employee_id}.jpg")
            cv2.imwrite(img_path, frame)
            logger.info(f"Gambar wajah disimpan di {img_path}")
            
            captured = True
    
    # Tutup webcam
    cap.release()
    cv2.destroyAllWindows()
    
    return face_encoding

def save_face_encoding(cursor, conn, employee_id, face_encoding):
    """
    Fungsi untuk menyimpan encoding wajah ke database
    
    Args:
        cursor: Database cursor
        conn: Database connection
        employee_id (int): ID karyawan
        face_encoding (numpy.ndarray): Encoding wajah karyawan
        
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    try:
        # Konversi encoding ke bytes
        encoding_bytes = face_encoding.tobytes()
        
        # Cek apakah encoding sudah ada
        cursor.execute("SELECT id FROM face_encoding WHERE karyawan_id = ?", (employee_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update encoding yang sudah ada
            cursor.execute("UPDATE face_encoding SET encoding = ?, updated_at = ? WHERE karyawan_id = ?",
                          (encoding_bytes, datetime.now(), employee_id))
            logger.info(f"Encoding wajah untuk karyawan ID {employee_id} berhasil diperbarui")
        else:
            # Buat encoding baru
            cursor.execute("INSERT INTO face_encoding (karyawan_id, encoding, created_at, updated_at) VALUES (?, ?, ?, ?)",
                          (employee_id, encoding_bytes, datetime.now(), datetime.now()))
            logger.info(f"Encoding wajah untuk karyawan ID {employee_id} berhasil disimpan")
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saat menyimpan encoding wajah: {str(e)}")
        return False

def main():
    """
    Fungsi utama untuk menjalankan program
    """
    logger.info("Memulai program training wajah karyawan")
    
    # Hubungkan ke database
    conn, cursor = connect_to_database()
    if not conn or not cursor:
        logger.error("Tidak dapat melanjutkan tanpa koneksi database")
        return
    
    try:
        # Dapatkan semua karyawan
        employees = get_all_employees(cursor)
        if not employees:
            logger.error("Tidak ada data karyawan")
            return
        
        # Tampilkan daftar karyawan
        print("\n=== DAFTAR KARYAWAN ===")
        for i, (emp_id, emp_name) in enumerate(employees):
            print(f"{i+1}. {emp_name} (ID: {emp_id})")
        
        # Pilih karyawan
        while True:
            try:
                choice = int(input("\nPilih nomor karyawan (0 untuk keluar): "))
                if choice == 0:
                    break
                
                if 1 <= choice <= len(employees):
                    employee_id, employee_name = employees[choice-1]
                    
                    # Ambil gambar wajah
                    face_encoding = capture_face(employee_id, employee_name)
                    
                    if face_encoding is not None:
                        # Simpan encoding wajah
                        success = save_face_encoding(cursor, conn, employee_id, face_encoding)
                        if success:
                            print(f"Data wajah untuk {employee_name} berhasil disimpan!")
                        else:
                            print(f"Gagal menyimpan data wajah untuk {employee_name}")
                else:
                    print("Pilihan tidak valid")
            except ValueError:
                print("Masukkan nomor yang valid")
    finally:
        # Tutup koneksi database
        if conn:
            conn.close()
            logger.info("Koneksi database ditutup")
    
    logger.info("Program training wajah karyawan selesai")

if __name__ == "__main__":
    main()
