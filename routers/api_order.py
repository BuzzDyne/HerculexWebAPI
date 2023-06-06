from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
import bcrypt

from database import get_db, Order_TM


router = APIRouter(
    tags=['API Order'],
    prefix="/api_order"
)


@router.get('/get_active_orders')
def get_active_orders(db: Session = Depends(get_db)):
    ecom_status_order_values = [100, 103, 220, 221, 400, 450, 500, 501, 530, 540, 600, 601, 690]
    res = db.query(Order_TM).filter(
        Order_TM.ecom_order_status.in_(ecom_status_order_values)).order_by(Order_TM.pltf_deadline_dt.asc()).all()
    return res

@router.get('/id/{id}')
def get_order_details(id: str, db: Session = Depends(get_db)):
    res = db.query(Order_TM).filter(Order_TM.id == id).first()

    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ID not found')

    return res