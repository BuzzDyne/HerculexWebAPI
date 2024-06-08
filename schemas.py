from typing import List, Optional
from pydantic import BaseModel


# User Table
class User(BaseModel):
    id: Optional[int]
    created_dt: Optional[str]
    last_login_dt: Optional[str]
    role: Optional[str]
    username: Optional[str]
    password: Optional[str]

    class Config:
        orm_mode = True


# Order Table
class Order(BaseModel):
    id: Optional[int]
    ecommerce_code: Optional[str]
    cust_phone_no: Optional[str]
    feeding_dt: Optional[str]
    last_updated_ts: Optional[str]
    user_deadline_prd: Optional[str]
    pltf_deadline_dt: Optional[str]
    design_sub_dt: Optional[str]
    design_acc_dt: Optional[str]
    print_done_dt: Optional[str]
    buyer_id: Optional[str]
    ecom_order_id: Optional[str]
    ecom_order_status: Optional[str]
    invoice_ref: Optional[str]

    class Config:
        orm_mode = True


# Order Item Table
class OrderItem(BaseModel):
    id: Optional[int]
    ecom_order_id: Optional[int]
    ecom_product_id: Optional[str]
    product_name: Optional[str]
    quantity: Optional[int]
    product_price: Optional[float]

    class Config:
        orm_mode = True


# Order Thumbnail Table
class OrderThumbnail(BaseModel):
    id: Optional[int]
    order_id: Optional[int]
    url: Optional[str]
    description: Optional[str]
    created_dt: Optional[str]

    class Config:
        orm_mode = True


# Order Activity Table
class OrderActivity(BaseModel):
    id: Optional[int]
    order_id: Optional[int]
    creator_id: Optional[int]
    message: Optional[str]
    created_dt: Optional[str]

    class Config:
        orm_mode = True


# Global Parameter Table
class GlobalParam(BaseModel):
    id: Optional[int]
    app_name: Optional[str]
    param_name1: Optional[str]
    param_value1: Optional[str]
    param_name2: Optional[str]
    param_value2: Optional[str]
    param_name3: Optional[str]
    param_value3: Optional[str]

    class Config:
        orm_mode = True


# Global Logging Table
class GlobalLogging(BaseModel):
    id: Optional[int]
    application_name: Optional[str]
    activity_date: Optional[str]
    activity_type: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True


# Login Form
class LoginForm(BaseModel):
    username: str
    password: str


# Register Form
class RegisterForm(BaseModel):
    username: str
    password: str
    rolename: str


# Register Form
class EditUserForm(BaseModel):
    rolename: str
    password: str


# Order Update Form
class OrderUpdate(BaseModel):
    initial_input_dt: Optional[str]
    cust_phone_no: Optional[str]
    user_deadline_prd: Optional[str]
    design_sub_dt: Optional[str]
    design_acc_dt: Optional[str]
    google_folder_url: Optional[str]
    google_file_url: Optional[str]
    print_done_dt: Optional[str]
    packing_done_dt: Optional[str]
    user_id: Optional[int]


# Order Submit URL Form
class OrderSubmitURL(BaseModel):
    folder_url: Optional[str]
    thumb_file_url: Optional[str]
    user_id: Optional[int]


# Order Submit URL Form
class OrderUpdateDatePayload(BaseModel):
    user_id: Optional[int]
    date: Optional[str]


# Order Initial Input Form
class OrderInitialInputPayload(BaseModel):
    user_id: Optional[int]
    pic_user_id: Optional[str]
    cust_phone_no: Optional[str]
    user_deadline_prd: Optional[str]


# Order PIC Form
class OrderPICUpdatePayload(BaseModel):
    user_id: Optional[int]
    pic_id: Optional[int]


# Order Comment Form
class OrderCommentCreatePayload(BaseModel):
    user_id: int
    comment: str


# Manual Order Form
class ManualOrderPayload(BaseModel):
    platform_code: str
    product_name: str
    quantity: int
    price: int
    user_id: int


class UserIDPayload(BaseModel):
    user_id: int


class CreateBatchFilePayload(BaseModel):
    designer_id: int
    order_ids: List[int]
    remarks: Optional[str]


class StringPayload(BaseModel):
    payload: str


class StringPayloadWithUserID(BaseModel):
    payload: str
    user_id: int


class OrderDocumentItem(BaseModel):
    item_name: str
    item_price: float
    item_qty: int


class OrderDocument(BaseModel):
    order_id: Optional[int]
    doc_type: str
    doc_number: str
    customer_name: str
    customer_addr_1: str
    customer_addr_2: str
    customer_addr_3: str
    customer_addr_4: str
    cust_phone: str
    cust_fax: str
    due_date: str
    items: List[OrderDocumentItem]
    discount: float


class OrderankuSeller(BaseModel):
    id: Optional[int]
    seller_name: str
    seller_phone: str


class OrderankuSellerEditForm(BaseModel):
    seller_name: Optional[str]
    seller_phone: Optional[str]


class OrderankuItemCreateForm(BaseModel):
    recipient_name: str
    recipient_provinsi: Optional[str]
    recipient_kota_kab: Optional[str]
    recipient_kecamatan: Optional[str]
    recipient_kelurahan: Optional[str]
    recipient_address: str
    order_details: str
    order_total: str
    seller_name: Optional[str]
    seller_phone: Optional[str]


class OrderankuItemEditForm(BaseModel):
    recipient_name: Optional[str] = None
    recipient_provinsi: Optional[str] = None
    recipient_kota_kab: Optional[str] = None
    recipient_kecamatan: Optional[str] = None
    recipient_kelurahan: Optional[str] = None
    recipient_address: Optional[str] = None
    order_details: Optional[str] = None
    order_total: Optional[str] = None
    seller_name: Optional[str] = None
    seller_phone: Optional[str] = None
    clear_paid: Optional[bool] = False
    clear_print: Optional[bool] = False


class OrderankuBatchPrint(BaseModel):
    order_ids: List[int]
