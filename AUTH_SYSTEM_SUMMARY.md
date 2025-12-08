"""
Ringkasan Sistem Autentikasi dan Dashboard Web
================================================

Sistem ini mencakup komponen-komponen berikut:

1. Folder auth_system/
   - models.py: Mendefinisikan model User dan RoleEnum
   - schemas.py: Mendefinisikan skema Pydantic untuk request/response
   - services.py: Berisi fungsi-fungsi untuk otentikasi dan manajemen token
   - dependencies.py: Berisi dependencies FastAPI untuk proteksi endpoint
   - routes.py: Mendefinisikan endpoint-endpoint autentikasi
   - __init__.py: Membuat folder menjadi package Python

2. Folder web_dashboard/
   - app.py: Aplikasi FastAPI untuk tampilan web dashboard
   - templates/: Folder berisi file-file HTML template
     - base.html: Template dasar untuk semua halaman
     - login.html: Halaman login
     - admin_dashboard.html: Dashboard untuk admin
     - dosen_dashboard.html: Dashboard untuk dosen
     - mahasiswa_dashboard.html: Dashboard untuk mahasiswa
     - pmb_data.html: Halaman data PMB (untuk admin)
     - krs_data.html: Halaman data KRS (untuk admin)
     - schedule_data.html: Halaman data jadwal (untuk admin)
   - static/style.css: File CSS untuk styling

3. Integrasi ke main.py:
   - Endpoint /api/auth/... untuk sistem autentikasi API
   - Mounting dashboard di /dashboard path

4. Endpoint Autentikasi yang Tersedia:
   - POST /api/auth/login: Login pengguna dan mendapatkan JWT token
   - POST /api/auth/register: Registrasi pengguna baru (admin only)
   - GET /api/auth/me: Mendapatkan informasi pengguna saat ini
   - GET /api/auth/users: Mendapatkan semua pengguna (admin only)
   - DELETE /api/auth/users/{id}: Menghapus pengguna (admin only)
   - PUT /api/auth/users/{id}/password: Memperbarui password pengguna (admin only)
   - PUT /api/auth/me/password: Memperbarui password pengguna saat ini

5. Role-based Access Control:
   - ADMIN: Dapat mengakses semua fitur, termasuk manajemen pengguna
   - DOSEN: Dapat mengakses fitur terkait dosen
   - MAHASISWA: Dapat mengakses fitur terkait mahasiswa

6. Dashboard Web:
   - Halaman login dengan form otentikasi
   - Dashboard berbeda untuk setiap role pengguna
   - Integrasi dengan API untuk mendapatkan data PMB, KRS, dan Jadwal
   - Sistem session untuk menjaga status login

Cara Penggunaan:
1. Jalankan aplikasi dengan: uvicorn main:app --reload
2. Akses dashboard di http://localhost:8000/dashboard/login
3. Gunakan akun default:
   - Admin: username=admin, password=admin123
   - Dosen: username=dosen, password=dosen123
   - Mahasiswa: username=mahasiswa, password=mahasiswa123

Fitur Keamanan:
- Password di-hash menggunakan bcrypt
- Otentikasi berbasis JWT token
- Proteksi endpoint dengan role-based access
- Validasi input menggunakan Pydantic