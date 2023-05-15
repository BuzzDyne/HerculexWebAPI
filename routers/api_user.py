from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session

from database import get_db, User_TM, Role_TM


router = APIRouter(
    tags=['API User'],
    prefix="/api_user"
)

@router.get('/get_list')
def get_list(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    users = db.query(
        User_TM.id,
        User_TM.username,
        Role_TM.role_name,
        User_TM.created_dt,
        User_TM.last_login_dt
    ).join(
        Role_TM, User_TM.role_id == Role_TM.id
    ).all()

    user_list = [
        {
            'id'            : user.id,
            'username'      : user.username,
            'role_name'     : user.role_name,
            'created_dt': user.created_dt,
            'last_login_dt': user.last_login_dt,
        }
        for user in users
    ]

    return user_list