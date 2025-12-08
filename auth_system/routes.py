from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth_system.schemas import UserCreate, UserLogin, TokenResponse
from auth_system.services import authenticate_user, create_user, create_access_token, hash_password
from auth_system.dependencies import get_current_user, role_required
from auth_system.models import User, RoleEnum
from pmb_system.database import get_db
from datetime import timedelta

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login endpoint to authenticate user and return JWT token."""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=180)  # 3 hours
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "nim": user.nim,
        "kode_dosen": user.kode_dosen
    }


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Register endpoint to create a new user (admin only)."""
    # Only admin users can register new users
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can register new users"
        )

    # Create the new user
    new_user = create_user(db, user_data)

    # Generate token for the newly created user
    access_token_expires = timedelta(minutes=180)  # 3 hours
    access_token = create_access_token(
        data={"sub": new_user.username, "role": new_user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": new_user.role,
        "nim": new_user.nim,
        "kode_dosen": new_user.kode_dosen
    }


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "nim": current_user.nim,
        "kode_dosen": current_user.kode_dosen,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }


@router.get("/users", dependencies=[Depends(role_required(RoleEnum.ADMIN))])
def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all users (admin only)."""
    users = db.query(User).all()
    return {"users": users}


@router.delete("/users/{user_id}", dependencies=[Depends(role_required(RoleEnum.ADMIN))])
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a user by ID (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Jangan izinkan admin untuk menghapus akun mereka sendiri
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully"}


@router.put("/users/{user_id}/password", dependencies=[Depends(role_required(RoleEnum.ADMIN))])
def update_user_password(
    user_id: int,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a user's password by ID (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Hash password baru
    hashed_password = hash_password(new_password)
    user.password_hash = hashed_password
    db.commit()

    return {"message": f"Password updated successfully for user {user.username}"}


@router.put("/me/password")
def update_current_user_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's password."""
    # Verifikasi password saat ini
    from auth_system.services import verify_password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Hash password baru
    hashed_new_password = hash_password(new_password)
    current_user.password_hash = hashed_new_password
    db.commit()

    return {"message": "Password updated successfully"}