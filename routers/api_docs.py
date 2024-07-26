from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi_jwt_auth import AuthJWT
from sqlalchemy import func, case
from sqlalchemy.orm import Session, aliased
from pdf_module import generate_pdf
from datetime import datetime

from schemas import OrderDocument

from database import (
    get_db,
    Order_TM,
    OrderItem_TR,
    OrderDocument_TM,
    OrderDocumentItem_TR,
)

router = APIRouter(tags=["API Docs"], prefix="/api_docs")


@router.post("/")
def create_order_doc(
    data: OrderDocument,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    # Authorize.jwt_required()

    # Check if order_id is valid
    # check_if_order_exist(data.order_id, db)

    new_doc = OrderDocument_TM(
        order_id=data.order_id,
        doc_type=data.doc_type,
        doc_number=data.doc_number,
        cust_name=data.customer_name,
        cust_addr_1=data.customer_addr_1,
        cust_addr_2=data.customer_addr_2,
        cust_addr_3=data.customer_addr_3,
        cust_addr_4=data.customer_addr_4,
        cust_phone=data.cust_phone,
        cust_fax=data.cust_fax,
        due_date=data.due_date,
        discount=data.discount,
        down_payment=data.down_payment,
        generated_date=datetime.now(),
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    for item in data.items:
        new_item = OrderDocumentItem_TR(
            order_doc_id=new_doc.id,
            item_name=item.item_name,
            item_price=item.item_price,
            item_qty=item.item_qty,
        )

        db.add(new_item)
    db.commit()

    # Get Invoice Data from DB
    invoice_data = get_invoice_data_by_orderdocid(new_doc.id, db)

    # Return the PDF as a streaming response
    pdf_buffer, filename = generate_pdf(invoice_data)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        # headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )


@router.patch("/id/{doc_id}")
def edit_order_doc(
    doc_id: int,
    data: OrderDocument,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    # Authorize.jwt_required()

    # Check if doc_id exists
    existing_doc = get_order_doc_by_id(doc_id, db)
    if not existing_doc:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update OrderDocument_TM fields
    existing_doc.doc_type = data.doc_type
    existing_doc.doc_number = data.doc_number
    existing_doc.cust_name = data.customer_name
    existing_doc.cust_addr_1 = data.customer_addr_1
    existing_doc.cust_addr_2 = data.customer_addr_2
    existing_doc.cust_addr_3 = data.customer_addr_3
    existing_doc.cust_addr_4 = data.customer_addr_4
    existing_doc.cust_phone = data.cust_phone
    existing_doc.cust_fax = data.cust_fax
    existing_doc.due_date = data.due_date
    existing_doc.discount = data.discount
    existing_doc.down_payment = data.down_payment

    # Update items in OrderDocumentItem_TR
    # Delete existing items
    db.query(OrderDocumentItem_TR).filter(
        OrderDocumentItem_TR.order_doc_id == doc_id
    ).delete()

    # Add new items
    for item in data.items:
        new_item = OrderDocumentItem_TR(
            order_doc_id=doc_id,
            item_name=item.item_name,
            item_price=item.item_price,
            item_qty=item.item_qty,
        )

        db.add(new_item)

    db.commit()

    # Get updated Invoice Data from DB
    updated_invoice_data = get_invoice_data_by_orderdocid(doc_id, db)

    # Return the PDF as a streaming response
    pdf_buffer, filename = generate_pdf(updated_invoice_data)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        # headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )


def get_order_doc_by_id(doc_id: int, db: Session):
    return db.query(OrderDocument_TM).filter(OrderDocument_TM.id == doc_id).first()


@router.get("/download/id/{id}")
def download_order_doc_by_id(
    id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):

    # Get Invoice Data from DB
    invoice_data = get_invoice_data_by_orderdocid(id, db)

    # Return the PDF as a streaming response
    pdf_buffer, filename = generate_pdf(invoice_data)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        # headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )


@router.get("/id/{doc_id}")
def get_document_by_id(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(OrderDocument_TM).filter(OrderDocument_TM.id == doc_id).first()

    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    items = (
        db.query(OrderDocumentItem_TR)
        .filter(OrderDocumentItem_TR.order_doc_id == doc_id)
        .all()
    )

    document_with_items = {
        "id": doc.id,
        "order_id": doc.order_id,
        "doc_number": doc.doc_number,
        "doc_type": doc.doc_type,
        "cust_name": doc.cust_name,
        "cust_addr_1": doc.cust_addr_1,
        "cust_addr_2": doc.cust_addr_2,
        "cust_addr_3": doc.cust_addr_3,
        "cust_addr_4": doc.cust_addr_4,
        "cust_phone": doc.cust_phone,
        "cust_fax": doc.cust_fax,
        "due_date": doc.due_date,
        "discount": float(doc.discount),
        "down_payment": float(doc.down_payment),
        "items": [
            {
                "id": item.id,
                "name": item.item_name,
                "price": float(item.item_price),
                "qty": item.item_qty,
            }
            for item in items
        ],
    }

    return document_with_items


@router.get("/list/latest/{n}")
def get_latest_n_docs(
    n: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    # Authorize.jwt_required()
    res = db.query(OrderDocument_TM).order_by(OrderDocument_TM.id.desc()).limit(n).all()

    return res


@router.get("/inquiry/order_id/{order_id}")
def inquiry_docs_by_order_id(
    order_id: str, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)
):
    # Authorize.jwt_required()
    check_if_order_exist(order_id, db)

    a1 = aliased(OrderDocument_TM)
    a2 = aliased(OrderDocument_TM)

    query = (
        db.query(
            func.max(case((a1.doc_type == "I", a1.id), else_=None)).label(
                "latest_invoice_id"
            ),
            func.max(case((a2.doc_type == "Q", a2.id), else_=None)).label(
                "latest_quote_id"
            ),
        )
        .filter(a1.order_id == order_id)
        .filter(a2.order_id == order_id)
    )

    latest_invoice_id, latest_quote_id = query.one()

    return {
        "order_id": order_id,
        "latest_invoice_id": latest_invoice_id,
        "latest_quote_id": latest_quote_id,
    }


def get_invoice_data_by_orderdocid(id: str, db: Session):
    query = (
        db.query(OrderDocument_TM, OrderDocumentItem_TR)
        .join(
            OrderDocumentItem_TR,
            OrderDocument_TM.id == OrderDocumentItem_TR.order_doc_id,
        )
        .filter(OrderDocument_TM.id == id)
        .all()
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OrderDocID ({id}) was not found",
        )

    doc_tm, doc_items = zip(*query)

    invoice_data = {
        "order_id": doc_tm[0].order_id,
        "doc_type": doc_tm[0].doc_type,
        "doc_number": doc_tm[0].doc_number,
        "customer_name": doc_tm[0].cust_name,
        "customer_addr_1": doc_tm[0].cust_addr_1,
        "customer_addr_2": doc_tm[0].cust_addr_2,
        "customer_addr_3": doc_tm[0].cust_addr_3,
        "customer_addr_4": doc_tm[0].cust_addr_4,
        "cust_phone": doc_tm[0].cust_phone,
        "cust_fax": doc_tm[0].cust_fax,
        "due_date": doc_tm[0].due_date,
        "items": [],
        "diskon": int(doc_tm[0].discount) if doc_tm[0].discount is not None else None,
        "down_payment": (
            int(doc_tm[0].down_payment) if doc_tm[0].down_payment is not None else None
        ),
    }

    for i in doc_items:
        invoice_data["items"].append(
            {
                "item_name": i.item_name,
                "price": int(i.item_price),
                "quantity": i.item_qty,
            }
        )

    return invoice_data


def check_if_order_exist(id, db: Session):
    query = db.query(Order_TM).filter(Order_TM.id == id).first()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"OrderID {id} not found"
        )

    return query
