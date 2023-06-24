from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
import bcrypt

from database import get_db, Order_TM, OrderItem_TR
from schemas import OrderUpdate

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
def get_order_details(id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    query = db.query(Order_TM, OrderItem_TR).\
        join(OrderItem_TR, Order_TM.ecom_order_id == OrderItem_TR.ecom_order_id).\
        filter(Order_TM.id == id).all()

    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ID not found')

    order_tm, order_items = zip(*query)
    result = {
        'order_data': order_tm[0],
        'order_items_data': order_items
    }

    return result

@router.patch('/id/{id}')
def update_order(id: str, data: OrderUpdate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)

    order.initial_input_dt  = data.initial_input_dt
    order.cust_phone_no     = data.cust_phone_no
    order.user_deadline_dt  = data.user_deadline_dt
    order.design_acc_dt     = data.design_acc_dt
    order.folder_url        = data.folder_url
    order.thumb_url         = data.thumb_url
    order.print_done_dt     = data.print_done_dt
    order.packing_done_dt   = data.packing_done_dt

    db.commit()
    db.refresh(order)

    return {"msg": f"Update successful"}


def check_if_order_exist(id, db: Session):
    query = db.query(Order_TM).filter(Order_TM.id == id).first()

    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ID not found')

    return query