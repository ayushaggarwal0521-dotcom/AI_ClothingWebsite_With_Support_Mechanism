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


RETURN_REASONS = [
    "Size issue",
    "Wrong product received",
    "Product damaged",
    "Color not as expected",
    "Changed my mind",
]


RETURN_STATUSES = [
    "REQUESTED",
    "APPROVED",
    "PICKUP_SCHEDULED",
    "RECEIVED",
    "COMPLETED",
]


def seed_returns():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get orders that have shipments
    cursor.execute("""
        SELECT
            s.shipment_id,
            s.order_id
        FROM shipments s
    """)

    shipments = cursor.fetchall()

    if not shipments:
        print("No shipments found. Seed shipments first.")
        cursor.close()
        connection.close()
        return

    # Select a subset of shipments for returns
    number_of_returns = min(
        random.randint(15, 25),
        len(shipments)
    )

    selected_shipments = random.sample(
        shipments,
        number_of_returns
    )

    for number, (shipment_id, order_id) in enumerate(
        selected_shipments,
        start=1
    ):

        return_id = f"RET-{number:03d}"

        return_reason = random.choice(
            RETURN_REASONS
        )

        return_status = random.choice(
            RETURN_STATUSES
        )

        return_request_time = datetime.now() - timedelta(
            days=random.randint(1, 60)
        )

        insert_query = """
        INSERT INTO returns (
            return_id,
            order_id,
            shipment_id,
            return_reason,
            return_status,
            return_request_time
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                return_id,
                order_id,
                shipment_id,
                return_reason,
                return_status,
                return_request_time,
            )
        )

    connection.commit()

    print(
        f"Return records inserted: "
        f"{number_of_returns}"
    )

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("RETURN SEEDING COMPLETE")


if __name__ == "__main__":
    seed_returns()