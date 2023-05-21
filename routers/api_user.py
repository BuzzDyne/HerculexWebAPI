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

@router.delete('/id/{id}')
def delete_user_by_id(id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    query_res = db.query(User_TM).filter(User_TM.id == id)

    if not query_res.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ID not found')

    query_res.delete()
    db.commit()

    return {'details': 'Deleted User of ID ' + id}