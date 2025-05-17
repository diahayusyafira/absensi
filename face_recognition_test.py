"""
Script untuk menguji pengenalan wajah karyawan.
Script ini akan:
1. Mengambil gambar wajah menggunakan webcam
2. Membandingkan dengan data wajah karyawan yang tersimpan di database
3. Menampilkan hasil pengenalan wajah

Cara penggunaan:
1. Jalankan script dengan perintah: python face_recognition_test.py
2. Arahkan wajah ke webcam
3. Tekan 'q' untuk keluar dari program
"""

import cv2
import face_recognition
import numpy as np
import sqlite3
import logging
from datetime import datetime

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def get_employee_face_data(cursor):
    """
    Fungsi untuk mendapatkan data wajah karyawan dari database
    
    Args:
        cursor: Database cursor
        
    Returns:
        dict: Dictionary dengan format {employee_id: (employee_name, face_encoding), ...}
    """
    try:
        # Dapatkan data karyawan dan encoding wajah
        cursor.execute("""
            SELECT k.id, k.nama, f.encoding 
            FROM karyawan k
            JOIN face_encoding f ON k.id = f.karyawan_id
        """)
        
        employee_data = {}
        for row in cursor.fetchall():
            employee_id, employee_name, encoding_bytes = row
            
            # Konversi bytes ke numpy array
            face_encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
            
            employee_data[employee_id] = (employee_name, face_encoding)
        
        logger.info(f"Berhasil mendapatkan data wajah untuk {len(employee_data)} karyawan")
        return employee_data
    except Exception as e:
        logger.error(f"Error saat mengambil data wajah karyawan: {str(e)}")
        return {}

def main():
    """
    Fungsi utama untuk menjalankan program
    """
    logger.info("Memulai program pengujian pengenalan wajah")
    
    # Hubungkan ke database
    conn, cursor = connect_to_database()
    if not conn or not cursor:
        logger.error("Tidak dapat melanjutkan tanpa koneksi database")
        return
    
    try:
        # Dapatkan data wajah karyawan
        employee_data = get_employee_face_data(cursor)
        if not employee_data:
            logger.error("Tidak ada data wajah karyawan")
            return
        
        # Daftar encoding wajah dan nama karyawan
        known_face_encodings = []
        known_face_names = []
        
        for employee_id, (employee_name, face_encoding) in employee_data.items():
            known_face_encodings.append(face_encoding)
            known_face_names.append(f"{employee_name} (ID: {employee_id})")
        
        # Inisialisasi webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logger.error("Tidak dapat membuka webcam")
            return
        
        logger.info("Webcam berhasil dibuka. Tekan 'q' untuk keluar.")
        
        while True:
            # Baca frame dari webcam
            ret, frame = cap.read()
            if not ret:
                logger.error("Tidak dapat membaca frame dari webcam")
                break
            
            # Resize frame untuk mempercepat proses (opsional)
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            
            # Konversi ke RGB (face_recognition menggunakan RGB)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Temukan semua wajah dan encoding wajah dalam frame
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            face_names = []
            for face_encoding in face_encodings:
                # Bandingkan dengan data wajah yang tersimpan
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                name = "Tidak Dikenal"
                
                # Gunakan wajah dengan jarak terkecil
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                
                face_names.append(name)
            
            # Tampilkan hasil
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Gambar kotak di sekitar wajah
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                
                # Gambar label dengan nama
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
            
            # Tampilkan instruksi
            cv2.putText(frame, "Tekan 'q' untuk keluar", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Tampilkan frame
            cv2.imshow('Face Recognition Test', frame)
            
            # Tunggu input keyboard
            if cv2.waitKey(1) == ord('q'):
                break
        
        # Tutup webcam
        cap.release()
        cv2.destroyAllWindows()
    
    finally:
        # Tutup koneksi database
        if conn:
            conn.close()
            logger.info("Koneksi database ditutup")
    
    logger.info("Program pengujian pengenalan wajah selesai")

if __name__ == "__main__":
    main()
