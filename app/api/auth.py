import random
import string
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db import get_db
from app.models import models
from app.schemas import schemas
from app.config import settings
from passlib.context import CryptContext
from jose import JWTError, jwt

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60) # Aumentado a 60 min
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=user_id)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=schemas.UserResponse, deprecated=True)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Este endpoint se mantiene pero se marca como obsoleto, favoreciendo el registro por OTP
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    password_bytes = user.password.encode('utf-8')
    truncated_password = password_bytes[:72]
    
    hashed_password = pwd_context.hash(truncated_password)
    db_user = models.User(
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Se busca por email o telefono. El username del form puede ser cualquiera de los dos.
    user = db.query(models.User).filter(
        (models.User.email == form_data.username) | (models.User.phone_number == form_data.username)
    ).first()
    if not user or not user.password_hash or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Nuevos Endpoints para registro por Teléfono (OTP) ---

@router.post("/otp/request", response_model=schemas.PhoneVerificationResponse)
def request_otp(req: schemas.PhoneVerificationRequest, db: Session = Depends(get_db)):
    """
    Genera un código OTP para un número de teléfono y lo devuelve para simulación.
    """
    # En producción, aquí se haría la llamada a la API de SMS (Twilio, etc.)
    otp_code = "".join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Guardar o actualizar el código de verificación
    verification = db.query(models.PhoneVerification).filter_by(phone_number=req.phone_number).first()
    if verification:
        verification.otp_code = otp_code
        verification.expires_at = expires_at
    else:
        verification = models.PhoneVerification(
            phone_number=req.phone_number,
            otp_code=otp_code,
            expires_at=expires_at,
        )
        db.add(verification)
    
    db.commit()

    # Devolvemos el código para que el frontend pueda simular el flujo
    return {"phone_number": req.phone_number, "otp_code": otp_code}

@router.post("/otp/verify", response_model=schemas.Token)
def verify_otp_and_register(req: schemas.PhoneVerificationVerify, db: Session = Depends(get_db)):
    """
    Verifica un código OTP y, si es correcto, crea/loguea al usuario.
    """
    verification = db.query(models.PhoneVerification).filter_by(phone_number=req.phone_number).first()

    if not verification or verification.otp_code != req.otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    if datetime.utcnow() > verification.expires_at:
        raise HTTPException(status_code=400, detail="OTP code has expired")

    # El código es válido, buscar o crear al usuario
    user = db.query(models.User).filter_by(phone_number=req.phone_number).first()
    if not user:
        user = models.User(
            phone_number=req.phone_number,
            full_name=req.full_name,
            # email y password son nulos
        )
        db.add(user)
    
    # Eliminar el código de verificación usado
    db.delete(verification)
    db.commit()
    db.refresh(user)

    # Crear token y devolverlo
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

