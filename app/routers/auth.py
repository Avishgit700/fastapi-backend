# app/routers/auth.py
import os, secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..security import verify_password, get_password_hash, create_access_token
from ..security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=schemas.UserOut)
def me(user = Depends(get_current_user)):  # 200 JSON
    return user

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = models.User(email=user_in.email, hashed_password=get_password_hash(user_in.password))
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/seed_demo")
def seed_demo(db: Session = Depends(get_db)):
    if os.getenv("DEMO_ENABLED", "true").lower() not in {"1","true","yes"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo seeding disabled")
    for _ in range(5):
        email = f"demo+{secrets.token_hex(3)}@mail.com"
        if not db.query(models.User).filter(models.User.email == email).first():
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate demo user")
    password = "secret123"
    user = models.User(email=email, hashed_password=get_password_hash(password))
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": user.email})
    return {"email": email, "password": password, "access_token": token, "token_type": "bearer"}
