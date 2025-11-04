# Sistem Penerimaan Mahasiswa Baru (PMB)

Sistem ini dirancang untuk mengelola pendaftaran calon mahasiswa baru dengan berbagai jalur masuk.

## Struktur Database

### Tabel `program_studi`
- `id`: Integer (Primary Key)
- `kode`: String(3) - Kode program studi (unik, 3 karakter)
- `nama`: String(255) - Nama program studi
- `fakultas`: String(255) - Fakultas yang menaungi

### Tabel `calon_mahasiswa`
- `id`: Integer (Primary Key)
- `nama_lengkap`: String(255) - Nama lengkap calon mahasiswa
- `email`: String(255) - Email (unik dan valid)
- `phone`: String(15) - Nomor telepon (format Indonesia: 08... dengan 10-13 digit)
- `tanggal_lahir`: DateTime - Tanggal lahir
- `alamat`: String(500) - Alamat calon mahasiswa
- `program_studi_id`: Integer (Foreign Key ke `program_studi.id`)
- `jalur_masuk`: Enum (SNBP, SNBT, Mandiri)
- `status`: Enum (pending, approved, rejected) - Default: pending
- `created_at`: DateTime - Timestamp pembuatan
- `approved_at`: DateTime (nullable) - Timestamp persetujuan

## Validasi

### Email
- Harus unik
- Format harus valid (mengikuti standar email)

### Phone
- Harus mengikuti format Indonesia
- Harus dimulai dengan "08"
- Panjang antara 10-13 digit (setelah menghapus spasi atau tanda hubung)

## Migrasi Database

1. Instal dependensi:
   ```
   pip install -r requirements.txt
   ```

2. Jalankan migrasi:
   ```
   alembic upgrade head
   ```

## API Endpoints

### PMB Module Endpoints (New)

- `POST /api/pmb/register` - Mendaftarkan calon mahasiswa baru, status default = 'pending'
- `PUT /api/pmb/approve/{id}` - Menyetujui calon mahasiswa, menghasilkan NIM dengan format [tahun][kode_prodi][nomor_urut]
- `GET /api/pmb/status/{id}` - Menampilkan data pendaftar dan statusnya
- `GET /api/pmb/stats` - Menampilkan jumlah pendaftar per jalur_masuk
- `POST /api/pmb/program-studi` - Membuat program studi baru
- `GET /api/pmb/program-studi` - Mendapatkan semua program studi
- `GET /api/pmb/program-studi/{id}` - Mendapatkan program studi berdasarkan ID

### Legacy Endpoints

- `POST /calon-mahasiswa/` - Membuat pendaftaran calon mahasiswa baru

## Teknologi

- Python 3.11
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL (disarankan)

## Instalasi

1. Buat virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # atau
   venv\Scripts\activate  # Windows
   ```

2. Instal dependensi:
   ```
   pip install -r requirements.txt
   ```

3. Jalankan aplikasi:
   ```
   uvicorn main:app --reload
   ```