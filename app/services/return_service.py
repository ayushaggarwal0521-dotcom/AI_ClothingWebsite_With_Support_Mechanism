from datetime import datetime
import uuid
from app.database import get_connection


RETURN_WINDOW_DAYS = 15


def check_return_eligibility(
    order_id: str,
    order_item_id: str,
    return_quantity: int
):
    connection = get_connection()
    cursor = connection.cursor()

    # 1. Validate requested quantity
    if return_quantity <= 0:
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "reason": "Return quantity must be greater than 0."
        }

    # 2. Get the order item and verify that it belongs to the order
    cursor.execute("""
        SELECT
            oi.order_item_id,
            oi.order_id,
            oi.quantity,
            p.name
        FROM order_items oi
        JOIN products p
            ON oi.product_id = p.product_id
        WHERE oi.order_item_id = %s
          AND oi.order_id = %s
    """, (order_item_id, order_id))

    order_item = cursor.fetchone()

    if order_item is None:
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "reason": "The specified product does not belong to this order."
        }

    _, _, ordered_quantity, product_name = order_item

    # 3. Check delivery status
    cursor.execute("""
        SELECT
            delivery_status,
            delivered_at
        FROM shipments
        WHERE order_id = %s
    """, (order_id,))

    shipment = cursor.fetchone()

    if shipment is None:
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "reason": "Shipment not found for this order."
        }

    delivery_status, delivered_at = shipment

    if delivery_status != "DELIVERED":
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "reason": "Order has not been delivered yet."
        }

    # 4. Make sure delivery date exists
    if delivered_at is None:
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "reason": "Delivery date is not available."
        }

    # 5. Check return window
    days_since_delivery = (
        datetime.now() - delivered_at
    ).days

    if days_since_delivery > RETURN_WINDOW_DAYS:
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "days_since_delivery": days_since_delivery,
            "reason": (
                f"Return window has expired. "
                f"The order was delivered {days_since_delivery} days ago."
            )
        }

    # 6. Calculate how many units have already been returned
    cursor.execute("""
        SELECT COALESCE(SUM(return_quantity), 0)
        FROM returns
        WHERE order_item_id = %s
    """, (order_item_id,))

    already_returned_quantity = cursor.fetchone()[0]

    # 7. Calculate remaining returnable quantity
    returnable_quantity = (
        ordered_quantity - already_returned_quantity
    )

    # 8. Make sure there is something left to return
    if returnable_quantity <= 0:
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "product_name": product_name,
            "ordered_quantity": ordered_quantity,
            "already_returned_quantity": already_returned_quantity,
            "returnable_quantity": 0,
            "reason": (
                "The full quantity of this product has already been returned."
            )
        }

    # 9. Make sure requested quantity fits within remaining quantity
    if return_quantity > returnable_quantity:
        cursor.close()
        connection.close()
        return {
            "eligible": False,
            "product_name": product_name,
            "ordered_quantity": ordered_quantity,
            "already_returned_quantity": already_returned_quantity,
            "returnable_quantity": returnable_quantity,
            "requested_return_quantity": return_quantity,
            "reason": (
                f"Only {returnable_quantity} unit(s) of this product "
                f"are still eligible for return."
            )
        }

    cursor.close()
    connection.close()

    # 10. Everything passed
    return {
        "eligible": True,
        "product_name": product_name,
        "ordered_quantity": ordered_quantity,
        "already_returned_quantity": already_returned_quantity,
        "returnable_quantity": returnable_quantity,
        "requested_return_quantity": return_quantity,
        "days_since_delivery": days_since_delivery,
        "reason": (
            f"{return_quantity} unit(s) of {product_name} "
            f"are eligible for return."
        )
    }



def create_return(
    order_id: str,
    order_item_id: str,
    return_quantity: int,
    return_reason: str
):

    # First, verify that this specific item and quantity
    # are eligible for return.
    eligibility = check_return_eligibility(
        order_id,
        order_item_id,
        return_quantity
    )

    if not eligibility["eligible"]:
        return {
            "success": False,
            "reason": eligibility["reason"]
        }

    connection = get_connection()
    cursor = connection.cursor()

    # Get the shipment associated with this order.
    cursor.execute("""
        SELECT shipment_id
        FROM shipments
        WHERE order_id = %s
    """, (order_id,))

    shipment = cursor.fetchone()

    if shipment is None:
        cursor.close()
        connection.close()

        return {
            "success": False,
            "reason": "Shipment not found for this order."
        }

    shipment_id = shipment[0]

    # Generate a unique return ID.
    return_id = "RET-" + str(uuid.uuid4())[:8]

    # Create the return request.
    cursor.execute("""
        INSERT INTO returns (
            return_id,
            order_id,
            shipment_id,
            order_item_id,
            return_quantity,
            return_reason,
            return_status
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        return_id,
        order_id,
        shipment_id,
        order_item_id,
        return_quantity,
        return_reason,
        "REQUESTED"
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "success": True,
        "return_id": return_id,
        "order_id": order_id,
        "order_item_id": order_item_id,
        "return_quantity": return_quantity,
        "return_status": "REQUESTED",
        "reason": "Return request created successfully."
    }





def get_return_status(return_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.return_id,
            r.order_id,
            r.return_status,
            r.return_reason,
            r.return_request_time,
            r.order_item_id,
            r.return_quantity
        FROM returns AS r
        WHERE r.return_id = %s
    """, (return_id,))

    return_data = cursor.fetchone()

    cursor.close()
    connection.close()

    if return_data is None:
        return {
            "success": False,
            "reason": "Return not found."
        }

    return {
        "success": True,
        "return_id": return_data[0],
        "order_id": return_data[1],
        "return_status": return_data[2],
        "return_reason": return_data[3],
        "return_request_time": return_data[4],
        "order_item_id": return_data[5],
        "return_quantity": return_data[6]
    }