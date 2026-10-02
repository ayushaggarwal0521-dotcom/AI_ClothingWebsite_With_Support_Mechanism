import psycopg2


# Size rules based on product category
SIZE_MAPPING = {
    "Hoodies": ["S", "M", "L", "XL"],
    "Jackets": ["S", "M", "L", "XL"],
    "Jeans": ["30", "32", "34", "36"],
    "Pants": ["30", "32", "34", "36"],
    "Shirts": ["S", "M", "L", "XL"],
    "Shorts": ["30", "32", "34", "36"],
    "Sweatshirts": ["S", "M", "L", "XL"],
    "T-Shirts": ["S", "M", "L", "XL"]
}


def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="clothing_store",
        user="postgres",
        password="Wecandoit1@"
    )


def main():

    connection = get_connection()
    cursor = connection.cursor()

    # Get all products
    cursor.execute("""
        SELECT product_id, category
        FROM products
        ORDER BY product_id;
    """)

    products = cursor.fetchall()

    print(f"Found {len(products)} products.")

    for product_id, category in products:

        sizes = SIZE_MAPPING.get(category)

        if not sizes:
            print(f"Skipping {product_id}: unknown category '{category}'")
            continue

        for size in sizes:

            # Check whether this product-size combination already exists
            cursor.execute("""
                SELECT 1
                FROM product_sizes
                WHERE product_id = %s
                AND size = %s;
            """, (product_id, size))

            exists = cursor.fetchone()

            if exists:
                continue

            # Generate a new product-size ID
            cursor.execute("""
                SELECT COUNT(*)
                FROM product_sizes;
            """)

            count = cursor.fetchone()[0]
            product_size_id = f"PS-{count + 1:03d}"

            cursor.execute("""
                INSERT INTO product_sizes (
                    product_size_id,
                    product_id,
                    size
                )
                VALUES (%s, %s, %s);
            """, (
                product_size_id,
                product_id,
                size
            ))

    connection.commit()

    cursor.close()
    connection.close()

    print("Product sizes seeded successfully.")


if __name__ == "__main__":
    main()