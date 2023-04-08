from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from datetime import datetime
from database import get_db, Order_TM, OrderActivity_TR
from schemas import Order, OrderActivity

router = APIRouter(
    tags=['Order'],
    prefix="/order"
)


@router.get('/get_all_activities')
def get_all_order(db: Session = Depends(get_db)):
    res = db.query(OrderActivity_TR).all()
    return res

@router.get('/get_all')
def get_all_order(db: Session = Depends(get_db)):
    res = db.query(Order_TM).all()
    return res

@router.get('/{id}/activity')
def get_all_orderactivities_by_orderid(id: str, db: Session = Depends(get_db)):
    res = db.query(OrderActivity_TR).filter(OrderActivity_TR.order_id == id).order_by(OrderActivity_TR.id.asc()).all()
    return res


@router.post('/{id}/activity')
def create_order_activity(id: str, payload: OrderActivity, db: Session = Depends(get_db)):
    newAct = OrderActivity_TR(
        order_id    = id,
        creator_id  = payload.creator_id,
        message     = payload.message,
        created_dt  = datetime.now()
    )

    db.add(newAct)
    db.commit()
    db.refresh(newAct)

    return newAct

@router.get('/{id}')
def get_order_by_id(id: str,  db: Session = Depends(get_db)):
    res = db.query(Order_TM).filter(Order_TM.id == id).first()
    return res

@router.patch('/{id}', status_code=status.HTTP_202_ACCEPTED)
def update_order(id: str, payload: Order, db: Session = Depends(get_db)):
    q_res = db.query(Order_TM).filter(Order_TM.id == id)

    if not q_res.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Order ID not found')

    stored_data = jsonable_encoder(q_res.first())
    stored_model = Order(**stored_data)

    new_data = payload.dict(exclude_unset=True)
    updated = stored_model.copy(update=new_data)
    updated.last_updated_ts = datetime.now()

    stored_data.update(updated)

    q_res.update(stored_data)

    db.commit()

    return updated