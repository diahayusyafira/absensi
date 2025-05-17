"""
Script untuk mengevaluasi performa sistem pengenalan wajah menggunakan metrik F1-score.

F1-score adalah metrik evaluasi yang menggabungkan precision dan recall, memberikan
ukuran keseimbangan antara keduanya. F1-score sangat penting dalam sistem pengenalan wajah
karena memberikan gambaran yang lebih komprehensif tentang performa sistem dibandingkan
hanya menggunakan akurasi.

Sistem ini menggunakan model CNN (Convolutional Neural Network) melalui library face_recognition
yang berbasis deep learning untuk deteksi dan pengenalan wajah. Model CNN memberikan
performa yang jauh lebih baik dibandingkan metode tradisional seperti Haar Cascade.

Script ini akan:
1. Mengambil data wajah karyawan dari database
2. Mengevaluasi performa sistem dengan menghitung precision, recall, dan F1-score
3. Menampilkan hasil evaluasi dalam bentuk laporan

Cara penggunaan:
1. Jalankan script dengan perintah: python face_recognition_evaluation.py
2. Ikuti instruksi yang muncul di layar
"""

import cv2
import face_recognition
import numpy as np
import sqlite3
import os
import logging
from datetime import datetime
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, classification_report

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

# Direktori untuk menyimpan gambar pengujian
TEST_DIR = "test_data"
if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)
    logger.info(f"Direktori {TEST_DIR} berhasil dibuat")

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

def capture_test_images(employee_id, employee_name, num_images=5):
    """
    Fungsi untuk mengambil beberapa gambar wajah untuk pengujian

    Args:
        employee_id (int): ID karyawan
        employee_name (str): Nama karyawan
        num_images (int): Jumlah gambar yang akan diambil

    Returns:
        list: Daftar path gambar yang diambil
    """
    logger.info(f"Memulai pengambilan gambar pengujian untuk {employee_name} (ID: {employee_id})")

    # Inisialisasi webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Tidak dapat membuka webcam")
        return []

    # Menggunakan face_recognition (berbasis CNN) untuk deteksi wajah
    # Tidak perlu menggunakan Haar Cascade Classifier

    image_paths = []
    images_captured = 0

    while images_captured < num_images:
        # Baca frame dari webcam
        ret, frame = cap.read()
        if not ret:
            logger.error("Tidak dapat membaca frame dari webcam")
            break

        # Konversi ke RGB untuk face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Deteksi wajah menggunakan model CNN dari face_recognition
        faces = face_recognition.face_locations(rgb_frame, model="cnn")

        # Konversi format face_locations ke format (x, y, w, h) untuk kompatibilitas dengan kode yang ada
        faces_rect = []
        for (top, right, bottom, left) in faces:
            faces_rect.append((left, top, right-left, bottom-top))

        # Gambar kotak di sekitar wajah yang terdeteksi
        for (x, y, w, h) in faces_rect:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        # Tampilkan instruksi
        cv2.putText(frame, f"Karyawan: {employee_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Gambar: {images_captured+1}/{num_images}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Tekan 'c' untuk mengambil gambar", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Tekan 'q' untuk keluar", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Tampilkan frame
        cv2.imshow('Face Evaluation', frame)

        # Tunggu input keyboard
        key = cv2.waitKey(1)

        # Jika 'q' ditekan, keluar dari loop
        if key == ord('q'):
            logger.info("Pengambilan gambar dibatalkan")
            break

        # Jika 'c' ditekan, ambil gambar
        if key == ord('c'):
            # Cek apakah ada wajah yang terdeteksi
            if len(faces_rect) == 0:
                logger.warning("Tidak ada wajah yang terdeteksi. Coba lagi.")
                continue

            if len(faces_rect) > 1:
                logger.warning("Terdeteksi lebih dari satu wajah. Pastikan hanya ada satu wajah dalam frame.")
                continue

            # Simpan gambar
            img_path = os.path.join(TEST_DIR, f"employee_{employee_id}_test_{images_captured+1}.jpg")
            cv2.imwrite(img_path, frame)
            logger.info(f"Gambar pengujian disimpan di {img_path}")

            image_paths.append(img_path)
            images_captured += 1

    # Tutup webcam
    cap.release()
    cv2.destroyAllWindows()

    return image_paths

def evaluate_face_recognition(employee_data, test_images_dir=TEST_DIR):
    """
    Fungsi untuk mengevaluasi performa sistem pengenalan wajah

    Args:
        employee_data (dict): Data wajah karyawan
        test_images_dir (str): Direktori gambar pengujian

    Returns:
        tuple: (precision, recall, f1, report) - Metrik evaluasi
    """
    logger.info("Memulai evaluasi sistem pengenalan wajah")

    # Daftar encoding wajah dan ID karyawan
    known_face_encodings = []
    known_face_ids = []

    for employee_id, (_, face_encoding) in employee_data.items():
        known_face_encodings.append(face_encoding)
        known_face_ids.append(employee_id)

    # Daftar untuk menyimpan hasil prediksi dan label sebenarnya
    y_true = []
    y_pred = []

    # Ambil semua gambar pengujian
    test_images = [f for f in os.listdir(test_images_dir) if f.endswith('.jpg')]

    for image_file in test_images:
        # Ekstrak ID karyawan dari nama file
        try:
            true_id = int(image_file.split('_')[1])
        except:
            logger.warning(f"Tidak dapat mengekstrak ID karyawan dari nama file: {image_file}")
            continue

        # Baca gambar
        image_path = os.path.join(test_images_dir, image_file)
        image = cv2.imread(image_path)

        if image is None:
            logger.warning(f"Tidak dapat membaca gambar: {image_path}")
            continue

        # Konversi ke RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Deteksi wajah menggunakan model CNN dan ekstrak encoding
        # Model CNN memberikan deteksi yang lebih akurat dan fleksibel
        face_locations = face_recognition.face_locations(rgb_image, model="cnn")

        if not face_locations:
            logger.warning(f"Tidak ada wajah yang terdeteksi dalam gambar: {image_path}")
            continue

        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        # Untuk setiap wajah yang terdeteksi
        for face_encoding in face_encodings:
            # Bandingkan dengan data wajah yang tersimpan
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)

            # Jika tidak ada yang cocok, tandai sebagai "tidak dikenal"
            if not any(matches):
                pred_id = -1  # ID untuk "tidak dikenal"
            else:
                # Gunakan wajah dengan jarak terkecil
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                pred_id = known_face_ids[best_match_index]

            # Tambahkan ke daftar prediksi dan label sebenarnya
            y_true.append(true_id)
            y_pred.append(pred_id)

    # Hitung metrik evaluasi
    if len(y_true) > 0:
        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        report = classification_report(y_true, y_pred, zero_division=0)

        logger.info(f"Precision: {precision:.4f}")
        logger.info(f"Recall: {recall:.4f}")
        logger.info(f"F1-score: {f1:.4f}")
        logger.info(f"Classification Report:\n{report}")

        return precision, recall, f1, report
    else:
        logger.warning("Tidak ada data yang cukup untuk evaluasi")
        return 0, 0, 0, "Tidak ada data"

def main():
    """
    Fungsi utama untuk menjalankan program
    """
    logger.info("Memulai program evaluasi pengenalan wajah")

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

        # Tampilkan daftar karyawan
        print("\n=== DAFTAR KARYAWAN ===")
        for i, (emp_id, (emp_name, _)) in enumerate(employee_data.items()):
            print(f"{i+1}. {emp_name} (ID: {emp_id})")

        # Pilih mode evaluasi
        print("\n=== MODE EVALUASI ===")
        print("1. Evaluasi dengan gambar yang sudah ada di folder test_data")
        print("2. Ambil gambar baru untuk evaluasi")

        mode = input("Pilih mode evaluasi (1/2): ")

        if mode == "2":
            # Pilih karyawan untuk pengambilan gambar pengujian
            while True:
                try:
                    choice = int(input("\nPilih nomor karyawan (0 untuk keluar): "))
                    if choice == 0:
                        break

                    if 1 <= choice <= len(employee_data):
                        employee_id = list(employee_data.keys())[choice-1]
                        employee_name = employee_data[employee_id][0]

                        # Ambil gambar pengujian
                        num_images = int(input(f"Berapa gambar yang ingin diambil untuk {employee_name}? "))
                        capture_test_images(employee_id, employee_name, num_images)
                    else:
                        print("Pilihan tidak valid")
                except ValueError:
                    print("Masukkan nomor yang valid")

        # Evaluasi sistem pengenalan wajah
        precision, recall, f1, report = evaluate_face_recognition(employee_data)

        # Tampilkan hasil evaluasi
        print("\n=== HASIL EVALUASI ===")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-score: {f1:.4f}")
        print("\nClassification Report:")
        print(report)

        # Simpan hasil evaluasi ke file
        with open("face_recognition_evaluation_report.txt", "w") as f:
            f.write("=== HASIL EVALUASI SISTEM PENGENALAN WAJAH ===\n")
            f.write(f"Tanggal Evaluasi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Precision: {precision:.4f}\n")
            f.write(f"Recall: {recall:.4f}\n")
            f.write(f"F1-score: {f1:.4f}\n\n")
            f.write("Classification Report:\n")
            f.write(report)

        logger.info("Hasil evaluasi berhasil disimpan ke file face_recognition_evaluation_report.txt")

    finally:
        # Tutup koneksi database
        if conn:
            conn.close()
            logger.info("Koneksi database ditutup")

    logger.info("Program evaluasi pengenalan wajah selesai")

if __name__ == "__main__":
    main()
