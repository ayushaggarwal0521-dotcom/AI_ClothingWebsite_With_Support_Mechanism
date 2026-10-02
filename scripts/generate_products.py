from pathlib import Path
# To easily defone the directory path of any file and in our case to define the loaction of our dataset
import json
# to handle json related processing
import random
# We're using this to randomly choose mock attributes.


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

DATASET_PATH = Path("dataset/raw")
#  This path tells the location of our data containing the images we would be furthur using to depict our clothes .
OUTPUT_PATH = Path("data/products.json")
#  THIS PATH IS THE PATH WHICH WILL BE CREATED AFTER RUNNING THIS FILE CONTAING THE MOCK PRODUCT.

# --------------------------------------------------
# 2. Mock product data
# --------------------------------------------------

PRODUCT_DATA = {
    "T-Shirts": {
        "names": [
            "Classic Cotton T-Shirt",
            "Oversized Graphic T-Shirt",
            "Essential Casual T-Shirt",
            "Premium Basic T-Shirt",
            "Relaxed Fit T-Shirt",
            "Urban Street T-Shirt",
        ],
        "fits": [
            "Regular",
            "Oversized",
            "Relaxed",
            "Slim",
        ],
        "materials": [
            "100% Cotton",
            "Cotton Blend",
            "Organic Cotton",
        ],
        "price_range": (999, 1999),
    },

    "Shirts": {
        "names": [
            "Classic Oxford Shirt",
            "Casual Linen Shirt",
            "Relaxed Cotton Shirt",
            "Slim Fit Formal Shirt",
            "Checked Casual Shirt",
        ],
        "fits": [
            "Regular",
            "Relaxed",
            "Slim",
        ],
        "materials": [
            "Cotton",
            "Linen",
            "Cotton Blend",
        ],
        "price_range": (1299, 2499),
    },

    "Pants": {
        "names": [
            "Relaxed Fit Trousers",
            "Classic Casual Pants",
            "Straight Fit Pants",
            "Comfort Cotton Trousers",
        ],
        "fits": [
            "Regular",
            "Relaxed",
            "Straight",
        ],
        "materials": [
            "Cotton",
            "Cotton Blend",
            "Polyester Blend",
        ],
        "price_range": (1499, 2999),
    },

    "Jeans": {
        "names": [
            "Classic Blue Jeans",
            "Slim Fit Jeans",
            "Straight Fit Denim",
            "Relaxed Denim Jeans",
        ],
        "fits": [
            "Slim",
            "Straight",
            "Relaxed",
        ],
        "materials": [
            "Denim",
            "Stretch Denim",
            "Cotton Denim",
        ],
        "price_range": (1799, 3499),
    },

    "Hoodies": {
        "names": [
            "Classic Pullover Hoodie",
            "Oversized Fleece Hoodie",
            "Minimal Logo Hoodie",
            "Everyday Comfort Hoodie",
        ],
        "fits": [
            "Regular",
            "Oversized",
            "Relaxed",
        ],
        "materials": [
            "Cotton Fleece",
            "Cotton Blend",
            "Polyester Fleece",
        ],
        "price_range": (1699, 2999),
    },

    "Jackets": {
        "names": [
            "Classic Casual Jacket",
            "Lightweight Bomber Jacket",
            "Utility Jacket",
            "Everyday Denim Jacket",
        ],
        "fits": [
            "Regular",
            "Relaxed",
            "Oversized",
        ],
        "materials": [
            "Denim",
            "Cotton",
            "Polyester",
            "Nylon",
        ],
        "price_range": (1999, 3999),
    },

    "Sweatshirts": {
        "names": [
            "Classic Crewneck Sweatshirt",
            "Oversized Sweatshirt",
            "Minimal Graphic Sweatshirt",
            "Everyday Fleece Sweatshirt",
        ],
        "fits": [
            "Regular",
            "Oversized",
            "Relaxed",
        ],
        "materials": [
            "Cotton Fleece",
            "Cotton Blend",
            "Polyester Blend",
        ],
        "price_range": (1499, 2799),
    },

    "Shorts": {
        "names": [
            "Classic Casual Shorts",
            "Cotton Comfort Shorts",
            "Relaxed Everyday Shorts",
            "Sport Casual Shorts",
        ],
        "fits": [
            "Regular",
            "Relaxed",
            "Slim",
        ],
        "materials": [
            "Cotton",
            "Cotton Blend",
            "Polyester",
        ],
        "price_range": (799, 1799),
    },
}
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

SIZES = [
    "S",
    "M",
    "L",
    "XL",
]

# --------------------------------------------------
# 3. Find image files
# --------------------------------------------------

image_files = sorted(
    [
        file
        for file in DATASET_PATH.iterdir()
        if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ],
    key=lambda file: int(file.stem)
    # sorts them numerically.
)


# --------------------------------------------------
# 4. Select 400 images
# --------------------------------------------------

image_files = image_files[:400]


# --------------------------------------------------
# 5. Create products
# --------------------------------------------------

products = []

for product_number in range(100):

    start_index = product_number * 4
    product_images = image_files[start_index:start_index + 4]

    category = random.choice(list(PRODUCT_DATA.keys()))

    category_data = PRODUCT_DATA[category]

    name = random.choice(category_data["names"])
    fit = random.choice(category_data["fits"])
    material = random.choice(category_data["materials"])
    color = random.choice(COLORS)

    min_price, max_price = category_data["price_range"]

    price = random.randrange(min_price, max_price + 1, 100)

    product = {
        "product_id": f"PROD-{product_number + 1:03d}",
        "name": name,
        "category": category,
        "description": (
            f"A {fit.lower()} fit {color.lower()} {name.lower()} "
            f"made from {material.lower()}. "
            f"Designed for everyday comfort and casual wear."
        ),
        "price": price,
        "currency": "INR",
        "color": color,
        "fit": fit,
        "material": material,
        "sizes": SIZES,
        "images": [image.name for image in product_images],
    }

    products.append(product)


# --------------------------------------------------
# 6. Save products as JSON
# --------------------------------------------------

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    json.dump(products, file, indent=4, ensure_ascii=False)


# --------------------------------------------------
# 7. Print result
# --------------------------------------------------

print("=" * 50)
print("PRODUCT GENERATION COMPLETE")
print("=" * 50)

print(f"Images used: {len(image_files)}")
print(f"Products created: {len(products)}")
print(f"Images per product: 4")
print(f"Output file: {OUTPUT_PATH}")

print("=" * 50)