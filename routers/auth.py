from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi_jwt_auth import AuthJWT

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import bcrypt

from database import get_db, User_TM, Role_TM
from schemas import LoginForm, RegisterForm

router = APIRouter(
    tags=['Auth'],
    prefix="/auth"
)

ACCESS_TOKEN_EXP = timedelta(minutes=60)
REFRESH_TOKEN_EXP= timedelta(days=7)

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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{payload.rolename}' not found!")


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

    return {"msg": f"Created user '{payload.username}'"}
    
@router.post('/login')
def login(payload: LoginForm, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)

    token_payload = {
        "role_id"   : user.role_id,
        "user_id"   : user.id
    }

    user.last_login_dt = datetime.now()
    db.commit()
    db.refresh(user)

    access_token  = Authorize.create_access_token(subject=user.username, user_claims=token_payload, expires_time=ACCESS_TOKEN_EXP)
    refresh_token = Authorize.create_refresh_token(subject=user.username, expires_time=REFRESH_TOKEN_EXP)

    return {"access_token": access_token, "refresh_token": refresh_token}

@router.get('/refresh')
def refresh(Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user, expires_time=ACCESS_TOKEN_EXP)
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