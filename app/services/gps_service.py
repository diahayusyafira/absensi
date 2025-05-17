# File: app/services/gps_service.py
# Deskripsi: Modul ini berisi layanan untuk validasi lokasi GPS dalam sistem absensi.
#            Menyediakan fungsi untuk mendapatkan alamat dari koordinat, menghitung jarak,
#            dan memvalidasi lokasi absensi karyawan.

# Import library untuk operasi geolokasi
from geopy.distance import geodesic  # Untuk menghitung jarak antara dua koordinat geografis
from geopy.geocoders import Nominatim  # Untuk reverse geocoding (koordinat ke alamat)

class GPSService:
    """
    Kelas untuk layanan GPS dan validasi lokasi.

    Kelas ini menyediakan fungsionalitas untuk:
    1. Mendapatkan alamat dari koordinat GPS (reverse geocoding)
    2. Menghitung jarak antara lokasi saat ini dengan lokasi kantor
    3. Memvalidasi apakah lokasi absensi berada dalam radius yang diizinkan

    Attributes:
        geolocator: Instance dari Nominatim untuk reverse geocoding
        office_location: Tuple (latitude, longitude) lokasi kantor
    """
    def __init__(self):
        """
        Inisialisasi layanan GPS.

        Membuat instance Nominatim geolocator dan menetapkan koordinat kantor default.
        """
        # Inisialisasi geolocator dengan user agent yang spesifik untuk aplikasi
        # User agent diperlukan oleh Nominatim untuk mengidentifikasi aplikasi
        self.geolocator = Nominatim(user_agent="matura_jaya_attendance")

        # Koordinat default lokasi kantor (PT Matura Jaya)
        # Format: (latitude, longitude)
        # Catatan: Ganti dengan koordinat kantor yang sebenarnya
        self.office_location = (-6.2088, 106.8456)  # Contoh koordinat Jakarta

    def get_current_location(self, latitude, longitude):
        """
        Mendapatkan informasi lokasi (alamat) dari koordinat GPS.

        Menggunakan reverse geocoding untuk mengubah koordinat menjadi alamat yang dapat dibaca manusia.

        Args:
            latitude (float): Koordinat latitude
            longitude (float): Koordinat longitude

        Returns:
            dict: Dictionary berisi alamat dan koordinat, atau None jika terjadi error
                Format: {
                    "address": string alamat lengkap,
                    "latitude": float latitude,
                    "longitude": float longitude
                }
        """
        try:
            # Melakukan reverse geocoding untuk mendapatkan alamat dari koordinat
            location = self.geolocator.reverse(f"{latitude}, {longitude}")

            # Mengembalikan dictionary dengan informasi lokasi
            return {
                "address": location.address,  # Alamat lengkap
                "latitude": latitude,         # Latitude yang diberikan
                "longitude": longitude        # Longitude yang diberikan
            }
        except Exception as e:
            # Jika terjadi error (misalnya tidak ada koneksi internet atau koordinat tidak valid)
            # Kembalikan None
            return None

    def is_within_radius(self, current_lat, current_lon, radius_km=0.5):
        """
        Memeriksa apakah lokasi saat ini berada dalam radius tertentu dari lokasi kantor.

        Args:
            current_lat (float): Latitude lokasi saat ini
            current_lon (float): Longitude lokasi saat ini
            radius_km (float, optional): Radius dalam kilometer. Default 0.5 km (500 meter)

        Returns:
            bool: True jika lokasi berada dalam radius, False jika di luar radius
        """
        # Buat tuple koordinat lokasi saat ini
        current_location = (current_lat, current_lon)

        # Hitung jarak antara lokasi saat ini dan lokasi kantor dalam kilometer
        # geodesic menghitung jarak berdasarkan bentuk bumi (lebih akurat daripada jarak Euclidean)
        distance = geodesic(current_location, self.office_location).kilometers

        # Kembalikan True jika jarak <= radius yang ditentukan, False jika tidak
        return distance <= radius_km

    def validate_attendance_location(self, latitude, longitude):
        """
        Memvalidasi apakah lokasi absensi berada dalam jangkauan yang diizinkan.

        Wrapper untuk is_within_radius yang mengembalikan pesan status.

        Args:
            latitude (float): Latitude lokasi absensi
            longitude (float): Longitude lokasi absensi

        Returns:
            tuple: (status, message)
                status (bool): True jika lokasi valid, False jika tidak
                message (str): Pesan status validasi
        """
        # Periksa apakah lokasi berada dalam radius yang diizinkan
        if not self.is_within_radius(latitude, longitude):
            # Jika di luar radius, kembalikan False dan pesan error
            return False, "Lokasi absensi di luar jangkauan kantor"

        # Jika dalam radius, kembalikan True dan pesan sukses
        return True, "Lokasi absensi valid"