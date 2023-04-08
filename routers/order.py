from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database import Order_TM

router = APIRouter(
    tags=['Order'],
    prefix="/order"
)

@router.get('/get_all')
def get_all(db: Session = Depends(get_db)):
    res = db.query(Order_TM).all()
    return res

@router.get('/id/{id}')
def get_by_id(id: str,  db: Session = Depends(get_db)):
    res = db.query(Order_TM).filter(Order_TM.id == id).first()
    return res