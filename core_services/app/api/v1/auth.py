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

# Cáº¥u hÃ¬nh Ä‘Æ°á»ng dáº«n láº¥y Token Ä‘á»ƒ tÃ­ch há»£p trá»±c tiáº¿p vÃ o giao diá»‡n Swagger UI (/docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# --- API ÄÄ‚NG KÃ (REGISTER) ---
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Kiá»ƒm tra Email Ä‘Ã£ tá»“n táº¡i hay chÆ°a
    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email nÃ y Ä‘Ã£ Ä‘Æ°á»£c Ä‘Äƒng kÃ½ trÃªn há»‡ thá»‘ng."
        )
    
    # 2. Tiáº¿n hÃ nh mÃ£ hÃ³a máº­t kháº©u vÃ  lÆ°u database
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


# --- API ÄÄ‚NG NHáº¬P (LOGIN) ---
# Sá»­ dá»¥ng OAuth2PasswordRequestForm Ä‘á»ƒ láº¥y username (chÃ­nh lÃ  email) vÃ  password dáº¡ng Form-data
@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 1. Kiá»ƒm tra tÃ i khoáº£n báº±ng Email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TÃ i khoáº£n hoáº·c máº­t kháº©u khÃ´ng chÃ­nh xÃ¡c.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. Táº¡o JWT Token chá»©a thÃ´ng tin User ID (UUID)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# --- DEPENDENCY: Láº¤Y THÃ”NG TIN USER HIá»†N Táº I (GET CURRENT USER) ---
# HÃ m nÃ y dÃ¹ng Ä‘á»ƒ inject vÃ o cÃ¡c API cáº§n báº£o máº­t nhÆ° /cv/upload hay /applications
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="PhiÃªn Ä‘Äƒng nháº­p khÃ´ng há»£p lá»‡ hoáº·c Ä‘Ã£ háº¿t háº¡n.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Giáº£i mÃ£ mÃ£ token JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Truy váº¥n thÃ´ng tin User tá»« Database thÃ´ng qua UUID bÃ³c tÃ¡ch Ä‘Æ°á»£c tá»« Token
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# --- API THá»¬ NGHIá»†M THÃ”NG TIN CÃ NHÃ‚N (PROFILE ME) ---
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
