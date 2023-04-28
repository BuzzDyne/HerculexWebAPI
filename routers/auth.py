from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi_jwt_auth import AuthJWT

from sqlalchemy.orm import Session
from datetime import datetime
import bcrypt

from database import get_db, User_TM, Role_TM
from schemas import LoginForm, RegisterForm

router = APIRouter(
    tags=['Auth'],
    prefix="/auth"
)


@router.post('/signup')
def signup(payload: RegisterForm = Body(default=None), Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
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
        "role_id"   : new_user.role_id
    }

    access_token = Authorize.create_access_token(subject=user.username, user_claims=token_payload)

    return {"token": access_token, "token-type": "bearer"}
    
@router.post('/login')
def login(payload: LoginForm, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)

    token_payload = {
        "role_id"   : user.role_id
    }

    access_token  = Authorize.create_access_token(subject=user.username, user_claims=token_payload)
    refresh_token = Authorize.create_refresh_token(subject=user.username)

    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post('/refresh')
def refresh(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    return {"access_token": new_access_token}

@router.get('/protected')
def protected(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    current_username = Authorize.get_jwt_subject()

    user = db.query(User_TM).filter(
        User_TM.username == current_username
    ).first()

    return user

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