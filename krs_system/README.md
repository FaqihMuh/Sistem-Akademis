# KRS System Module

This module implements a Course Registration System (KRS) that uses the same database as the PMB system.

## Tables

### matakuliah
- `id`: Primary key
- `kode`: Unique course code (e.g., "IF101")
- `nama`: Course name
- `sks`: Credit hours
- `semester`: Semester number (1-8)
- `hari`: Day of the week
- `jam_mulai`: Start time
- `jam_selesai`: End time
- `created_at`, `updated_at`: Timestamps

### prerequisite
- `id`: Primary key
- `matakuliah_id`: Foreign key to matakuliah (the course that has prerequisites)
- `prerequisite_id`: Foreign key to matakuliah (the prerequisite course)
- Note: Self-referencing table with both fields pointing to matakuliah.id

### krs
- `id`: Primary key
- `nim`: Student ID
- `semester`: Academic semester (e.g., "2023/2024-1")
- `status`: Enum (DRAFT, SUBMITTED, APPROVED, REVISION)
- `dosen_pa_id`: Advisor ID (nullable, stored as integer)
- `created_at`, `updated_at`: Timestamps

### krs_detail
- `id`: Primary key
- `krs_id`: Foreign key to krs
- `matakuliah_id`: Foreign key to matakuliah

## Relationships

- `krs_detail.krs_id` → `krs.id`
- `krs_detail.matakuliah_id` → `matakuliah.id`
- `prerequisite.matakuliah_id` and `prerequisite.prerequisite_id` → `matakuliah.id` (self-reference)

## Usage

The KRS system uses the same Base and database connection as the PMB system, ensuring both modules share the same database.

## Migrations

To apply migrations:
```bash
cd krs_system
alembic upgrade head
```

## Testing

Run the tests to verify functionality:
```bash
python -m krs_system.test_db_connectivity
python -m krs_system.test_comprehensive
```