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


TICKET_MESSAGES = [
    "Where is my order?",
    "My order has not arrived yet.",
    "I received the wrong product.",
    "I want to return my order.",
    "Can I get a refund?",
    "My payment failed but money was deducted.",
    "The product I received is damaged.",
    "I want to know my shipment status.",
    "Can I cancel my order?",
    "I need help with sizing.",
    "My refund has not arrived yet.",
    "I received a different size than I ordered.",
]


TICKET_STATUSES = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
]


PRIORITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "URGENT",
]


def seed_support_tickets():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get existing customers
    cursor.execute("""
        SELECT customer_id
        FROM customers
    """)

    customers = [row[0] for row in cursor.fetchall()]

    if not customers:
        print("No customers found. Seed customers first.")
        cursor.close()
        connection.close()
        return

    # Get existing orders
    cursor.execute("""
        SELECT order_id, customer_id
        FROM orders
    """)

    orders = cursor.fetchall()

    # Get existing shipments
    cursor.execute("""
        SELECT shipment_id, order_id
        FROM shipments
    """)

    shipments = cursor.fetchall()

    # Get existing refunds
    cursor.execute("""
        SELECT refund_id, order_id
        FROM refunds
    """)

    refunds = cursor.fetchall()

    number_of_tickets = 25

    for number in range(1, number_of_tickets + 1):

        support_ticket_id = f"TKT-{number:03d}"

        customer_id = random.choice(customers)

        actual_message = random.choice(
            TICKET_MESSAGES
        )

        ticket_status = random.choice(
            TICKET_STATUSES
        )

        priority = random.choice(
            PRIORITIES
        )

        ticket_creation_time = datetime.now() - timedelta(
            days=random.randint(1, 60)
        )

        # Default: ticket is not connected to an order
        order_id = None
        shipment_id = None
        refund_id = None

        # Sometimes connect the ticket to an order
        if orders and random.random() < 0.75:

            customer_orders = [
                order
                for order in orders
                if order[1] == customer_id
            ]

            if customer_orders:

                order_id, _ = random.choice(
                    customer_orders
                )

                # Sometimes connect shipment
                matching_shipments = [
                    shipment
                    for shipment in shipments
                    if shipment[1] == order_id
                ]

                if matching_shipments and random.random() < 0.6:
                    shipment_id, _ = random.choice(
                        matching_shipments
                    )

                # Sometimes connect refund
                matching_refunds = [
                    refund
                    for refund in refunds
                    if refund[1] == order_id
                ]

                if matching_refunds and random.random() < 0.4:
                    refund_id, _ = random.choice(
                        matching_refunds
                    )

        insert_query = """
        INSERT INTO support_tickets (
            support_ticket_id,
            customer_id,
            order_id,
            shipment_id,
            refund_id,
            actual_message,
            ticket_status,
            priority,
            ticket_creation_time
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                support_ticket_id,
                customer_id,
                order_id,
                shipment_id,
                refund_id,
                actual_message,
                ticket_status,
                priority,
                ticket_creation_time,
            )
        )

    connection.commit()

    print(
        f"Support tickets inserted: "
        f"{number_of_tickets}"
    )

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("SUPPORT TICKET SEEDING COMPLETE")


if __name__ == "__main__":
    seed_support_tickets()