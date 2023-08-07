import requests as r
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, Order_TM, OrderItem_TR, OrderTracking_TH, User_TM
from schemas import OrderUpdate, OrderSubmitURL, OrderUpdateDatePayload

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

@router.get('/get_designer_tasks')
def get_designer_tasks(db: Session = Depends(get_db)):
    ecom_status_order_values = [200, 400]
    res = db.query(Order_TM).filter(
        Order_TM.ecom_order_status.in_(ecom_status_order_values),
        Order_TM.design_acc_dt.is_(None),
        Order_TM.initial_input_dt.isnot(None)
    ).order_by(Order_TM.user_deadline_prd.asc()).all()
    return res

@router.get('/get_printer_tasks')
def get_printer_tasks(db: Session = Depends(get_db)):
    ecom_status_order_value = 400
    res = db.query(Order_TM).filter(
        Order_TM.ecom_order_status == ecom_status_order_value,
        Order_TM.initial_input_dt.isnot(None),
        Order_TM.design_acc_dt.isnot(None),
        Order_TM.design_sub_dt.isnot(None),
        Order_TM.print_done_dt.is_(None)
    ).order_by(Order_TM.user_deadline_prd.asc()).all()
    return res

@router.get('/get_packer_tasks')
def get_packer_tasks(db: Session = Depends(get_db)):
    ecom_status_order_value = 400
    res = db.query(Order_TM).filter(
        Order_TM.ecom_order_status == ecom_status_order_value,
        Order_TM.initial_input_dt.isnot(None),
        Order_TM.design_acc_dt.isnot(None),
        Order_TM.design_sub_dt.isnot(None),
        Order_TM.print_done_dt.isnot(None),
        Order_TM.packing_done_dt.is_(None)
    ).order_by(Order_TM.user_deadline_prd.asc()).all()
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
    
    # Query to fetch data from 'ordertracking_th' table based on the 'order_id' column
    order_tracking_query = db.query(OrderTracking_TH, User_TM.username).\
        outerjoin(User_TM, OrderTracking_TH.user_id == User_TM.id).\
        filter(OrderTracking_TH.order_id == id).\
        order_by(OrderTracking_TH.id.desc()).all()

    result = {
        'order_data': order_tm[0],
        'order_items_data': order_items,
        'order_trackings': []
    }

    # Loop through the results and create a list of dictionaries with the required data
    for tracking, username in order_tracking_query:
        result['order_trackings'].append({
            'order_tracking_id' : tracking.id,
            'order_id'          : tracking.order_id,
            'activity_date'     : tracking.activity_date,
            'activity_msg'      : tracking.activity_msg,
            'user_id'           : tracking.user_id,
            'user_name'         : username,
        })

    return result

@router.patch('/id/{id}')
def update_order(id: str, data: OrderUpdate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)

    order.initial_input_dt  = data.initial_input_dt   if data.initial_input_dt   else datetime.now()
    order.cust_phone_no     = data.cust_phone_no      if data.cust_phone_no      else order.cust_phone_no      
    order.user_deadline_prd = data.user_deadline_prd  if data.user_deadline_prd  else order.user_deadline_prd   
    order.design_sub_dt     = data.design_sub_dt      if data.design_sub_dt      else order.design_sub_dt      
    order.design_acc_dt     = data.design_acc_dt      if data.design_acc_dt      else order.design_acc_dt      
    order.google_folder_url = data.google_folder_url  if data.google_folder_url  else order.google_folder_url         
    order.google_file_url   = data.google_file_url    if data.google_file_url    else order.google_file_url    
    order.print_done_dt     = data.print_done_dt      if data.print_done_dt      else order.print_done_dt      
    order.packing_done_dt   = data.packing_done_dt    if data.packing_done_dt    else order.packing_done_dt    

    db.commit()
    db.refresh(order)

    # Format the date string as "YYYY-MM-DD"
    formatted_date_str = f"{order.user_deadline_prd[:4]}-{order.user_deadline_prd[4:6]}-{order.user_deadline_prd[6:]}"


    new_order_tracking = OrderTracking_TH(
        order_id    = order.id,
        activity_msg= f"Updated Customer Phone Number to ({order.cust_phone_no}) and Deadline Date to ({formatted_date_str})",
        user_id     = data.user_id
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}

@router.patch('/id/{id}/submit_url')
def update_order(id: str, data: OrderSubmitURL, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)

    extracted_thumb_url = extract_link_from_url(data.thumb_file_url) if data.thumb_file_url else None

    order.google_folder_url = data.folder_url         if data.folder_url         else order.google_folder_url
    order.google_file_url   = data.thumb_file_url     if data.thumb_file_url     else order.google_file_url
    order.thumb_url         = extracted_thumb_url
    order.design_sub_dt     = datetime.now()

    db.commit()
    db.refresh(order)

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id    = order.id,
        activity_msg= f"Updated Design URL to ({order.google_folder_url}) and Thumbnail URL to ({order.google_file_url})",
        user_id     = data.user_id
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}

@router.patch('/id/{id}/submit_design_acc')
def update_order_design_acc(id: str, data: OrderUpdateDatePayload, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)

    order.design_acc_dt = data.date if data.date else datetime.now()

    db.commit()
    db.refresh(order)

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id    = order.id,
        activity_msg= f"Approved Design URLs",
        user_id     = data.user_id
    )

    db.add(new_order_tracking)
    db.commit()
    return {"msg": f"Update successful"}

@router.patch('/id/{id}/submit_print_done')
def update_order_print_done(id: str, data: OrderUpdateDatePayload, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)

    order.print_done_dt = data.date if data.date else datetime.now()

    db.commit()
    db.refresh(order)

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id    = order.id,
        activity_msg= f"Printing Process Done",
        user_id     = data.user_id
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}

@router.patch('/id/{id}/submit_packing_done')
def update_order_packing_done(id: str, data: OrderUpdateDatePayload, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)

    order.packing_done_dt = data.date if data.date else datetime.now()

    db.commit()
    db.refresh(order)

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id    = order.id,
        activity_msg= f"Packing Process Done",
        user_id     = data.user_id
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}

def check_if_order_exist(id, db: Session):
    query = db.query(Order_TM).filter(Order_TM.id == id).first()

    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ID not found')

    return query
    
def extract_link_from_url(url):
    # Send a GET request to the URL and get the content
    response = r.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve content from {url}. Status code: {response.status_code}")
        return None

    # Find the substring that contains the link
    start_pattern = 'https://lh3.googleusercontent.com/drive-viewer/'
    end_pattern = '\\'
    start_index = response.text.find(start_pattern)
    end_index = response.text.find(end_pattern, start_index)

    if start_index != -1 and end_index != -1:
        extracted_link = response.text[start_index:end_index]
        return extracted_link + "=s400"
    else:
        print("Link not found in the content.")
        return None