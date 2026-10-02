import json
from pathlib import Path

import psycopg2


# -----------------------------
# Paths
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCTS_FILE = BASE_DIR / "data" / "products.json"


# -----------------------------
# PostgreSQL configuration
# -----------------------------

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "clothing_store",
    "user": "postgres",
    "password": "Wecandoit1@",
}


# -----------------------------
# Load JSON data
# -----------------------------

with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
    products = json.load(file)


print(f"Products found in JSON: {len(products)}")


# -----------------------------
# Connect to PostgreSQL
# -----------------------------

connection = psycopg2.connect(**DB_CONFIG)

cursor = connection.cursor()


# -----------------------------
# Insert products
# -----------------------------

insert_query = """
INSERT INTO products (
    product_id,
    name,
    category,
    price
)
VALUES (%s, %s, %s, %s)
"""


for product in products:

    cursor.execute(
        insert_query,
        (
            product["product_id"],
            product["name"],
            product["category"],
            product["price"],
        )
    )


# -----------------------------
# Save changes
# -----------------------------

connection.commit()


print(f"Products inserted: {len(products)}")


# -----------------------------
# Close connection
# -----------------------------

cursor.close()
connection.close()

print("Database connection closed.")
print("PRODUCT IMPORT COMPLETE")