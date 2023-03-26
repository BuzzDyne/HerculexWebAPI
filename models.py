from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, DECIMAL
from sqlalchemy.orm import relationship

from database import Base

class UserTm(Base):
    __tablename__ = 'user_tm'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_dt = Column(DateTime)
    last_login_dt = Column(DateTime)
    role = Column(String(20))
    username = Column(String(20))
    password = Column(String(40))

class OrderTm(Base):
    __tablename__ = 'order_tm'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ecommerce_code = Column(String(1))
    cust_phone_no = Column(String(50))
    feeding_dt = Column(DateTime)
    last_updated_ts = Column(DateTime)
    user_deadline_dt = Column(DateTime)
    pltf_deadline_dt = Column(DateTime)
    design_acc_dt = Column(DateTime)
    print_done_dt = Column(DateTime)
    buyer_id = Column(String(50))
    ecom_order_id = Column(String(100))
    ecom_order_status = Column(String(10))
    invoice_ref = Column(String(50))

class OrderItemTr(Base):
    __tablename__ = 'orderitem_tr'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ecom_order_id = Column(Integer, nullable=False) # Order.id
    ecom_product_id = Column(String(200)) # Dari eCommerce
    product_name = Column(String(200))
    quantity = Column(Integer)
    product_price = Column(DECIMAL)

class OrderThumbnailTr(Base):
    __tablename__ = 'orderthumbnail_tr'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False) # Order.id
    url = Column(String(200))
    description = Column(String(200))
    created_dt = Column(DateTime)

class OrderActivityTr(Base):
    __tablename__ = 'orderactivity_tr'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False) # Order.id
    creator_id = Column(Integer, nullable=False) # User.id
    message = Column(Text)
    created_dt = Column(DateTime)

class GlobalParamTm(Base):
    __tablename__ = 'globalparam_tm'
    id = Column(Integer, primary_key=True, autoincrement=True)
    app_name = Column(String(200))
    param_name1 = Column(String(200))
    param_value1 = Column(String(200))
    param_name2 = Column(String(200))
    param_value2 = Column(String(200))
    param_name3 = Column(String(200))
    param_value3 = Column(String(200))

class GlobalLoggingTH(Base):
    __tablename__ = 'globallogging_TH'
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_name = Column(String(50))
    activity_date = Column(DateTime)
    activity_type = Column(String(50))
    description = Column(String(255))