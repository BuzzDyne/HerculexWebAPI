from fastapi import FastAPI
from sqlalchemy import Table, MetaData, create_engine
from _cred import Credentials

app = FastAPI()

# create a database connection
SQLALCHEMY_DB_URL = f'mysql://{Credentials["user"]}:{Credentials["password"]}!@{Credentials["host"]}/{Credentials["database"]}?charset=utf8mb4'
engine = create_engine(SQLALCHEMY_DB_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get('/query')
async def query_data():
    table = Table('order_tm', metadata, autoload=True, autoload_with=engine)
    query = table.select()
    return str(query)