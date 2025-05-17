# File: app/models/face_recognition.py
# Deskripsi: Modul ini berisi implementasi model pengenalan wajah menggunakan CNN (Convolutional Neural Network).
#            Model ini digunakan untuk mendeteksi dan memverifikasi wajah karyawan dalam sistem absensi.

# Import library untuk pengolahan gambar dan deep learning
import cv2  # OpenCV untuk pengolahan gambar dan deteksi wajah
import numpy as np  # NumPy untuk operasi array dan matriks
# TensorFlow dan Keras untuk deep learning
from tensorflow import keras  # Keras API untuk membangun model neural network
from tensorflow.keras import layers  # Layer-layer untuk membangun arsitektur model

class FaceRecognitionModel:
    """
    Kelas untuk model pengenalan wajah menggunakan CNN.

    Kelas ini menyediakan fungsionalitas untuk:
    1. Membangun model CNN untuk pengenalan wajah
    2. Mendeteksi wajah dalam gambar menggunakan Haar Cascade
    3. Memproses gambar untuk input ke model
    4. Melakukan prediksi/verifikasi wajah

    Attributes:
        model: Model CNN Keras untuk pengenalan wajah
        face_cascade: Haar Cascade Classifier untuk deteksi wajah
    """
    def __init__(self):
        """
        Inisialisasi model pengenalan wajah.

        Membangun model CNN dan memuat Haar Cascade Classifier untuk deteksi wajah.
        """
        # Membangun model CNN
        self.model = self._build_model()
        # Memuat Haar Cascade Classifier untuk deteksi wajah dari OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def _build_model(self):
        """
        Membangun arsitektur model CNN untuk pengenalan wajah.

        Arsitektur:
        - 3 blok konvolusional (Conv2D + MaxPooling2D)
        - Flatten layer untuk mengubah data 3D menjadi 1D
        - Dense layer dengan aktivasi ReLU
        - Dropout untuk mencegah overfitting
        - Output layer dengan aktivasi sigmoid (binary classification)

        Returns:
            Model Keras yang sudah dikompilasi
        """
        # Membangun arsitektur model sequential
        model = keras.Sequential([
            # Blok konvolusional pertama
            # 32 filter 3x3, aktivasi ReLU, input shape 100x100x3 (RGB image)
            layers.Conv2D(32, (3, 3), activation='relu', input_shape=(100, 100, 3)),
            # Max pooling 2x2 untuk mengurangi dimensi spasial
            layers.MaxPooling2D(2, 2),

            # Blok konvolusional kedua
            # 64 filter 3x3, aktivasi ReLU
            layers.Conv2D(64, (3, 3), activation='relu'),
            # Max pooling 2x2
            layers.MaxPooling2D(2, 2),

            # Blok konvolusional ketiga
            # 128 filter 3x3, aktivasi ReLU
            layers.Conv2D(128, (3, 3), activation='relu'),
            # Max pooling 2x2
            layers.MaxPooling2D(2, 2),

            # Flatten layer untuk mengubah data 3D menjadi 1D
            layers.Flatten(),

            # Dense layer dengan 512 neuron dan aktivasi ReLU
            layers.Dense(512, activation='relu'),
            # Dropout 50% untuk mencegah overfitting
            layers.Dropout(0.5),

            # Output layer dengan 1 neuron dan aktivasi sigmoid (binary classification)
            # Output 0-1 merepresentasikan probabilitas kecocokan wajah
            layers.Dense(1, activation='sigmoid')
        ])

        # Kompilasi model dengan optimizer Adam, loss function binary crossentropy,
        # dan metrik akurasi
        model.compile(optimizer='adam',
                     loss='binary_crossentropy',
                     metrics=['accuracy'])
        return model

    def detect_face(self, image):
        """
        Mendeteksi wajah dalam gambar menggunakan Haar Cascade Classifier.

        Args:
            image (numpy.ndarray): Gambar dalam format BGR (OpenCV default)

        Returns:
            numpy.ndarray: Array dengan format (x, y, w, h) untuk setiap wajah yang terdeteksi
                           x, y: koordinat pojok kiri atas
                           w, h: lebar dan tinggi kotak wajah
        """
        # Konversi gambar ke grayscale untuk deteksi wajah
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Deteksi wajah menggunakan Haar Cascade
        # Parameter: 1.3 = scale factor, 5 = minNeighbors
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        return faces

    def preprocess_image(self, image):
        """
        Memproses gambar untuk input ke model CNN.

        Langkah-langkah:
        1. Resize gambar menjadi 100x100 piksel
        2. Normalisasi nilai piksel (0-255 -> 0-1)
        3. Tambahkan dimensi batch

        Args:
            image (numpy.ndarray): Gambar wajah dalam format BGR

        Returns:
            numpy.ndarray: Gambar yang sudah diproses dengan shape (1, 100, 100, 3)
        """
        # Resize gambar menjadi 100x100 piksel (sesuai input shape model)
        resized = cv2.resize(image, (100, 100))
        # Normalisasi nilai piksel (0-255 -> 0-1)
        normalized = resized / 255.0
        # Tambahkan dimensi batch (model mengharapkan batch input)
        return np.expand_dims(normalized, axis=0)

    def predict(self, image):
        """
        Melakukan prediksi/verifikasi wajah menggunakan model CNN.

        Args:
            image (numpy.ndarray): Gambar wajah dalam format BGR

        Returns:
            float: Skor kecocokan wajah (0-1), di mana nilai lebih tinggi
                  menunjukkan probabilitas lebih tinggi bahwa wajah cocok
        """
        # Proses gambar untuk input ke model
        preprocessed = self.preprocess_image(image)
        # Lakukan prediksi menggunakan model
        prediction = self.model.predict(preprocessed)
        # Kembalikan skor kecocokan (nilai antara 0-1)
        return prediction[0][0]