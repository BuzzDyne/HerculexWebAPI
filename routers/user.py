from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from typing_extensions import Annotated
from database import get_db
from database import User_TM, Role_TM
from schemas import User
from JWT import decode_token

from jose import JWTError

router = APIRouter(
    tags=['Users'],
    prefix="/user"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/loginv2")


credential_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
    except JWTError:
        raise credential_exception
    
    user = db.query(User_TM).filter(User_TM.username == payload.sub).first()
    
    if user is None:
        raise credential_exception
    return user

@router.get('/role/get_all')
def get_all(db: Session = Depends(get_db)):
    res = db.query(Role_TM).all()
    return res

@router.get('/get_all')
def get_all(db: Session = Depends(get_db)):
    res = db.query(User_TM).all()
    return res

@router.get('/id/{id}')
def get_by_id(id: str,  db: Session = Depends(get_db)):
    res = db.query(User_TM).filter(User_TM.id == id).first()
    return res

@router.post('/create')
def create_user(u: User, db: Session = Depends(get_db)):
    newUser = User_TM(
        created_dt      = datetime.now(),
        role            = u.role,
        username        = u.username,
        password        = u.password
    )

    db.add(newUser)
    db.commit()
    db.refresh(newUser)

    return newUser

@router.delete('/id/{id}')
def delete_user(id: str,  db: Session = Depends(get_db)):
    query_res = db.query(User_TM).filter(User_TM.id == id)

    if not query_res.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ID not found')

    query_res.delete()
    db.commit()

    return {'details': 'Deleted User of ID ' + id}
