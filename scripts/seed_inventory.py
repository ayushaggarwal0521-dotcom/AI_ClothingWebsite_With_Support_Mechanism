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


def seed_inventory():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get all existing products
    cursor.execute("SELECT product_id FROM products")
    products = [row[0] for row in cursor.fetchall()]

    if not products:
        print("No products found. Load products first.")
        cursor.close()
        connection.close()
        return

    for number, product_id in enumerate(products, start=1):

        inventory_id = f"INV-{number:03d}"

        stock_quantity = random.randint(0, 50)

        insert_query = """
        INSERT INTO inventory (
            inventory_id,
            product_id,
            stock_quantity
        )
        VALUES (%s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                inventory_id,
                product_id,
                stock_quantity,
            )
        )

    connection.commit()

    print(f"Inventory records inserted: {len(products)}")

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("INVENTORY SEEDING COMPLETE")


if __name__ == "__main__":
    seed_inventory()