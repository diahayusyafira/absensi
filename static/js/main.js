/**
 * @file main.js
 * @description File JavaScript utama untuk aplikasi absensi karyawan.
 *              Berisi fungsi-fungsi untuk akses kamera, geolokasi, dan validasi form.
 * @author PT Matura Jaya
 * @version 1.0.0
 */

/**
 * ===================================
 * FUNGSI PENGENALAN WAJAH
 * ===================================
 */

/**
 * Memulai akses kamera untuk pengenalan wajah
 *
 * Fungsi ini mengakses kamera perangkat pengguna menggunakan MediaDevices API
 * dan menampilkan feed kamera pada elemen video dengan id 'camera'.
 *
 * @async
 * @returns {Promise<void>} - Promise yang diselesaikan ketika kamera berhasil diakses
 * @throws {Error} - Jika terjadi kesalahan saat mengakses kamera
 */
async function startCamera() {
    try {
        // Meminta akses ke kamera perangkat
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });

        // Mendapatkan elemen video dan menetapkan stream kamera
        const videoElement = document.getElementById('camera');
        videoElement.srcObject = stream;
    } catch (err) {
        // Menangani kesalahan jika kamera tidak dapat diakses
        console.error('Error accessing camera:', err);
        alert('Could not access the camera');
    }
}

/**
 * ===================================
 * FUNGSI GPS DAN GEOLOKASI
 * ===================================
 */

/**
 * Mendapatkan lokasi pengguna saat ini
 *
 * Fungsi ini menggunakan Geolocation API untuk mendapatkan koordinat GPS pengguna
 * dan mengisi nilai latitude dan longitude ke dalam input form.
 *
 * @returns {void}
 */
function getLocation() {
    // Memeriksa apakah browser mendukung Geolocation API
    if (navigator.geolocation) {
        // Mendapatkan posisi saat ini
        navigator.geolocation.getCurrentPosition(
            // Callback sukses
            position => {
                // Mengisi nilai latitude dan longitude ke dalam input form
                document.getElementById('latitude').value = position.coords.latitude;
                document.getElementById('longitude').value = position.coords.longitude;
            },
            // Callback error
            error => {
                // Menangani kesalahan jika lokasi tidak dapat diakses
                console.error('Error getting location:', error);
                alert('Could not get your location');
            }
        );
    } else {
        // Menampilkan pesan jika browser tidak mendukung Geolocation API
        alert('Geolocation is not supported by this browser');
    }
}

/**
 * ===================================
 * FUNGSI VALIDASI FORM
 * ===================================
 */

/**
 * Memvalidasi form sebelum pengiriman
 *
 * Fungsi ini memeriksa semua field yang ditandai sebagai required
 * dan menambahkan class 'error' jika field kosong.
 *
 * @returns {boolean} - true jika semua field valid, false jika ada field yang tidak valid
 */
function validateForm() {
    // Mendapatkan semua elemen dengan atribut 'required'
    const requiredFields = document.querySelectorAll('[required]');
    let isValid = true;

    // Memeriksa setiap field required
    requiredFields.forEach(field => {
        if (!field.value) {
            // Jika field kosong, tandai sebagai tidak valid
            isValid = false;
            field.classList.add('error');
        } else {
            // Jika field terisi, hapus tanda error
            field.classList.remove('error');
        }
    });

    // Mengembalikan status validasi keseluruhan
    return isValid;
}