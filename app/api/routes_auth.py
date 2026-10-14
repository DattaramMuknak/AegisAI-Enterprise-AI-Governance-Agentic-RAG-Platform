"""
/auth — registration and login issuing JWTs used by the RBAC layer.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.rbac import create_access_token, hash_password, verify_password
from app.core.database import get_db
from app.models.audit import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "viewer"


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    if payload.role not in ("admin", "analyst", "viewer"):
        raise HTTPException(400, "Invalid role")

    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(401, "Incorrect email or password")

    token = create_access_token(subject=str(user.id), role=str(user.role))
    return {"access_token": token, "token_type": "bearer", "role": user.role}
