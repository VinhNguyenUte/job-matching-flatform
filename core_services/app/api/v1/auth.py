from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models import User
from app.schemas.user import UserCreate, UserResponse
from pydantic import BaseModel

router = APIRouter()

# C?u h?nh ðý?ng d?n l?y Token ð? tích h?p tr?c ti?p vào giao di?n Swagger UI (/docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# --- API ÐÃNG K? (REGISTER) ---
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Ki?m tra Email ð? t?n t?i hay chýa
    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này ð? ðý?c ðãng k? trên h? th?ng."
        )
    
    # 2. Ti?n hành m? hóa m?t kh?u và lýu database
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# --- API ÐÃNG NH?P (LOGIN) ---
# S? d?ng OAuth2PasswordRequestForm ð? l?y username (chính là email) và password d?ng Form-data
@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 1. Ki?m tra tài kho?n b?ng Email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài kho?n ho?c m?t kh?u không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. T?o JWT Token ch?a thông tin User ID (UUID)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# --- DEPENDENCY: L?Y THÔNG TIN USER HI?N T?I (GET CURRENT USER) ---
# Hàm này dùng ð? inject vào các API c?n b?o m?t nhý /cv/upload hay /applications
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên ðãng nh?p không h?p l? ho?c ð? h?t h?n.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Gi?i m? m? token JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Truy v?n thông tin User t? Database thông qua UUID bóc tách ðý?c t? Token
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# --- API TH? NGHI?M THÔNG TIN CÁ NHÂN (PROFILE ME) ---
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user