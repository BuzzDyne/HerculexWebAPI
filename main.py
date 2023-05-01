from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from sqlalchemy.orm import Session
from datetime import timedelta
from routers import user, order, auth
from database import get_db
from database import Order_TM, HCXProcessSyncStatus_TM, User_TM
from pydantic import BaseModel

from _cred import AuthSecret

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
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
app.include_router(auth.router)

#region AuthJWT
class Settings(BaseModel):
    authjwt_secret_key: str = AuthSecret["SECRET_KEY"]
    authjwt_access_token_expires = timedelta(minutes=AuthSecret["ACCESS_TOKEN_EXPIRE_MINUTES"])
    
@AuthJWT.load_config
def get_config():
    return Settings()

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )
#endregion

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