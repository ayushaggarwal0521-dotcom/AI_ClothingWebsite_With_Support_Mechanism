"""Storefront API: catalogue for the UI + cart checkout / Buy Now (writes to PostgreSQL)."""
import json, random
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_connection

router = APIRouter(prefix="/api")
_DATA = json.loads((Path(__file__).resolve().parent.parent / "data" / "products.json").read_text(encoding="utf-8"))
META = {p["product_id"]: p for p in _DATA}  # description + images live in the JSON


class Item(BaseModel):
    product_id: str
    quantity: int = 1
    size: str | None = None

class Checkout(BaseModel):
    name: str
    email: str
    phone: str
    items: list[Item]
    payment_method: str = "COD"  # no gateway yet


@router.get("/products")
def products():
    con = get_connection(); cur = con.cursor()
    cur.execute("""SELECT p.product_id,p.name,p.category,p.price,p.color,p.gender,p.material,p.fit,
                   COALESCE(i.stock_quantity,0) FROM products p
                   LEFT JOIN inventory i ON i.product_id=p.product_id ORDER BY p.product_id""")
    rows = cur.fetchall()
    cur.execute("SELECT product_id,size FROM product_sizes ORDER BY product_id,size")
    sizes = {}
    for pid, sz in cur.fetchall():
        sizes.setdefault(pid, []).append(sz)
    cur.close(); con.close()
    out = []
    for r in rows:
        m = META.get(r[0], {})
        out.append(dict(product_id=r[0], name=r[1], category=r[2], price=float(r[3]), color=r[4], gender=r[5],
                        material=r[6], fit=r[7], stock=r[8], sizes=sizes.get(r[0], m.get("sizes", [])),
                        images=m.get("images", []), description=m.get("description", "")))
    return out


def _next(cur, table, col, prefix, width=3):
    cur.execute(f"SELECT COALESCE(MAX(CAST(SUBSTRING({col} FROM '[0-9]+$') AS INT)),0) FROM {table}")
    return cur.fetchone()[0] + 1


@router.post("/orders")
def place_order(req: Checkout):
    """Used by both 'Place order' (cart) and 'Buy now' (single item)."""
    if not req.items:
        raise HTTPException(400, "Cart is empty.")
    con = get_connection(); cur = con.cursor()
    try:
        # guest customer: reuse by email
        cur.execute("SELECT customer_id FROM customers WHERE LOWER(email)=LOWER(%s)", (req.email,))
        row = cur.fetchone()
        if row:
            cid = row[0]
        else:
            cid = f"CUST-{_next(cur, 'customers', 'customer_id', 'CUST'):03d}"
            cur.execute("INSERT INTO customers (customer_id,name,email,phone,created_at) VALUES (%s,%s,%s,%s,NOW())",
                        (cid, req.name, req.email, req.phone))
        lines, total = [], 0.0
        for it in req.items:
            if it.quantity < 1:
                raise HTTPException(400, "Invalid quantity.")
            cur.execute("""SELECT p.name,p.price,COALESCE(i.stock_quantity,0) FROM products p
                           LEFT JOIN inventory i ON i.product_id=p.product_id
                           WHERE p.product_id=%s FOR UPDATE OF p""", (it.product_id,))
            p = cur.fetchone()
            if not p:
                raise HTTPException(404, f"Product {it.product_id} not found.")
            if p[2] < it.quantity:
                raise HTTPException(409, f"Only {p[2]} left of {p[0]}.")
            lines.append((it, float(p[1]))); total += float(p[1]) * it.quantity
        oid = f"ORD-{_next(cur, 'orders', 'order_id', 'ORD'):03d}"
        cur.execute("INSERT INTO orders (order_id,customer_id,order_date,status,total_amount) VALUES (%s,%s,NOW(),'PLACED',%s)",
                    (oid, cid, total))
        cur.execute("""SELECT 1 FROM information_schema.columns WHERE table_name='order_items' AND column_name='size'""")
        has_size = cur.fetchone() is not None  # optional: see add_size_column.sql
        n = _next(cur, "order_items", "order_item_id", "ITEM")
        for it, price in lines:
            if has_size:
                cur.execute("INSERT INTO order_items (order_item_id,order_id,product_id,quantity,unit_price,size) VALUES (%s,%s,%s,%s,%s,%s)",
                            (f"ITEM-{n:03d}", oid, it.product_id, it.quantity, price, it.size))
            else:
                cur.execute("INSERT INTO order_items (order_item_id,order_id,product_id,quantity,unit_price) VALUES (%s,%s,%s,%s,%s)",
                            (f"ITEM-{n:03d}", oid, it.product_id, it.quantity, price))
            cur.execute("UPDATE inventory SET stock_quantity=stock_quantity-%s WHERE product_id=%s", (it.quantity, it.product_id))
            n += 1
        cur.execute("INSERT INTO payments (payment_id,order_id,amount,payment_method,payment_status,payment_time) VALUES (%s,%s,%s,%s,'PENDING',NOW())",
                    (f"PAY-{_next(cur, 'payments', 'payment_id', 'PAY'):03d}", oid, total, req.payment_method))
        cur.execute("INSERT INTO shipments (shipment_id,order_id,delivery_status,courier_partner,tracking_number) VALUES (%s,%s,'PROCESSING',%s,%s)",
                    (f"SHIP-{_next(cur, 'shipments', 'shipment_id', 'SHIP'):03d}", oid,
                     random.choice(["Delhivery", "Blue Dart", "DTDC"]), f"TRK{random.randint(100000000, 999999999)}"))
        con.commit()
        return {"success": True, "order_id": oid, "customer_id": cid, "total_amount": total}
    except HTTPException:
        con.rollback(); raise
    except Exception as e:
        con.rollback(); raise HTTPException(500, f"Could not place order: {e}")
    finally:
        cur.close(); con.close()
