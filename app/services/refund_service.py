from app.database import get_connection
def get_refund_status(return_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.refund_id,
            r.refund_status,
            r.refund_amount,
            r.refund_method
        FROM refunds r
        WHERE r.return_id = %s
    """, (return_id,))

    refund = cursor.fetchone()

    cursor.close()
    connection.close()

    if refund is None:
        return {
            "success": False,
            "reason": "Refund not found for this return."
        }

    return {
        "success": True,
        "return_id": return_id,
        "refund_id": refund[0],
        "refund_status": refund[1],
        "refund_amount": float(refund[2]),
        "refund_method": refund[3]
    }