from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import func, case
from sqlalchemy.orm import Session, aliased
from pdf_module import generate_pdf
from datetime import datetime
from math import ceil

from schemas import OrderDocument

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
    query = db.query(OrderankuSeller_TR).filter(OrderankuSeller_TR.is_active == 1)

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
        "per_page": per_page,
        "sellers": [
            {
                "id": result.id,
                "seller_name": result.seller_name,
                "seller_phone": result.seller_phone,
            }
            for result in results
        ],
    }
