from app.database import get_connection
from datetime import datetime, timedelta

def get_order_status(order_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            o.status,
            s.delivery_status,
            s.courier_partner,
            s.tracking_number
        FROM orders o
        LEFT JOIN shipments s
            ON o.order_id = s.order_id
        WHERE o.order_id = %s
    """, (order_id,))

    order = cursor.fetchone()

    cursor.close()
    connection.close()

    if order is None:
        return {
            "success": False,
            "reason": "Order not found."
        }

    return {
        "success": True,
        "order_id": order_id,
        "order_status": order[0],
        "delivery_status": order[1],
        "courier_partner": order[2],
        "tracking_number": order[3]
    }




def get_customer_order_statuses(customer_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            o.order_id,
            o.order_date,
            o.status,
            s.delivery_status,
            s.tracking_number,
            s.courier_partner
        FROM orders o
        LEFT JOIN shipments s
            ON o.order_id = s.order_id
        WHERE o.customer_id = %s
        ORDER BY o.order_date DESC
    """, (customer_id,))

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    result = []

    for order in orders:
        result.append({
            "order_id": order[0],
            "order_date": order[1],
            "order_status": order[2],
            "delivery_status": order[3],
            "tracking_number": order[4],
            "courier_partner": order[5]
        })

    return {
        "success": True,
        "customer_id": customer_id,
        "orders": result
    }



def get_order_items(order_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            oi.order_item_id,
            oi.product_id,
            oi.quantity,
            p.name,
            p.category
        FROM order_items oi
        INNER JOIN products p
            ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
    """, (order_id,))

    items = cursor.fetchall()
    
    if not items:
        cursor.close()
        connection.close()

        return {
            "success": False,
            "reason": "Order not found."
        }

    cursor.close()
    connection.close()

    result = []

    for item in items:
        result.append({
            "order_item_id": item[0],
            "product_id": item[1],
            "quantity": item[2],
            "name": item[3],
            "category": item[4]
        })

    return {
        "success": True,
        "order_id": order_id,
        "items": result
    }


def check_cancellation_eligibility(order_id: str):
    """Read-only. Does NOT change anything."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT order_date, status
        FROM orders
        WHERE order_id = %s
    """, (order_id,))

    order = cursor.fetchone()

    cursor.close()
    connection.close()

    if order is None:
        return {"success": False, "reason": "Order not found."}

    order_date, status = order

    if status == "CANCELLED":
        return {"success": True, "cancellation_allowed": False,
                "order_id": order_id,
                "reason": "This order is already cancelled."}

    if status in ("SHIPPED", "DELIVERED"):
        return {"success": True, "cancellation_allowed": False,
                "order_id": order_id,
                "reason": f"The order is already {status.lower()} and can no longer be cancelled. A return can be requested after delivery."}

    deadline = order_date + timedelta(hours=12)

    if datetime.now() > deadline:
        return {"success": True, "cancellation_allowed": False,
                "order_id": order_id,
                "reason": "The 12-hour cancellation window has expired."}

    return {"success": True, "cancellation_allowed": True,
            "order_id": order_id, "cancellation_deadline": deadline,
            "support_email": "abc@gmail.com"}


def cancel_order(order_id: str):
    """Actually cancels the order (status -> CANCELLED) and restores stock.
    Re-checks eligibility first, so it is safe even if called directly."""

    check = check_cancellation_eligibility(order_id)

    if not check.get("success") or not check.get("cancellation_allowed"):
        return check

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE orders SET status = 'CANCELLED'
            WHERE order_id = %s
              AND status NOT IN ('CANCELLED', 'SHIPPED', 'DELIVERED')
        """, (order_id,))

        if cursor.rowcount == 0:
            connection.rollback()
            return {"success": False, "reason": "Order could not be cancelled."}

        cursor.execute("""
            UPDATE inventory i
            SET stock_quantity = i.stock_quantity + oi.quantity
            FROM order_items oi
            WHERE oi.order_id = %s
              AND oi.product_id = i.product_id
        """, (order_id,))

        connection.commit()

        return {"success": True, "cancelled": True, "order_id": order_id,
                "order_status": "CANCELLED", "support_email": "abc@gmail.com"}

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
