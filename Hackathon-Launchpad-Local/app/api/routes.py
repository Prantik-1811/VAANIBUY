import json
import sqlite3
import uuid
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, StrictBool
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sarvamai import SarvamAI

from app.services.catalog import PRODUCTS
from app.services.store import connect
from config import settings

router = APIRouter(prefix="/api")


class ProposalItem(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=20)


class ProposalRequest(BaseModel):
    items: list[ProposalItem] = Field(min_length=1, max_length=20)
    budget: int | None = Field(default=None, ge=1)
    address: str = Field(min_length=5, max_length=300)


class ApprovalRequest(BaseModel):
    approved: StrictBool
    idempotency_key: str = Field(min_length=8, max_length=100)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


def _order_result(db, order_id):
    row = db.execute(
        """
        SELECT o.id, o.status, o.created_at, p.total, p.items_json,
               pay.status AS payment_status
        FROM orders o
        JOIN proposals p ON p.id = o.proposal_id
        JOIN payments pay ON pay.order_id = o.id
        WHERE o.id = ?
        """,
        (order_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": row["id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "total": row["total"],
        "items": json.loads(row["items_json"]),
        "payment_status": row["payment_status"],
        "demo": True,
    }


@router.get("/products")
def search_products(q: str = Query(default="", max_length=100)):
    query = q.strip().casefold()
    products = [
        item
        for item in PRODUCTS
        if not query or query in f"{item['name']} {item['category']}".casefold()
    ]
    return {"demo": True, "products": products}


@router.get("/voice/status")
def voice_status():
    return {
        "agent_id_configured": bool(settings.SARVAM_AGENT_ID),
        "api_key_configured": bool(settings.SAMVAAD_API_KEY),
        "organization_configured": bool(settings.SAMVAAD_ORG_ID),
        "workspace_configured": bool(settings.SAMVAAD_WORKSPACE_ID),
        "ready": all(
            (
                settings.SARVAM_AGENT_ID,
                settings.SAMVAAD_API_KEY,
                settings.SAMVAAD_ORG_ID,
                settings.SAMVAAD_WORKSPACE_ID,
            )
        ),
    }


@router.post("/chat")
def chat(request: ChatRequest):
    if not settings.SARVAM_API_KEY:
        raise HTTPException(status_code=503, detail="SARVAM_API_KEY is not configured")
    client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are VaaniBuy, a friendly shopping assistant for India. "
                    "Ask concise questions to understand items, quantity, budget, "
                    "brand preferences, substitutions, delivery timing, and address. "
                    "Ask only for details still missing. Never claim product stock, "
                    "prices, delivery dates, or orders are real; the catalog is demo "
                    "data. Never authorize a purchase. The user must approve the "
                    "itemized proposal in the app before a simulated order is created."
                ),
            },
            *[message.model_dump() for message in request.messages],
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="Sarvam returned an empty reply")
    return {"reply": content}


@router.post("/proposals", status_code=201)
def create_proposal(request: ProposalRequest):
    catalog = {item["id"]: item for item in PRODUCTS}
    quantities = {}
    for item in request.items:
        if item.product_id not in catalog:
            raise HTTPException(
                status_code=404, detail=f"Unknown product: {item.product_id}"
            )
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
        if quantities[item.product_id] > 20:
            raise HTTPException(
                status_code=422, detail="Maximum quantity per item is 20"
            )

    items = [
        {**catalog[product_id], "quantity": quantity}
        for product_id, quantity in quantities.items()
    ]
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    if request.budget is not None and subtotal > request.budget:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Subtotal ₹{subtotal} is over the stated budget "
                f"of ₹{request.budget}"
            ),
        )
    delivery_fee = 0 if subtotal >= 500 else 40
    proposal_id = str(uuid.uuid4())
    with connect() as db:
        db.execute(
            """
            INSERT INTO proposals
                (id, status, items_json, budget, address, subtotal, delivery_fee, total)
            VALUES (?, 'pending_approval', ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                json.dumps(items),
                request.budget,
                request.address.strip(),
                subtotal,
                delivery_fee,
                subtotal + delivery_fee,
            ),
        )
    return {
        "id": proposal_id,
        "status": "pending_approval",
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": subtotal + delivery_fee,
        "budget": request.budget,
        "address": request.address.strip(),
        "demo": True,
    }


@router.post("/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str, request: ApprovalRequest):
    if not request.approved:
        raise HTTPException(
            status_code=422, detail="Explicit customer approval is required"
        )
    order_id = str(uuid.uuid4())
    payment_id = str(uuid.uuid4())
    try:
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            proposal = db.execute(
                "SELECT total FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if proposal is None:
                raise HTTPException(status_code=404, detail="Proposal not found")
            existing = db.execute(
                "SELECT id FROM orders WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if existing:
                return _order_result(db, existing["id"])
            db.execute(
                "INSERT INTO approvals (id, proposal_id, idempotency_key, approved) "
                "VALUES (?, ?, ?, 1)",
                (str(uuid.uuid4()), proposal_id, request.idempotency_key),
            )
            db.execute(
                "INSERT INTO orders (id, proposal_id, status) "
                "VALUES (?, ?, 'demo_placed')",
                (order_id, proposal_id),
            )
            db.execute(
                "UPDATE proposals SET status = 'approved' WHERE id = ?", (proposal_id,)
            )
            db.execute(
                "INSERT INTO payments (id, order_id, amount, status) "
                "VALUES (?, ?, ?, 'simulated_not_charged')",
                (payment_id, order_id, proposal["total"]),
            )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Approval already recorded"
        ) from exc
    with connect() as db:
        return _order_result(db, order_id)


@router.get("/orders")
def list_orders():
    with connect() as db:
        rows = db.execute("SELECT id FROM orders ORDER BY created_at DESC").fetchall()
        return {"demo": True, "orders": [_order_result(db, row["id"]) for row in rows]}


@router.get("/orders/{order_id}")
def get_order(order_id: str):
    with connect() as db:
        return _order_result(db, order_id)


@router.get("/orders/{order_id}/receipt")
def receipt(order_id: str):
    with connect() as db:
        order = _order_result(db, order_id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"VaaniBuy demo receipt {order_id}")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(48, 790, "VaaniBuy - Demo Receipt")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(48, 766, f"Order: {order['id']}")
    pdf.drawString(48, 750, f"Status: {order['status']} (simulated; no payment taken)")
    y = 710
    for item in order["items"]:
        pdf.drawString(48, y, f"{item['name']} x {item['quantity']}")
        pdf.drawRightString(540, y, f"INR {item['price'] * item['quantity']}")
        y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(540, y - 10, f"Total: INR {order['total']}")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(48, 48, "Demo only. This is not a tax invoice or proof of purchase.")
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="vaanibuy-{order_id}.pdf"'
        },
    )
