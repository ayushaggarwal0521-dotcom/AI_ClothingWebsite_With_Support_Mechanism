import os
import random
from datetime import datetime, timedelta

import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "clothing_store",
    "user": "postgres",
    "password": os.getenv("LOCAL_DB_PASSWORD"),
}


PAYMENT_METHODS = [
    "UPI",
    "CARD",
    "NET_BANKING",
    "COD",
    "WALLET",
]


def seed_payments():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get existing orders
    cursor.execute(
        "SELECT order_id, total_amount, order_date FROM orders"
    )

    orders = cursor.fetchall()

    if not orders:
        print("No orders found. Seed orders first.")
        cursor.close()
        connection.close()
        return

    payment_number = 1

    for order_id, total_amount, order_date in orders:

        # Most orders have one payment attempt.
        # Some orders will have a failed attempt followed by success.
        has_retry = random.random() < 0.25

        if has_retry:

            # First attempt fails
            payment_id = f"PAY-{payment_number:03d}"

            payment_method = random.choice(PAYMENT_METHODS)

            payment_time = order_date + timedelta(
                minutes=random.randint(1, 10)
            )

            insert_query = """
            INSERT INTO payments (
                payment_id,
                order_id,
                amount,
                payment_method,
                payment_status,
                payment_time
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                insert_query,
                (
                    payment_id,
                    order_id,
                    total_amount,
                    payment_method,
                    "FAILED",
                    payment_time,
                )
            )

            payment_number += 1

            # Second attempt succeeds
            payment_id = f"PAY-{payment_number:03d}"

            payment_method = random.choice(PAYMENT_METHODS)

            payment_time = payment_time + timedelta(
                minutes=random.randint(1, 15)
            )

            cursor.execute(
                insert_query,
                (
                    payment_id,
                    order_id,
                    total_amount,
                    payment_method,
                    "SUCCESS",
                    payment_time,
                )
            )

            payment_number += 1

        else:

            payment_id = f"PAY-{payment_number:03d}"

            payment_method = random.choice(PAYMENT_METHODS)

            payment_time = order_date + timedelta(
                minutes=random.randint(1, 10)
            )

            insert_query = """
            INSERT INTO payments (
                payment_id,
                order_id,
                amount,
                payment_method,
                payment_status,
                payment_time
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                insert_query,
                (
                    payment_id,
                    order_id,
                    total_amount,
                    payment_method,
                    "SUCCESS",
                    payment_time,
                )
            )

            payment_number += 1

    connection.commit()

    print(f"Payment records inserted: {payment_number - 1}")

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("PAYMENT SEEDING COMPLETE")


if __name__ == "__main__":
    seed_payments()