import os
import random
from datetime import timedelta

import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "clothing_store",
    "user": "postgres",
    "password": os.getenv("LOCAL_DB_PASSWORD"),
}


CUSTOMER_MESSAGES = [
    "Where is my order?",
    "Can you tell me my order status?",
    "I want to return this product.",
    "My product arrived damaged.",
    "I received the wrong size.",
    "When will my refund arrive?",
    "My payment failed.",
    "Can I cancel my order?",
    "Is this product available in my size?",
    "I need help with my order.",
]


ASSISTANT_MESSAGES = [
    "Sure, let me check your order details.",
    "I'll check the latest status for you.",
    "Let me look into that for you.",
    "I can help you with that.",
    "I'll check the available information.",
    "Let me verify the details of your order.",
]


AGENT_MESSAGES = [
    "I've checked the issue and will take care of it.",
    "I've reviewed the case and updated the ticket.",
    "I'll help resolve this issue for you.",
    "I've reviewed your request.",
]


def seed_messages():
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get existing conversations
    cursor.execute("""
        SELECT
            conversation_id,
            created_at
        FROM conversations
    """)

    conversations = cursor.fetchall()

    if not conversations:
        print("No conversations found. Seed conversations first.")
        cursor.close()
        connection.close()
        return

    message_number = 1

    for conversation_id, created_at in conversations:

        # Each conversation gets 3 to 8 messages
        number_of_messages = random.randint(3, 8)

        current_time = created_at

        for message_index in range(number_of_messages):

            message_id = f"MSG-{message_number:03d}"

            # First message is always from customer
            if message_index == 0:

                sender_type = "customer"

                message_text = random.choice(
                    CUSTOMER_MESSAGES
                )

            else:

                # Most messages are customer/assistant.
                # Occasionally a human agent joins.
                sender_type = random.choices(
                    ["customer", "assistant", "agent"],
                    weights=[35, 55, 10],
                    k=1
                )[0]

                if sender_type == "customer":
                    message_text = random.choice(
                        CUSTOMER_MESSAGES
                    )

                elif sender_type == "assistant":
                    message_text = random.choice(
                        ASSISTANT_MESSAGES
                    )

                else:
                    message_text = random.choice(
                        AGENT_MESSAGES
                    )

            current_time = current_time + timedelta(
                minutes=random.randint(1, 10)
            )

            insert_query = """
            INSERT INTO messages (
                message_id,
                conversation_id,
                sender_type,
                message_text,
                message_time
            )
            VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(
                insert_query,
                (
                    message_id,
                    conversation_id,
                    sender_type,
                    message_text,
                    current_time,
                )
            )

            message_number += 1

    connection.commit()

    print(
        f"Messages inserted: "
        f"{message_number - 1}"
    )

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("MESSAGE SEEDING COMPLETE")


if __name__ == "__main__":
    seed_messages()