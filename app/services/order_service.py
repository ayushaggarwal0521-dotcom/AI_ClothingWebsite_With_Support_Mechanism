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
        JOIN shipments s
            ON o.order_id = s.order_id
        WHERE o.order_id = %s
    """, (order_id,))

    order = cursor.fetchone()

    cursor.close()
    connection.close()

    if order is None:
        return {
            "success": False,
            "reason": "Order or shipment not found."
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


def cancel_order(order_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            order_date
        FROM orders
        WHERE order_id = %s
    """, (order_id,))

    order = cursor.fetchone()

    cursor.close()
    connection.close()

    if order is None:
        return {
            "success": False,
            "reason": "Order not found."
        }

    order_date = order[0]

    cancellation_deadline = order_date + timedelta(hours=12)

    current_time = datetime.now()

    if current_time <= cancellation_deadline:
        return {
            "success": True,
            "cancellation_allowed": True,
            "order_id": order_id,
            "cancellation_deadline": cancellation_deadline,
            "support_email": "abc@gmail.com"
        }

    return {
        "success": True,
        "cancellation_allowed": False,
        "order_id": order_id,
        "reason": "The 12-hour cancellation window has expired."
    }