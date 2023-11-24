from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
import bcrypt

from database import get_db, User_TM, Role_TM
from schemas import EditUserForm


router = APIRouter(tags=["API User"], prefix="/api_user")


@router.get("/get_designers")
def get_designers(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    # Query users with role_id = 2 (designer role)
    designers = (
        db.query(
            User_TM.id,
            User_TM.username,
            Role_TM.role_name,
            User_TM.created_dt,
            User_TM.last_login_dt,
        )
        .join(Role_TM, User_TM.role_id == Role_TM.id)
        .filter(Role_TM.id == 2)
        .all()
    )

    designer_list = [
        {
            "id": designer.id,
            "username": designer.username,
            "role_name": designer.role_name,
            "created_dt": designer.created_dt,
            "last_login_dt": designer.last_login_dt,
        }
        for designer in designers
    ]

    return designer_list


@router.get("/get_list")
def get_list(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    users = (
        db.query(
            User_TM.id,
            User_TM.username,
            Role_TM.role_name,
            User_TM.created_dt,
            User_TM.last_login_dt,
        )
        .join(Role_TM, User_TM.role_id == Role_TM.id)
        .all()
    )

    user_list = [
        {
            "id": user.id,
            "username": user.username,
            "role_name": user.role_name,
            "created_dt": user.created_dt,
            "last_login_dt": user.last_login_dt,
        }
        for user in users
    ]

    return user_list


@router.get("/id/{id}")
def get_user_by_id(
    id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    Authorize.jwt_required()

    user = (
        db.query(
            User_TM.id,
            User_TM.username,
            Role_TM.role_name,
            User_TM.created_dt,
            User_TM.last_login_dt,
        )
        .join(Role_TM, User_TM.role_id == Role_TM.id)
        .filter(User_TM.id == id)
        .first()
    )

    return {
        "id": user.id,
        "username": user.username,
        "role_name": user.role_name,
        "created_dt": user.created_dt,
        "last_login_dt": user.last_login_dt,
    }


@router.delete("/id/{id}")
def delete_user_by_id(
    id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    Authorize.jwt_required()

    query_res = db.query(User_TM).filter(User_TM.id == id)

    if not query_res.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ID not found"
        )

    query_res.delete()
    db.commit()

    return {"details": "Deleted User of ID " + id}


@router.patch("/id/{id}")
def edit_user_by_id(
    id: str,
    editForm: EditUserForm,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    user = db.query(User_TM).filter(User_TM.id == id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ID not found"
        )

    # Check if rolename exists
    role = db.query(Role_TM).filter(Role_TM.role_name == editForm.rolename).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{editForm.rolename}' not found!",
        )

    user.role_id = role.id

    if editForm.password:
        user.password = bcrypt.hashpw(
            editForm.password.encode("UTF-8"), bcrypt.gensalt()
        )

    db.commit()
    db.refresh(user)

    return {"msg": f"Update successful"}
