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


COURIER_PARTNERS = [
    "Delhivery",
    "Blue Dart",
    "DTDC",
    "Ecom Express",
    "XpressBees",
]


DELIVERY_STATUSES = [
    "PROCESSING",
    "SHIPPED",
    "IN_TRANSIT",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
]


def seed_shipments():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get existing orders
    cursor.execute(
        "SELECT order_id, status FROM orders"
    )

    orders = cursor.fetchall()

    if not orders:
        print("No orders found. Seed orders first.")
        cursor.close()
        connection.close()
        return

    shipment_number = 1

    for order_id, order_status in orders:

        # Cancelled orders will not be shipped
        if order_status == "CANCELLED":
            continue

        shipment_id = f"SHIP-{shipment_number:03d}"

        delivery_status = random.choice(
            DELIVERY_STATUSES
        )

        courier_partner = random.choice(
            COURIER_PARTNERS
        )

        tracking_number = (
            f"TRK{random.randint(100000000, 999999999)}"
        )

        insert_query = """
        INSERT INTO shipments (
            shipment_id,
            order_id,
            delivery_status,
            courier_partner,
            tracking_number
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                shipment_id,
                order_id,
                delivery_status,
                courier_partner,
                tracking_number,
            )
        )

        shipment_number += 1

    connection.commit()

    print(
        f"Shipment records inserted: "
        f"{shipment_number - 1}"
    )

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("SHIPMENT SEEDING COMPLETE")


if __name__ == "__main__":
    seed_shipments()