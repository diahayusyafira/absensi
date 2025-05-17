# Panduan Pengenalan Wajah untuk Sistem Absensi

Dokumen ini berisi panduan untuk menggunakan fitur pengenalan wajah dalam sistem absensi karyawan PT Matura Jaya.

## Daftar Isi

1. [Pengenalan](#pengenalan)
2. [Persyaratan Sistem](#persyaratan-sistem)
3. [Instalasi Library](#instalasi-library)
4. [Pengumpulan Data Training](#pengumpulan-data-training)
5. [Pengujian Pengenalan Wajah](#pengujian-pengenalan-wajah)
6. [Evaluasi Performa dengan F1-score](#evaluasi-performa-dengan-f1-score)
7. [Troubleshooting](#troubleshooting)

## Pengenalan

Sistem absensi PT Matura Jaya menggunakan teknologi pengenalan wajah untuk memverifikasi identitas karyawan saat melakukan absensi. Teknologi ini memungkinkan karyawan untuk melakukan absensi tanpa perlu memasukkan username dan password.

Sistem pengenalan wajah ini menggunakan library `face_recognition` yang dibangun di atas `dlib` untuk mendeteksi dan mengenali wajah karyawan. Library ini menggunakan model deep learning untuk mengekstrak fitur wajah dan membandingkannya dengan data yang tersimpan di database.

## Persyaratan Sistem

Untuk menggunakan fitur pengenalan wajah, Anda memerlukan:

1. Python 3.6 atau lebih baru
2. Webcam yang terhubung ke komputer
3. Library berikut:
   - OpenCV
   - face_recognition
   - dlib
   - numpy
   - sqlite3
   - scikit-learn (untuk evaluasi performa)

## Instalasi Library

Untuk menginstal library yang diperlukan, jalankan perintah berikut:

```bash
# Instal CMake (diperlukan untuk dlib)
pip install cmake

# Instal dlib
pip install dlib

# Instal face_recognition
pip install face_recognition

# Instal OpenCV
pip install opencv-python

# Instal numpy
pip install numpy

# Instal scikit-learn untuk evaluasi performa
pip install scikit-learn
```

## Pengumpulan Data Training

Untuk mengumpulkan data wajah karyawan yang akan digunakan untuk pengenalan wajah, gunakan script `face_training.py`.

### Langkah-langkah:

1. Pastikan database sudah berisi data karyawan (nama, email, dll.)
2. Jalankan script dengan perintah:
   ```bash
   python face_training.py
   ```
3. Script akan menampilkan daftar karyawan yang terdaftar di database
4. Pilih nomor karyawan yang akan diambil data wajahnya
5. Arahkan wajah karyawan ke webcam
6. Tekan tombol 'c' untuk mengambil gambar wajah
7. Script akan menyimpan gambar wajah dan encoding wajah ke database
8. Ulangi langkah 4-7 untuk karyawan lainnya
9. Tekan tombol '0' untuk keluar dari program

### Catatan Penting:

- Pastikan wajah karyawan terlihat jelas dan tidak tertutup (tidak memakai masker, kacamata hitam, dll.)
- Pastikan pencahayaan cukup baik
- Pastikan hanya ada satu wajah dalam frame
- Gambar wajah akan disimpan di folder `face_data` untuk referensi
- Encoding wajah akan disimpan di tabel `face_encoding` di database

## Pengujian Pengenalan Wajah

Untuk menguji apakah sistem pengenalan wajah berfungsi dengan baik, gunakan script `face_recognition_test.py`.

### Langkah-langkah:

1. Jalankan script dengan perintah:
   ```bash
   python face_recognition_test.py
   ```
2. Arahkan wajah ke webcam
3. Script akan mendeteksi wajah dan menampilkan nama karyawan jika wajah dikenali
4. Tekan tombol 'q' untuk keluar dari program

## Evaluasi Performa dengan F1-score

Untuk mengevaluasi performa sistem pengenalan wajah secara kuantitatif, gunakan script `face_recognition_evaluation.py`. Script ini menggunakan metrik F1-score yang menggabungkan precision dan recall untuk mengukur akurasi sistem.

### Apa itu F1-score?

F1-score adalah metrik evaluasi yang menggabungkan precision dan recall:

- **Precision**: Persentase prediksi positif yang benar (TP / (TP + FP))
- **Recall**: Persentase kasus positif yang berhasil diidentifikasi (TP / (TP + FN))
- **F1-score**: Rata-rata harmonik dari precision dan recall (2 * (precision * recall) / (precision + recall))

F1-score bernilai antara 0 dan 1, di mana 1 menunjukkan performa sempurna.

### Langkah-langkah Evaluasi:

1. Jalankan script dengan perintah:
   ```bash
   python face_recognition_evaluation.py
   ```

2. Pilih mode evaluasi:
   - Mode 1: Evaluasi dengan gambar yang sudah ada di folder `test_data`
   - Mode 2: Ambil gambar baru untuk evaluasi

3. Jika memilih mode 2, pilih karyawan dan ambil beberapa gambar untuk pengujian

4. Script akan mengevaluasi performa sistem dan menampilkan:
   - Precision
   - Recall
   - F1-score
   - Classification report lengkap

5. Hasil evaluasi juga akan disimpan ke file `face_recognition_evaluation_report.txt`

### Interpretasi Hasil:

- F1-score > 0.9: Performa sangat baik
- F1-score 0.8-0.9: Performa baik
- F1-score 0.7-0.8: Performa cukup
- F1-score < 0.7: Performa kurang, perlu perbaikan

### Tips Meningkatkan F1-score:

1. Tambahkan lebih banyak data training dengan variasi pencahayaan, sudut, dan ekspresi wajah
2. Pastikan kualitas gambar training baik (pencahayaan cukup, wajah terlihat jelas)
3. Sesuaikan parameter tolerance pada fungsi `compare_faces` (nilai default 0.5)
4. Gunakan teknik augmentasi data untuk memperkaya data training

## Troubleshooting

### Wajah Tidak Terdeteksi

Jika wajah tidak terdeteksi:
- Pastikan pencahayaan cukup baik
- Pastikan wajah terlihat jelas dan tidak tertutup
- Pastikan webcam berfungsi dengan baik

### Wajah Terdeteksi Tapi Tidak Dikenali

Jika wajah terdeteksi tapi tidak dikenali:
- Pastikan data wajah karyawan sudah diambil menggunakan `face_training.py`
- Pastikan data wajah tersimpan dengan benar di database
- Coba ambil ulang data wajah dengan pencahayaan yang lebih baik

### Error saat Menjalankan Script

Jika terjadi error saat menjalankan script:
- Pastikan semua library sudah terinstal dengan benar
- Pastikan database sudah ada dan berisi data karyawan
- Periksa log error untuk informasi lebih lanjut

## Kontak

Jika Anda memiliki pertanyaan atau mengalami masalah, silakan hubungi tim IT PT Matura Jaya.

---

Dokumen ini dibuat untuk membantu pengguna dalam menggunakan fitur pengenalan wajah pada sistem absensi karyawan PT Matura Jaya.
