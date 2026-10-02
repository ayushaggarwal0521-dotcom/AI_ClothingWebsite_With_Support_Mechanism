import psycopg2
import random


# Category-specific attribute rules
CATEGORY_RULES = {
    "T-Shirts": {
        "gender": ["Men", "Women", "Unisex"],
        "material": ["Cotton", "Polyester"],
        "fit": ["Regular", "Slim", "Oversized", "Relaxed"],
        "color": ["Black", "White", "Blue", "Grey", "Green", "Beige"]
    },

    "Shirts": {
        "gender": ["Men", "Women"],
        "material": ["Cotton", "Linen", "Polyester"],
        "fit": ["Regular", "Slim", "Relaxed"],
        "color": ["Black", "White", "Blue", "Grey", "Green", "Beige"]
    },

    "Jeans": {
        "gender": ["Men", "Women"],
        "material": ["Denim"],
        "fit": ["Slim", "Regular", "Relaxed"],
        "color": ["Black", "Blue", "Grey"]
    },

    "Pants": {
        "gender": ["Men", "Women"],
        "material": ["Cotton", "Polyester", "Linen"],
        "fit": ["Regular", "Slim", "Relaxed"],
        "color": ["Black", "Beige", "Grey", "Blue", "Green"]
    },

    "Shorts": {
        "gender": ["Men", "Women", "Unisex"],
        "material": ["Cotton", "Polyester"],
        "fit": ["Regular", "Relaxed"],
        "color": ["Black", "White", "Blue", "Grey", "Green", "Beige"]
    },

    "Hoodies": {
        "gender": ["Men", "Women", "Unisex"],
        "material": ["Cotton", "Polyester"],
        "fit": ["Regular", "Oversized", "Relaxed"],
        "color": ["Black", "White", "Blue", "Grey", "Green", "Beige"]
    },

    "Sweatshirts": {
        "gender": ["Men", "Women", "Unisex"],
        "material": ["Cotton", "Polyester"],
        "fit": ["Regular", "Oversized", "Relaxed"],
        "color": ["Black", "White", "Blue", "Grey", "Green", "Beige"]
    },

    "Jackets": {
        "gender": ["Men", "Women", "Unisex"],
        "material": ["Denim", "Polyester", "Cotton"],
        "fit": ["Regular", "Slim", "Relaxed"],
        "color": ["Black", "Blue", "Grey", "Green", "Beige"]
    }
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

    updated_count = 0

    for product_id, category in products:

        rules = CATEGORY_RULES.get(category)

        if not rules:
            print(f"Skipping {product_id}: unknown category '{category}'")
            continue

        # Randomly select realistic attributes
        color = random.choice(rules["color"])
        gender = random.choice(rules["gender"])
        material = random.choice(rules["material"])
        fit = random.choice(rules["fit"])

        cursor.execute("""
            UPDATE products
            SET
                color = %s,
                gender = %s,
                material = %s,
                fit = %s
            WHERE product_id = %s;
        """, (
            color,
            gender,
            material,
            fit,
            product_id
        ))

        updated_count += 1

        print(
            f"{product_id} → "
            f"{color}, {gender}, {material}, {fit}"
        )

    connection.commit()

    cursor.close()
    connection.close()

    print()
    print(f"Updated {updated_count} products successfully.")


if __name__ == "__main__":
    main()