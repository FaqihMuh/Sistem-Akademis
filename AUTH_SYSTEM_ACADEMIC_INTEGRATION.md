# Auth System Enhancement: Academic Data Integration

## Summary of Changes

This enhancement adds academic data linking to the authentication system by adding two optional fields to the User model:

- `nim`: Optional[str] - used only if role = "MAHASISWA"
- `kode_dosen`: Optional[str] - used only if role = "DOSEN"

Both fields can be NULL and are backward compatible with existing users.

## Files Modified

### 1. auth_system/models.py
- Added `nim` and `kode_dosen` columns to the User model
- Both fields are nullable (optional)

### 2. auth_system/schemas.py
- Updated `UserCreate` schema to include optional `nim` and `kode_dosen` fields
- Added `nim` and `kode_dosen` to `TokenResponse` schema
- Added `nim` and `kode_dosen` to `MeResponse` schema

### 3. auth_system/services.py
- Updated `create_user` function to properly handle `nim` and `kode_dosen` fields
- Only assigns `nim` if role is MAHASISWA
- Only assigns `kode_dosen` if role is DOSEN

### 4. auth_system/routes.py
- Updated login endpoint to include `nim` and `kode_dosen` in the response
- Updated register endpoint to include the new fields in the response
- Updated get_current_user_info endpoint to return the new fields

### 5. Alembic Migration
- Created migration file `002_add_nim_kode_dosen_to_users.py` 
- Adds `nim` and `kode_dosen` columns to the existing `users` table
- Migration applied successfully to the database

## API Changes

### Login Response
The login endpoint now returns additional fields:
```json
{
  "access_token": "...",
  "token_type": "bearer", 
  "role": "MAHASISWA",
  "nim": "2010230123",        // Provided if user is MAHASISWA
  "kode_dosen": null          // Provided if user is DOSEN
}
```

### Register Response
The register endpoint now returns the new academic fields:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "role": "DOSEN", 
  "nim": null,                // null if user is not MAHASISWA
  "kode_dosen": "D001"        // Provided if user is DOSEN
}
```

### Get User Info Response
The /me endpoint now includes academic fields:
```json
{
  "id": 1,
  "username": "student123",
  "role": "MAHASISWA",
  "nim": "2010230123",        // Provided if user is MAHASISWA
  "kode_dosen": null,         // Provided if user is DOSEN
  "created_at": "...",
  "updated_at": "..."
}
```

## Usage Examples

### Creating a Student User
```python
student_data = UserCreate(
    username="student123",
    password="password123", 
    role=RoleEnum.MAHASISWA,
    nim="2010230123"
)
```

### Creating a Lecturer User
```python
lecturer_data = UserCreate(
    username="lecturer001", 
    password="password123",
    role=RoleEnum.DOSEN,
    kode_dosen="D001"
)
```

### Creating an Admin User
```python
admin_data = UserCreate(
    username="admin_user",
    password="password123",
    role=RoleEnum.ADMIN
    # nim and kode_dosen will be None
)
```

## Backward Compatibility

- All existing users remain unaffected 
- Existing PMB/KRS/Schedule modules are not modified
- New fields are optional and can be NULL
- Migration preserves all existing data

## Testing

A test script (`test_new_fields.py`) was created and executed successfully to verify:
- Student users can be created with NIM
- Lecturer users can be created with kode_dosen
- Admin users have both fields as NULL
- All data is properly returned in API responses
- Backward compatibility with existing users is maintained