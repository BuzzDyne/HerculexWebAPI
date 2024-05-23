from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, aliased
from pdf_module import generate_pdf
from datetime import datetime
from math import ceil

from schemas import OrderankuSeller, OrderankuSellerEditForm

from database import get_db, OrderankuItem_TM, OrderankuSeller_TR

router = APIRouter(tags=["API Orderanku"], prefix="/api_orderanku")


@router.get("/order")
def get_orders(
    sort_field: str = "id",
    sort_order: str = "desc",
    page: int = 1,  # Default page number is 1
    per_page: int = 5,  # Default number of results per page is 10
    created_date_from: str = None,
    created_date_to: str = None,
    recipient_name: str = None,
    recipient_addr: str = None,
    total_from: float = None,
    total_to: float = None,
    flag_printed: int = 2,  # 0 Not yet, 1 Have, 2 All
    flag_paid: int = 2,  # 0 Not yet, 1 Have, 2 All
    flag_active: int = 1,  # 0 Not Active, 1 Active, 2 All
    seller_name: str = None,
    seller_phone: str = None,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    query = db.query(OrderankuItem_TM)

    # region Filter Logic
    if created_date_from:
        created_date_from_dt = datetime.strptime(created_date_from, "%Y-%m-%d")
        query = query.filter(OrderankuItem_TM.created_date >= created_date_from_dt)

    if created_date_to:
        created_date_to_dt = datetime.strptime(created_date_to, "%Y-%m-%d")
        query = query.filter(OrderankuItem_TM.created_date <= created_date_to_dt)

    if recipient_name:
        query = query.filter(
            OrderankuItem_TM.recipient_name.ilike(f"%{recipient_name}%")
        )

    if recipient_addr:
        query = query.filter(
            or_(
                OrderankuItem_TM.recipient_provinsi.ilike(f"%{recipient_addr}%"),
                OrderankuItem_TM.recipient_kota_kab.ilike(f"%{recipient_addr}%"),
                OrderankuItem_TM.recipient_kecamatan.ilike(f"%{recipient_addr}%"),
                OrderankuItem_TM.recipient_kelurahan.ilike(f"%{recipient_addr}%"),
                OrderankuItem_TM.recipient_address.ilike(f"%{recipient_addr}%"),
            )
        )

    if total_from:
        query = query.filter(OrderankuItem_TM.order_total >= total_from)

    if total_to:
        query = query.filter(OrderankuItem_TM.order_total <= total_to)

    if flag_printed == 1:
        query = query.filter(OrderankuItem_TM.print_date.isnot(None))

    if flag_printed == 0:
        query = query.filter(OrderankuItem_TM.print_date.is_(None))

    if flag_paid == 1:
        query = query.filter(OrderankuItem_TM.paid_date.isnot(None))

    if flag_paid == 0:
        query = query.filter(OrderankuItem_TM.paid_date.is_(None))

    if flag_active == 1:
        query = query.filter(OrderankuItem_TM.is_active == 1)

    if flag_active == 0:
        query = query.filter(OrderankuItem_TM.is_active == 0)

    if seller_name:
        query = query.filter(OrderankuItem_TM.seller_name.ilike(f"%{seller_name}%"))

    if seller_phone:
        query = query.filter(OrderankuItem_TM.seller_phone.ilike(f"%{seller_phone}%"))
    # endregion

    # region Sorting Logic
    sort_mapping = {
        "id": OrderankuItem_TM.id,
        "created_date": OrderankuItem_TM.created_date,
        "recipient_name": OrderankuItem_TM.recipient_name,
        "order_total": OrderankuItem_TM.order_total,
        "print_date": OrderankuItem_TM.print_date,
        "paid_date": OrderankuItem_TM.paid_date,
        "seller_name": OrderankuItem_TM.seller_name,
    }

    sort_field_mapped = sort_mapping.get(sort_field.lower(), OrderankuItem_TM.id)

    if sort_order.lower() == "desc":
        query = query.order_by(sort_field_mapped.desc())
    else:
        query = query.order_by(sort_field_mapped.asc())
    # endregion

    total_results = query.count()

    max_page = max(1, ceil(total_results / per_page)) if total_results > 0 else 1
    page = min(max_page, max(1, page))

    results = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total_results": total_results,
        "page": page,
        "max_page": max_page,
        "sellers": [
            {
                "id": result.id,
                "recipient_name": result.recipient_name,
                "recipient_address": ", ".join(
                    [
                        value
                        for value in [
                            result.recipient_address,
                            result.recipient_kelurahan,
                            result.recipient_kecamatan,
                            result.recipient_kota_kab,
                            result.recipient_provinsi,
                        ]
                        if value
                    ]
                ),
                "order_details": result.order_details,
                "order_total": result.order_total,
                "created_date": result.created_date,
                "print_date": result.print_date,
                "paid_date": result.paid_date,
                "seller_name": result.seller_name,
                "seller_phone": result.seller_phone,
            }
            for result in results
        ],
    }


@router.delete("/order/id/{id}")
def delete_order(
    id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    Authorize.jwt_required()

    order_query = (
        db.query(OrderankuItem_TM)
        .filter(OrderankuItem_TM.id == id)
        .filter(OrderankuItem_TM.is_active == 1)
    )

    # Validation
    if not order_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orderanku ID ({id}) not found / inactive",
        )

    order = order_query.first()

    # Update to inactive

    order_query.update({"is_active": 0})
    db.commit()
    db.refresh(order)

    return {"msg": f"Update OrderanID ({id}) successful", "data": order}


@router.patch("/order/id/{id}/has_paid")
def make_order_paid(
    id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    Authorize.jwt_required()

    order_query = (
        db.query(OrderankuItem_TM)
        .filter(OrderankuItem_TM.id == id)
        .filter(OrderankuItem_TM.is_active == 1)
    )

    # Validation
    if not order_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orderanku ID ({id}) not found / inactive",
        )

    order = order_query.first()

    order_query.update({"paid_date": datetime.now()})
    db.commit()
    db.refresh(order)

    return {"msg": f"Update paidDate of OrderanID ({id}) successful", "data": order}


@router.patch("/order/id/{id}/print_resi")
def order_print(id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()

    order_query = (
        db.query(OrderankuItem_TM)
        .filter(OrderankuItem_TM.id == id)
        .filter(OrderankuItem_TM.is_active == 1)
    )

    # Validation
    if not order_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orderanku ID ({id}) not found / inactive",
        )

    order = order_query.first()

    # TODO Logic PDF Generation

    # Update to print_date

    order_query.update({"print_date": datetime.now()})
    db.commit()
    db.refresh(order)

    return {"msg": f"Update paidDate of OrderanID ({id}) successful", "data": order}


@router.get("/seller")
def get_sellers(
    name: str = None,
    phone: str = None,
    sort_field: str = "id",
    sort_order: str = "asc",
    page: int = 1,  # Default page number is 1
    per_page: int = 5,  # Default number of results per page is 10
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()
    query = db.query(OrderankuSeller_TR)

    if name:
        query = query.filter(OrderankuSeller_TR.seller_name.ilike(f"%{name}%"))

    if phone:
        query = query.filter(OrderankuSeller_TR.seller_phone.ilike(f"%{phone}%"))

    # Map sort_field to the appropriate field in the query
    sort_mapping = {
        "id": OrderankuSeller_TR.id,
        "name": OrderankuSeller_TR.seller_name,
    }

    sort_field_mapped = sort_mapping.get(sort_field.lower(), OrderankuSeller_TR.id)

    # Implement the sorting logic
    if sort_order.lower() == "desc":
        query = query.order_by(sort_field_mapped.desc())
    else:
        query = query.order_by(sort_field_mapped.asc())

    total_results = query.count()

    max_page = max(1, ceil(total_results / per_page)) if total_results > 0 else 1
    page = min(max_page, max(1, page))

    results = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total_results": total_results,
        "page": page,
        "max_page": max_page,
        "sellers": [
            {
                "id": result.id,
                "seller_name": result.seller_name,
                "seller_phone": result.seller_phone,
            }
            for result in results
        ],
    }


@router.post("/seller")
def create_seller(
    payload: OrderankuSeller,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    seller = (
        db.query(OrderankuSeller_TR)
        .filter(OrderankuSeller_TR.seller_name == payload.seller_name)
        .filter(OrderankuSeller_TR.seller_phone == payload.seller_phone)
        .all()
    )

    if seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seller with name '{payload.seller_name}' and phone '{payload.seller_phone}' already exist!",
        )

    new_seller = OrderankuSeller_TR(
        seller_name=payload.seller_name, seller_phone=payload.seller_phone
    )

    db.add(new_seller)
    db.commit()
    db.refresh(new_seller)

    return {"msg": "Success create Seller", "data": new_seller}


@router.delete("/seller/id/{id}")
def delete_seller(
    id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    Authorize.jwt_required()

    seller_query = db.query(OrderankuSeller_TR).filter(OrderankuSeller_TR.id == id)

    if not seller_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seller ID ({id}) not found",
        )

    seller_query.delete()
    db.commit()

    return {"msg": f"Deleted Seller of ID ({id})"}


@router.patch("/seller/id/{id}")
def edit_seller(
    id: str,
    payload: OrderankuSellerEditForm,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    Authorize.jwt_required()

    seller_query = db.query(OrderankuSeller_TR).filter(OrderankuSeller_TR.id == id)
    seller = seller_query.first()

    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seller ID ({id}) not found",
        )

    # Validation
    if not payload.seller_name and not payload.seller_phone:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Either one of Name or Phone must be given",
        )

    update_data = {}
    if payload.seller_name:
        update_data["seller_name"] = payload.seller_name

    if payload.seller_phone:
        update_data["seller_phone"] = payload.seller_phone

    if update_data:
        seller_query.update(update_data)
        db.commit()
        db.refresh(seller)

    return {"msg": f"Update SellerID ({id}) successful", "data": seller}