from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_to_pydantic import sqlalchemy_to_pydantic

from _cred import Credentials

SQLALCHEMY_DB_URL = f'mysql+pymysql://{Credentials["user"]}:{Credentials["password"]}@{Credentials["host"]}/{Credentials["database"]}?charset=utf8mb4'

engine = create_engine(SQLALCHEMY_DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = automap_base()

Base.prepare(engine, reflect=True)

Order_TM                = Base.classes.order_tm
HCXProcessSyncStatus_TM = Base.classes.hcxprocesssyncstatus_tm
User_TM                 = Base.classes.user_tm

Order_TM_schema         = sqlalchemy_to_pydantic(Order_TM)
User_TM_schema          = sqlalchemy_to_pydantic(User_TM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()