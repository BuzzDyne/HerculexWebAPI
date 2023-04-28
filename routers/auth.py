from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from datetime import datetime
import bcrypt

from database import get_db, User_TM, Role_TM
from schemas import LoginForm, RegisterForm
import JWT

router = APIRouter(
    tags=['Auth'],
    prefix="/auth"
)

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post('/signup')
def signup(payload: RegisterForm = Body(default=None), db: Session = Depends(get_db)):
    # Check if username exists
    user = db.query(User_TM).filter(
        User_TM.username == payload.username
    ).all()

    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Username '{payload.username}' already exist!")

    # Check if rolename exists
    role = db.query(Role_TM).filter(
        Role_TM.role_name == payload.rolename
    ).first()

    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{payload.username}' not found!")


    # Add user to DB
    new_user = User_TM(
        username    = payload.username,
        password    = bcrypt.hashpw(payload.password.encode("UTF-8"), bcrypt.gensalt()),
        role_id     = role.id,
        created_dt  = datetime.now()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token_payload = {
        "sub"       : new_user.username,
        "role_id"   : new_user.role_id
    }

    access_token = JWT.create_access_token(data=token_payload)

    return {"token": access_token, "token-type": "bearer"}
    

@router.post('/login')
def login(payload: LoginForm, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)

    token_payload = {
        "username"  : user.username,
        "role_id"   : user.role_id
    }

    access_token = JWT.create_access_token(data=token_payload)

    return {"token": access_token, "token-type": "bearer"}

@router.post('/loginv2')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    
    token_payload = {
        "username"  : user.username,
        "role_id"   : user.role_id
    }

    access_token = JWT.create_access_token(data=token_payload)

    return {"token": access_token, "token-type": "bearer"}


def authenticate_user(db: Session, username, pwd):
    user = db.query(User_TM).filter(
        User_TM.username == username
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Username not found!")

    db_pw = user.password if isinstance(user.password, bytes) else user.password.encode("utf-8")

    if not bcrypt.checkpw(pwd.encode("utf-8"), db_pw):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Incorrect password!")
    
    return user