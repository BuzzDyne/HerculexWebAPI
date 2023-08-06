from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from datetime import datetime
from database import get_db, Order_TM
from schemas import Order, OrderActivity

router = APIRouter(
    tags=['Order'],
    prefix="/order"
)

@router.get('/get_all')
def get_all_order(db: Session = Depends(get_db)):
    res = db.query(Order_TM).all()
    return res

@router.get('/get_top_5')
def get_top_5_order(db: Session = Depends(get_db)):
    res = db.query(Order_TM).order_by(Order_TM.id.desc()).limit(5).all()
    return res

@router.get("/random_5_rows")
def read_random_5_rows(db: Session = Depends(get_db)):
    return db.query(Order_TM).order_by(func.random()).limit(5).all()

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