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


ORDER_STATUSES = [
    "PLACED",
    "CONFIRMED",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
]


def generate_orders(count=100):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get existing customers
    cursor.execute("SELECT customer_id FROM customers")
    customers = [row[0] for row in cursor.fetchall()]
    # Get all customer IDs from PostgreSQL and put only the customer IDs into a Python list

    if not customers:
        print("No customers found. Seed customers first.")
        cursor.close()
        connection.close()
        return

    orders = []

    for number in range(1, count + 1):

        order_id = f"ORD-{number:03d}"

        customer_id = random.choice(customers)

        order_date = datetime.now() - timedelta(
            days=random.randint(1, 180)
        )

        status = random.choice(ORDER_STATUSES)

        total_amount = round(
            random.uniform(499, 7999),
            2
        )

        orders.append(
            (
                order_id,
                customer_id,
                order_date,
                status,
                total_amount,
            )
        )

    insert_query = """
    INSERT INTO orders (
        order_id,
        customer_id,
        order_date,
        status,
        total_amount
    )
    VALUES (%s, %s, %s, %s, %s)
    """

    for order in orders:
        cursor.execute(insert_query, order)

    connection.commit()

    print(f"Orders inserted: {len(orders)}")

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("ORDER SEEDING COMPLETE")


if __name__ == "__main__":
    generate_orders(100)