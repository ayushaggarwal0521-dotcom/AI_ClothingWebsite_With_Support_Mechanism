import os
import random

import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "clothing_store",
    "user": "postgres",
    "password": os.getenv("LOCAL_DB_PASSWORD"),
}


REFUND_STATUSES = [
    "PENDING",
    "PROCESSING",
    "COMPLETED",
]


REFUND_METHODS = [
    "ORIGINAL_PAYMENT_METHOD",
    "UPI",
    "BANK_TRANSFER",
]


def seed_refunds():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get existing returns
    cursor.execute("""
        SELECT
            return_id,
            order_id
        FROM returns
    """)

    returns = cursor.fetchall()

    if not returns:
        print("No returns found. Seed returns first.")
        cursor.close()
        connection.close()
        return

    # Select some returns that will receive refunds
    number_of_refunds = min(
        random.randint(10, 20),
        len(returns)
    )

    selected_returns = random.sample(
        returns,
        number_of_refunds
    )

    refund_number = 1

    for return_id, order_id in selected_returns:

        # Find order items belonging to this order
        cursor.execute("""
            SELECT
                order_item_id,
                quantity,
                unit_price
            FROM order_items
            WHERE order_id = %s
        """, (order_id,))

        order_items = cursor.fetchall()

        if not order_items:
            continue

        # Select one purchased item for the refund
        order_item_id, quantity, unit_price = random.choice(
            order_items
        )

        # Calculate refund amount
        refund_amount = round(
            float(unit_price) * quantity,
            2
        )

        refund_id = f"REF-{refund_number:03d}"

        refund_status = random.choice(
            REFUND_STATUSES
        )

        refund_method = random.choice(
            REFUND_METHODS
        )

        insert_query = """
        INSERT INTO refunds (
            refund_id,
            order_id,
            order_item_id,
            refund_amount,
            refund_status,
            refund_method,
            return_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                refund_id,
                order_id,
                order_item_id,
                refund_amount,
                refund_status,
                refund_method,
                return_id,
            )
        )

        refund_number += 1

    connection.commit()

    print(
        f"Refund records inserted: "
        f"{refund_number - 1}"
    )

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("REFUND SEEDING COMPLETE")


if __name__ == "__main__":
    seed_refunds()