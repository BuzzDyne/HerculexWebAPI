from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from routers import user, order
from database import get_db
from database import Order_TM, HCXProcessSyncStatus_TM, User_TM
from schemas import User

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

app.include_router(user.router)
app.include_router(order.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get('/orders')
async def get_all_orders(db: Session = Depends(get_db)):
    res = db.query(Order_TM).all()
    return res

@app.get('/users')
async def get_all_users(db: Session = Depends(get_db)):
    res = db.query(User_TM).all()
    return res

@app.get('/syncstatus')
async def get_tokopedia_sync_status(db: Session = Depends(get_db)):
    res = db.query(HCXProcessSyncStatus_TM).filter(
        HCXProcessSyncStatus_TM.platform_name == "TOKOPEDIA" 
    ).first()
    
    return res