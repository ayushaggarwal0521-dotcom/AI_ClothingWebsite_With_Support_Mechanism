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


CONVERSATION_STATUSES = [
    "ACTIVE",
    "RESOLVED",
    "CLOSED",
]


def seed_conversations():
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

    # Get existing support tickets
    cursor.execute("""
        SELECT support_ticket_id, customer_id
        FROM support_tickets
    """)

    tickets = cursor.fetchall()

    number_of_conversations = 35

    for number in range(1, number_of_conversations + 1):

        conversation_id = f"CONV-{number:03d}"

        customer_id = random.choice(customers)

        status = random.choice(
            CONVERSATION_STATUSES
        )

        created_at = datetime.now() - timedelta(
            days=random.randint(1, 60)
        )

        updated_at = created_at + timedelta(
            minutes=random.randint(5, 120)
        )

        # A conversation may or may not be connected
        # to an existing support ticket.
        support_ticket_id = None

        customer_tickets = [
            ticket
            for ticket in tickets
            if ticket[1] == customer_id
        ]

        if customer_tickets and random.random() < 0.7:
            support_ticket_id, _ = random.choice(
                customer_tickets
            )

        insert_query = """
        INSERT INTO conversations (
            conversation_id,
            customer_id,
            support_ticket_id,
            status,
            created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                conversation_id,
                customer_id,
                support_ticket_id,
                status,
                created_at,
                updated_at,
            )
        )

    connection.commit()

    print(
        f"Conversations inserted: "
        f"{number_of_conversations}"
    )

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("CONVERSATION SEEDING COMPLETE")


if __name__ == "__main__":
    seed_conversations()