from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import func, case
from sqlalchemy.orm import Session, aliased
from pdf_module import generate_pdf
from datetime import datetime
from math import ceil

from schemas import OrderankuSeller, OrderankuSellerEditForm

from database import get_db, OrderankuItem_TM, OrderankuSeller_TR

router = APIRouter(tags=["API Orderanku"], prefix="/api_orderanku")


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
