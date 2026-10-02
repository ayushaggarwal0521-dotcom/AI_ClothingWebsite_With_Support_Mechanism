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


def seed_order_items():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get existing orders
    cursor.execute("SELECT order_id FROM orders")
    orders = [row[0] for row in cursor.fetchall()]

    # Get existing products and their prices
    cursor.execute("SELECT product_id, price FROM products")
    products = cursor.fetchall()

    if not orders:
        print("No orders found. Seed orders first.")
        cursor.close()
        connection.close()
        return

    if not products:
        print("No products found. Load products first.")
        cursor.close()
        connection.close()
        return

    order_item_number = 1

    for order_id in orders:

        # Each order gets 1 to 4 products
        number_of_items = random.randint(1, 4)

        selected_products = random.sample(
            products,
            number_of_items
        )

        for product_id, price in selected_products:

            order_item_id = f"ITEM-{order_item_number:03d}"

            quantity = random.randint(1, 3)

            insert_query = """
            INSERT INTO order_items (
                order_item_id,
                order_id,
                product_id,
                quantity,
                unit_price
            )
            VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(
                insert_query,
                (
                    order_item_id,
                    order_id,
                    product_id,
                    quantity,
                    price,
                )
            )

            order_item_number += 1

    connection.commit()

    print(f"Order items inserted: {order_item_number - 1}")

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("ORDER ITEM SEEDING COMPLETE")


if __name__ == "__main__":
    seed_order_items()