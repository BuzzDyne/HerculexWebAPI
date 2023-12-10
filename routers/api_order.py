import random
import string
import requests as r
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_
from datetime import datetime, timedelta

from database import (
    get_db,
    Order_TM,
    OrderItem_TR,
    OrderTracking_TH,
    User_TM,
    OrderComment_TH,
    OrderBatchfile_TM,
)
from schemas import (
    OrderUpdate,
    OrderSubmitURL,
    OrderUpdateDatePayload,
    OrderInitialInputPayload,
    OrderPICUpdatePayload,
    OrderCommentCreatePayload,
    ManualOrderPayload,
    CreateBatchFilePayload,
    UserIDPayload,
    StringPayload,
)

router = APIRouter(tags=["API Order"], prefix="/api_order")


@router.post("/post_manual_order")
def post_manual_order(
    data: ManualOrderPayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    # Ensure platform_code is valid
    if data.platform_code not in {"X", "Y", "Z"}:
        raise HTTPException(
            status_code=400, detail="Invalid platform_code. Must be 'X', 'Y', or 'Z'."
        )

    # Check given user_id
    user = check_if_user_exist(data.user_id, db)

    # Create Order
    new_order = Order_TM(
        ecommerce_code=data.platform_code,
        feeding_dt=datetime.now(),
        ecom_order_status="MANUAL",
        internal_status_id="000",
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Get the id of the newly created Order
    order_id = new_order.id

    # Form ecom_order_id with the formula new_order.ecommerce_code + new_order.id (10 digits, zero pad)
    ecom_order_id = f"{new_order.ecommerce_code}{order_id:010d}"

    # Update the new_order.ecom_order_id with the new formula
    new_order.ecom_order_id = ecom_order_id
    db.commit()

    # Create OrderItem
    new_item = OrderItem_TR(
        ecom_order_id=ecom_order_id,
        product_name=data.product_name,
        quantity=data.quantity,
        product_price=data.price,
    )

    db.add(new_item)

    # Create Tracking
    new_order_tracking = OrderTracking_TH(
        order_id=order_id,
        activity_msg=f"Created manual order to system",
        user_id=data.user_id,
    )

    db.add(new_order_tracking)

    db.commit()

    return {"msg": "Manual order successfully saved!"}


@router.get("/get_all_orders")
def get_all_orders(db: Session = Depends(get_db)):
    res = (
        db.query(Order_TM, User_TM.username)
        .outerjoin(User_TM, Order_TM.pic_user_id == User_TM.id)
        .order_by(Order_TM.id.desc())
        .all()
    )
    response_data = [
        {"order": order.__dict__, "pic_username": username} for order, username in res
    ]
    return response_data


@router.get("/last_3_months")
def get_active_orders(db: Session = Depends(get_db)):
    three_months_ago = datetime.now() - timedelta(days=30)  # Assuming 30 days per month

    res = (
        db.query(Order_TM, User_TM.username)
        .outerjoin(User_TM, Order_TM.pic_user_id == User_TM.id)
        .filter(Order_TM.feeding_dt >= three_months_ago)  # Filter by date
        .order_by(Order_TM.id.desc())
        .all()
    )

    response_data = [
        {"order": order.__dict__, "pic_username": username} for order, username in res
    ]

    return response_data


@router.get("/get_orders_by_status")
def get_orders_by_status(status: str, db: Session = Depends(get_db)):
    if status == "admin":
        # If status is admin, include orders with status 000 or 200
        res = (
            db.query(Order_TM, User_TM.username)
            .outerjoin(User_TM, Order_TM.pic_user_id == User_TM.id)
            .filter(
                or_(
                    Order_TM.internal_status_id == "000",
                    Order_TM.internal_status_id == "200",
                )
            )
            .order_by(Order_TM.internal_status_id.desc(), Order_TM.id.desc())
            .all()
        )
    else:
        # For other statuses, filter by the specified status
        res = (
            db.query(Order_TM, User_TM.username)
            .outerjoin(User_TM, Order_TM.pic_user_id == User_TM.id)
            .filter(Order_TM.internal_status_id == status)
            .order_by(Order_TM.internal_status_id.desc(), Order_TM.id.desc())
            .all()
        )

    response_data = [
        {"order": order.__dict__, "pic_username": username} for order, username in res
    ]

    return response_data


@router.get("/get_all_active_orders")
def get_active_orders(db: Session = Depends(get_db)):
    ecom_status_order_values = [220, 221, 400, 450]
    res = (
        db.query(Order_TM)
        .filter(Order_TM.ecom_order_status.in_(ecom_status_order_values))
        .order_by(Order_TM.pltf_deadline_dt.asc())
        .all()
    )
    return res


@router.get("/get_batchfile_tasks")
def get_batchfile_tasks(db: Session = Depends(get_db)):
    ecom_status_order_values = [250]
    res = (
        db.query(Order_TM)
        .filter(
            Order_TM.ecom_order_status.in_(ecom_status_order_values),
            Order_TM.batch_done_dt.is_(None),
            Order_TM.design_acc_dt.isnot(None),
        )
        .order_by(Order_TM.user_deadline_prd.asc())
        .all()
    )
    return res


@router.post("/get_by_ecom_id")
def get_order_details(
    data: StringPayload, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    Authorize.jwt_required()

    # Extract payload from the request data
    payload = data.payload

    # Query the database to retrieve the first Order_TM data based on the payload
    order_tm = (
        db.query(Order_TM)
        .filter(or_(Order_TM.invoice_ref == payload, Order_TM.ecom_order_id == payload))
        .first()
    )

    # Check if the query result is empty
    if not order_tm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No matching order found"
        )

    # Convert the result to a dictionary for JSON output
    order_data = order_tm.__dict__

    return order_tm


@router.get("/id/{id}")
def get_order_details(
    id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    Authorize.jwt_required()
    query = (
        db.query(Order_TM, OrderItem_TR)
        .join(OrderItem_TR, Order_TM.ecom_order_id == OrderItem_TR.ecom_order_id)
        .filter(Order_TM.id == id)
        .all()
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ID not found"
        )

    order_tm, order_items = zip(*query)

    # Check pic_user_id against User_TM directly
    pic_user_query = (
        db.query(User_TM.username).filter(User_TM.id == order_tm[0].pic_user_id).first()
    )

    # Check batchfile_id against OrderBatchfile_TM
    batch = (
        db.query(OrderBatchfile_TM.batch_name)
        .filter(OrderBatchfile_TM.id == order_tm[0].batchfile_id)
        .first()
    )

    result = {
        "order_data": order_tm[0],
        "order_items_data": order_items,
        "order_trackings": [],
        "pic_username": pic_user_query.username if pic_user_query else None,
        "batch_name": batch.batch_name if batch else None,
    }

    # Fetch order tracking data and associated username
    order_tracking_query = (
        db.query(OrderTracking_TH, User_TM.username)
        .outerjoin(User_TM, OrderTracking_TH.user_id == User_TM.id)
        .filter(OrderTracking_TH.order_id == id)
        .order_by(OrderTracking_TH.id.desc())
        .all()
    )

    # Loop through the results and create a list of dictionaries with the required data
    for tracking, username in order_tracking_query:
        result["order_trackings"].append(
            {
                "order_tracking_id": tracking.id,
                "order_id": tracking.order_id,
                "activity_date": tracking.activity_date,
                "activity_msg": tracking.activity_msg,
                "user_id": tracking.user_id,
                "user_name": username,
            }
        )

    return result


@router.get("/id/{id}/get_comments")
def get_comments(
    id: str,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    order = check_if_order_exist(id, db)

    result = (
        db.query(OrderComment_TH, User_TM.username.label("creator_username"))
        .filter(OrderComment_TH.creator_id == User_TM.id)
        .filter(OrderComment_TH.order_id == id)
        .order_by(OrderComment_TH.id.desc())
        .all()
    )

    # Convert the result to a list of dictionaries
    comments = [
        {
            "id": comment[0].id,
            "creator_id": comment[0].creator_id,
            "order_id": comment[0].order_id,
            "comment_text": comment[0].comment_text,
            "comment_date": comment[0].comment_date,
            "creator_username": comment.creator_username,
        }
        for comment in result
    ]

    return comments


@router.post("/id/{id}/post_comment")
def post_comment(
    id: str,
    data: OrderCommentCreatePayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)
    user = check_if_user_exist(data.user_id, db)

    new_comment = OrderComment_TH(
        creator_id=data.user_id, order_id=id, comment_text=data.comment
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"msg": f"Comment successfully saved!"}


@router.patch("/id/{id}")
def update_order(
    id: str,
    data: OrderUpdate,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    order = check_if_order_exist(id, db)

    order.initial_input_dt = (
        data.initial_input_dt if data.initial_input_dt else datetime.now()
    )
    order.cust_phone_no = (
        data.cust_phone_no if data.cust_phone_no else order.cust_phone_no
    )
    order.user_deadline_prd = (
        data.user_deadline_prd if data.user_deadline_prd else order.user_deadline_prd
    )
    order.design_sub_dt = (
        data.design_sub_dt if data.design_sub_dt else order.design_sub_dt
    )
    order.design_acc_dt = (
        data.design_acc_dt if data.design_acc_dt else order.design_acc_dt
    )
    order.google_folder_url = (
        data.google_folder_url if data.google_folder_url else order.google_folder_url
    )
    order.google_file_url = (
        data.google_file_url if data.google_file_url else order.google_file_url
    )
    order.print_done_dt = (
        data.print_done_dt if data.print_done_dt else order.print_done_dt
    )
    order.packing_done_dt = (
        data.packing_done_dt if data.packing_done_dt else order.packing_done_dt
    )

    db.commit()
    db.refresh(order)

    # Format the date string as "YYYY-MM-DD"
    formatted_date_str = f"{order.user_deadline_prd[:4]}-{order.user_deadline_prd[4:6]}-{order.user_deadline_prd[6:]}"

    new_order_tracking = OrderTracking_TH(
        order_id=order.id,
        activity_msg=f"Updated Customer Phone Number to ({order.cust_phone_no}) and Deadline Date to ({formatted_date_str})",
        user_id=data.user_id,
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}


@router.patch("/id/{id}/submit_url")
def update_order(
    id: str,
    data: OrderSubmitURL,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    order = check_if_order_exist(id, db)

    before_internal_status_id = order.internal_status_id

    extracted_thumb_url = (
        extract_link_from_url(data.thumb_file_url) if data.thumb_file_url else None
    )

    order.google_folder_url = (
        data.folder_url if data.folder_url else order.google_folder_url
    )
    order.google_file_url = (
        data.thumb_file_url if data.thumb_file_url else order.google_file_url
    )
    order.thumb_url = extracted_thumb_url
    order.last_updated_ts = datetime.now()
    order.design_sub_dt = datetime.now()
    if before_internal_status_id == "100":
        order.pic_user_id = None
        order.internal_status_id = "200"

    db.commit()
    db.refresh(order)

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id=order.id,
        activity_msg=f"Updated Design URL to ({order.google_folder_url}) and Thumbnail URL to ({order.google_file_url})",
        user_id=data.user_id,
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}


@router.patch("/id/{order_id}/update_pic")
def update_order_pic(
    order_id: str,
    data: OrderPICUpdatePayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    # Authorize the request with JWT
    Authorize.jwt_required()

    # Check if the order exists
    order = db.query(Order_TM).filter(Order_TM.id == order_id).first()
    if not order:
        return {"error": "Order not found"}

    before_pic_name = get_user_name(db, order.pic_user_id)
    after_pic_name = get_user_name(db, data.pic_id)

    # Update the pic_user_id
    order.pic_user_id = data.pic_id
    order.last_updated_ts = datetime.now()

    # Create the message
    message = f"PIC was updated from ({before_pic_name}) to ({after_pic_name})"

    # Create an order tracking entry for the message
    new_order_tracking = OrderTracking_TH(
        order_id=order.id,
        activity_msg=message,
        user_id=data.user_id,
    )
    db.add(new_order_tracking)
    db.commit()

    return {"msg": "Update successful"}


@router.patch("/id/{id}/submit_initial_data")
def update_order_initial_data(
    id: str,
    data: OrderInitialInputPayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    order = check_if_order_exist(id, db)

    before_phone_no = order.cust_phone_no
    before_user_deadline_prd = order.user_deadline_prd
    before_internal_status_id = order.internal_status_id

    # Check if the values have changed
    phone_no_changed = before_phone_no != data.cust_phone_no
    deadline_changed = before_user_deadline_prd != data.user_deadline_prd

    order.cust_phone_no = data.cust_phone_no
    order.user_deadline_prd = data.user_deadline_prd
    order.initial_input_dt = datetime.now()
    order.last_updated_ts = datetime.now()
    if before_internal_status_id == "000":
        order.pic_user_id = None
        order.internal_status_id = "100"

    # Create update messages only if values change
    update_messages = []
    if phone_no_changed:
        if before_phone_no:
            update_messages.append(
                f"Updated phone number from '{before_phone_no}' to '{data.cust_phone_no}'"
            )
        else:
            update_messages.append(f"Set phone number to '{data.cust_phone_no}'")

    if deadline_changed:
        if before_user_deadline_prd:
            update_messages.append(
                f"Updated deadline from '{before_user_deadline_prd}' to '{data.user_deadline_prd}'"
            )
        else:
            update_messages.append(f"Set deadline to '{data.user_deadline_prd}'")

    if data.pic_user_id:
        order.pic_user_id = data.pic_user_id
        after_pic_name = get_user_name(db, data.pic_user_id)
        update_messages.append(f"PIC set to {after_pic_name}")

    msg = " and ".join(update_messages)

    if msg:
        new_order_tracking = OrderTracking_TH(
            order_id=order.id, activity_msg=msg, user_id=data.user_id
        )

        db.add(new_order_tracking)

    db.commit()
    return {"msg": "Update successful"}


@router.patch("/id/{id}/submit_design_acc")
def update_order_design_acc(
    id: str,
    data: OrderUpdateDatePayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    order = check_if_order_exist(id, db)

    before_internal_status_id = order.internal_status_id

    order.design_acc_dt = data.date if data.date else datetime.now()
    order.last_updated_ts = datetime.now()
    if before_internal_status_id == "200":
        order.pic_user_id = None
        order.internal_status_id = "250"

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id=order.id, activity_msg=f"Approved Design", user_id=data.user_id
    )

    db.add(new_order_tracking)
    db.commit()
    return {"msg": f"Update successful"}


@router.patch("/id/{id}/submit_design_rej")
def update_order_design_rej(
    id: str,
    data: OrderUpdateDatePayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    order = check_if_order_exist(id, db)

    before_internal_status_id = order.internal_status_id

    order.last_updated_ts = datetime.now()
    if before_internal_status_id == "200":
        order.design_sub_dt = None
        order.pic_user_id = None
        order.internal_status_id = "100"

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id=order.id, activity_msg=f"Rejected Design", user_id=data.user_id
    )

    db.add(new_order_tracking)
    db.commit()
    return {"msg": f"Update successful"}


@router.patch("/id/{id}/submit_print_done")
def update_order_print_done(
    id: str,
    data: OrderUpdateDatePayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    order = check_if_order_exist(id, db)

    before_internal_status_id = order.internal_status_id

    order.print_done_dt = data.date if data.date else datetime.now()
    order.last_updated_ts = datetime.now()
    if before_internal_status_id == "300":
        order.pic_user_id = None
        order.internal_status_id = "400"

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id=order.id, activity_msg=f"Printing Process Done", user_id=data.user_id
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}


@router.patch("/id/{id}/submit_packing_done")
def update_order_packing_done(
    id: str,
    data: OrderUpdateDatePayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    order = check_if_order_exist(id, db)

    before_internal_status_id = order.internal_status_id

    order.packing_done_dt = data.date if data.date else datetime.now()
    order.last_updated_ts = datetime.now()
    if before_internal_status_id == "400":
        order.pic_user_id = None
        order.internal_status_id = "999"

    # Insert a new row in ordertracking_th
    new_order_tracking = OrderTracking_TH(
        order_id=order.id, activity_msg=f"Packing Process Done", user_id=data.user_id
    )

    db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}


@router.get("/batchfile/last_3_month")
def get_batchfile_last3month(db: Session = Depends(get_db)):
    three_months_ago = datetime.now() - timedelta(days=30)
    designer_user = aliased(User_TM)
    printer_user = aliased(User_TM)

    res = (
        db.query(
            OrderBatchfile_TM,
            designer_user.username.label("designer_username"),
            printer_user.username.label("printer_username"),
        )
        .outerjoin(
            designer_user, OrderBatchfile_TM.designer_user_id == designer_user.id
        )
        .outerjoin(printer_user, OrderBatchfile_TM.printer_user_id == printer_user.id)
        .filter(OrderBatchfile_TM.create_dt >= three_months_ago)
        .order_by(OrderBatchfile_TM.id.desc())
        .all()
    )

    result_list = []
    for order_batchfile, designer_username, printer_username in res:
        order_dict = order_batchfile.__dict__
        order_dict["designer_username"] = designer_username
        order_dict["printer_username"] = printer_username

        # Get Order_TM data for the current batch
        order_list = (
            db.query(Order_TM).filter(Order_TM.batchfile_id == order_batchfile.id).all()
        )

        order_dict["batch_order_list"] = [order.__dict__ for order in order_list]

        result_list.append(order_dict)

    return result_list


@router.get("/batchfile/active")
def get_batchfile_last3month(db: Session = Depends(get_db)):
    designer_user = aliased(User_TM)
    printer_user = aliased(User_TM)

    res = (
        db.query(
            OrderBatchfile_TM,
            designer_user.username.label("designer_username"),
            printer_user.username.label("printer_username"),
        )
        .outerjoin(
            designer_user, OrderBatchfile_TM.designer_user_id == designer_user.id
        )
        .outerjoin(printer_user, OrderBatchfile_TM.printer_user_id == printer_user.id)
        .filter(OrderBatchfile_TM.printed_dt.is_(None))
        .order_by(OrderBatchfile_TM.id.desc())
        .all()
    )

    result_list = []
    for order_batchfile, designer_username, printer_username in res:
        order_dict = order_batchfile.__dict__
        order_dict["designer_username"] = designer_username
        order_dict["printer_username"] = printer_username

        # Get Order_TM data for the current batch
        order_list = (
            db.query(Order_TM).filter(Order_TM.batchfile_id == order_batchfile.id).all()
        )

        order_dict["batch_order_list"] = [order.__dict__ for order in order_list]

        result_list.append(order_dict)

    return result_list


@router.patch("/batchfile/id/{id}/submit_print_done")
def submit_batchfile_print_done(
    id: str,
    data: UserIDPayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    # Check if printerID exists
    printer = check_if_user_exist(data.user_id, db)

    # Check if batchfileID exists
    batchfile = check_if_batchfile_exist(id, db)

    # Update batchFile
    batchfile.printer_user_id = printer.id
    batchfile.printed_dt = datetime.now()

    # Update orders
    related_orders = (
        db.query(Order_TM).filter(Order_TM.batchfile_id == batchfile.id).all()
    )
    for o in related_orders:
        o.print_done_dt = datetime.now()
        o.last_updated_ts = datetime.now()
        o.internal_status_id = "400"

        # Insert a new row in ordertracking_th
        new_order_tracking = OrderTracking_TH(
            order_id=o.id,
            activity_msg=f"Printing Process Done (BatchFile {batchfile.batch_name})",
            user_id=printer.id,
        )

        db.add(new_order_tracking)
    db.commit()

    return {"msg": f"Update successful"}


@router.post("/batchfile/new")
def create_batchfile(
    data: CreateBatchFilePayload,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    validated_orders = []

    # Check if all Order is valid
    for order_id in data.order_ids:
        order = check_if_order_exist(order_id, db)
        validated_orders.append(order)

    # Check if designer_id is valid
    designer = check_if_user_exist(data.designer_id, db)

    # Create BatchFile
    new_batch = OrderBatchfile_TM(
        batch_name=generate_readable_id(),
        remarks=data.remarks,
        create_dt=datetime.now(),
        designer_user_id=designer.id,
    )

    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)

    # Update Each Order
    for order in validated_orders:
        order.last_updated_ts = datetime.now()
        order.batch_done_dt = datetime.now()
        order.batchfile_id = new_batch.id
        order.internal_status_id = "300"

        new_order_tracking = OrderTracking_TH(
            order_id=order.id,
            activity_msg=f"Assigned to BatchFile ({new_batch.batch_name})",
            user_id=designer.id,
        )

        db.add(new_order_tracking)
    db.commit()
    return {"msg": f"Create BatchFile ({new_batch.batch_name}) successful"}


def check_if_order_exist(id, db: Session):
    query = db.query(Order_TM).filter(Order_TM.id == id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"OrderID {id} not found"
        )

    return query


def check_if_batchfile_exist(id, db: Session):
    query = db.query(OrderBatchfile_TM).filter(OrderBatchfile_TM.id == id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"BatchFileID {id} not found"
        )

    return query


def check_if_user_exist(id, db: Session):
    query = db.query(User_TM).filter(User_TM.id == id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"UserID {id} not found"
        )

    return query


def extract_link_from_url(url):
    # Send a GET request to the URL and get the content
    response = r.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        print(
            f"Failed to retrieve content from {url}. Status code: {response.status_code}"
        )
        return None

    # Find the substring that contains the link
    start_pattern = "https://lh3.googleusercontent.com/drive-viewer/"
    end_pattern = "\\"
    start_index = response.text.find(start_pattern)
    end_index = response.text.find(end_pattern, start_index)

    if start_index != -1 and end_index != -1:
        extracted_link = response.text[start_index:end_index]
        return extracted_link + "=s400"
    else:
        print("Link not found in the content.")
        return None


def get_user_name(db, user_id):
    user_name = "-"
    if user_id is not None:
        user = db.query(User_TM).filter(User_TM.id == user_id).first()
        if user:
            user_name = user.username
    return user_name


def generate_readable_id():
    characters = "".join(
        [ch for ch in string.ascii_uppercase + string.digits if ch not in "OIL01"]
    )
    return "".join(random.choices(characters, k=4))
