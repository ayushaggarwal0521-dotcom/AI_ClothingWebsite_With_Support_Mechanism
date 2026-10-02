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


CATEGORIES = [
    "T-Shirts",
    "Shirts",
    "Pants",
    "Jeans",
    "Hoodies",
    "Jackets",
    "Sweatshirts",
    "Shorts",
]


SIZES = [
    "S",
    "M",
    "L",
    "XL",
]


COLORS = [
    "Black",
    "White",
    "Blue",
    "Grey",
    "Green",
    "Brown",
    "Beige",
    "Navy",
]


STYLES = [
    "Casual",
    "Streetwear",
    "Minimal",
    "Sporty",
    "Formal",
]


def seed_customer_preferences():
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

    # Only some customers have saved preferences
    number_of_preferences = min(40, len(customers))

    selected_customers = random.sample(
        customers,
        number_of_preferences
    )

    for number, customer_id in enumerate(
        selected_customers,
        start=1
    ):

        preference_id = f"PREF-{number:03d}"

        preferred_category = random.choice(
            CATEGORIES
        )

        preferred_size = random.choice(
            SIZES
        )

        preferred_color = random.choice(
            COLORS
        )

        preferred_style = random.choice(
            STYLES
        )

        insert_query = """
        INSERT INTO customer_preferences (
            preference_id,
            customer_id,
            preferred_category,
            preferred_size,
            preferred_color,
            preferred_style
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            insert_query,
            (
                preference_id,
                customer_id,
                preferred_category,
                preferred_size,
                preferred_color,
                preferred_style,
            )
        )

    connection.commit()

    print(
        f"Customer preferences inserted: "
        f"{number_of_preferences}"
    )

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("CUSTOMER PREFERENCE SEEDING COMPLETE")


if __name__ == "__main__":
    seed_customer_preferences()