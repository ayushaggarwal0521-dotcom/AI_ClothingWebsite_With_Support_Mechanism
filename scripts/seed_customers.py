import random
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "clothing_store",
    "user": "postgres",
    "password": "Wecandoit1@",
}


FIRST_NAMES = [
    "Aarav",
    "Arjun",
    "Aditya",
    "Rahul",
    "Rohan",
    "Karan",
    "Vivek",
    "Ankit",
    "Priya",
    "Ananya",
    "Neha",
    "Riya",
    "Simran",
    "Kavya",
    "Isha",
]

LAST_NAMES = [
    "Sharma",
    "Verma",
    "Mehta",
    "Gupta",
    "Agarwal",
    "Malhotra",
    "Kapoor",
    "Singh",
    "Bansal",
    "Khanna",
]


def generate_phone():
    return "9" + "".join(str(random.randint(0, 9)) for _ in range(9))


def generate_customers(count=50):
    customers = []

    for number in range(1, count + 1):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        name = f"{first_name} {last_name}"

        email = (
            f"{first_name.lower()}.{last_name.lower()}"
            f"{number}@example.com"
        )

        phone = generate_phone()

        created_at = datetime.now() - timedelta(
            days=random.randint(1, 365)
        )

        customers.append(
            (
                f"CUST-{number:03d}",
                name,
                email,
                phone,
                created_at,
            )
        )

    return customers


def main():
    customers = generate_customers(50)

    print(f"Customers generated: {len(customers)}")

    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    insert_query = """
    INSERT INTO customers (
        customer_id,
        name,
        email,
        phone,
        created_at
    )
    VALUES (%s, %s, %s, %s, %s)
    """

    for customer in customers:
        cursor.execute(insert_query, customer)

    connection.commit()

    print(f"Customers inserted: {len(customers)}")

    cursor.close()
    connection.close()

    print("Database connection closed.")
    print("CUSTOMER SEEDING COMPLETE")


if __name__ == "__main__":
    main()