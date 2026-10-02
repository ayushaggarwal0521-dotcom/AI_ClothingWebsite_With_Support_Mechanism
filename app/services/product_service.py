from app.database import get_connection


def _run_product_query(
    category=None,
    color=None,
    gender=None,
    material=None,
    fit=None,
    max_price=None,
    size=None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT DISTINCT
            p.product_id,
            p.name,
            p.category,
            p.price,
            p.color,
            p.gender,
            p.material,
            p.fit
        FROM products p
    """

    conditions = []
    parameters = []

    if size is not None:
        query += """
            JOIN product_sizes ps
                ON p.product_id = ps.product_id
        """

        conditions.append("ps.size = %s")
        parameters.append(size)

    if category is not None:
        conditions.append("LOWER(p.category) = LOWER(%s)")
        parameters.append(category)

    if color is not None:
        conditions.append("LOWER(p.color) = LOWER(%s)")
        parameters.append(color)

    if gender is not None:
        conditions.append("LOWER(p.gender) = LOWER(%s)")
        parameters.append(gender)

    if material is not None:
        conditions.append("LOWER(p.material) = LOWER(%s)")
        parameters.append(material)

    if fit is not None:
        conditions.append("LOWER(p.fit) = LOWER(%s)")
        parameters.append(fit)

    if max_price is not None:
        conditions.append("p.price < %s")
        parameters.append(max_price)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += """
        ORDER BY p.product_id;
    """

    cursor.execute(query, parameters)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    products = []

    for row in rows:
        products.append({
            "product_id": row[0],
            "name": row[1],
            "category": row[2],
            "price": float(row[3]),
            "color": row[4],
            "gender": row[5],
            "material": row[6],
            "fit": row[7]
        })

    return products


def search_products(
    category=None,
    color=None,
    gender=None,
    material=None,
    fit=None,
    max_price=None,
    size=None
):
    # Keep the original filters so we can explain
    # what the customer originally requested.
    original_filters = {
        "category": category,
        "color": color,
        "gender": gender,
        "material": material,
        "fit": fit,
        "max_price": max_price,
        "size": size
    }

    # Track every change made during fallback.
    fallback_changes = []

    # --------------------------------------------------
    # STEP 1: Exact search
    # --------------------------------------------------

    products = _run_product_query(
        category=category,
        color=color,
        gender=gender,
        material=material,
        fit=fit,
        max_price=max_price,
        size=size
    )

    if products:
        return {
            "success": True,
            "count": len(products),
            "fallback_used": False,
            "original_filters": original_filters,
            "applied_filters": original_filters,
            "fallback_changes": [],
            "products": products
        }

    # --------------------------------------------------
    # STEP 2: Relax price by 50%
    # --------------------------------------------------

    relaxed_price = max_price

    if max_price is not None:

        relaxed_price = max_price * 1.5

        products = _run_product_query(
            category=category,
            color=color,
            gender=gender,
            material=material,
            fit=fit,
            max_price=relaxed_price,
            size=size
        )

        if products:
            fallback_changes.append(
                f"price increased from {max_price} to {relaxed_price}"
            )

            applied_filters = {
                "category": category,
                "color": color,
                "gender": gender,
                "material": material,
                "fit": fit,
                "max_price": relaxed_price,
                "size": size
            }

            return {
                "success": True,
                "count": len(products),
                "fallback_used": True,
                "original_filters": original_filters,
                "applied_filters": applied_filters,
                "fallback_changes": fallback_changes,
                "products": products
            }

    # --------------------------------------------------
    # STEP 3: Relax fit
    # --------------------------------------------------

    if fit is not None:

        products = _run_product_query(
            category=category,
            color=color,
            gender=gender,
            material=material,
            fit=None,
            max_price=relaxed_price,
            size=size
        )

        if products:
            fallback_changes.append("fit filter was relaxed")

            applied_filters = {
                "category": category,
                "color": color,
                "gender": gender,
                "material": material,
                "fit": None,
                "max_price": relaxed_price,
                "size": size
            }

            return {
                "success": True,
                "count": len(products),
                "fallback_used": True,
                "original_filters": original_filters,
                "applied_filters": applied_filters,
                "fallback_changes": fallback_changes,
                "products": products
            }

    # --------------------------------------------------
    # STEP 4: Relax color
    # --------------------------------------------------

    if color is not None:

        products = _run_product_query(
            category=category,
            color=None,
            gender=gender,
            material=material,
            fit=None if fit is not None else fit,
            max_price=relaxed_price,
            size=size
        )

        if products:
            fallback_changes.append("color filter was relaxed")

            applied_filters = {
                "category": category,
                "color": None,
                "gender": gender,
                "material": material,
                "fit": None if fit is not None else fit,
                "max_price": relaxed_price,
                "size": size
            }

            return {
                "success": True,
                "count": len(products),
                "fallback_used": True,
                "original_filters": original_filters,
                "applied_filters": applied_filters,
                "fallback_changes": fallback_changes,
                "products": products
            }

    # --------------------------------------------------
    # STEP 5: Nothing found
    # --------------------------------------------------

    return {
        "success": True,
        "count": 0,
        "fallback_used": True,
        "original_filters": original_filters,
        "applied_filters": None,
        "fallback_changes": fallback_changes,
        "fallback_reason": "No matching or reasonable alternative products found.",
        "products": []
    }




def get_product_details(product_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            p.product_id,
            p.name,
            p.category,
            p.price,
            p.color,
            p.gender,
            p.material,
            p.fit,
            ps.size
        FROM products p
        JOIN product_sizes ps
            ON p.product_id = ps.product_id
        WHERE p.product_id = %s
        ORDER BY ps.size;
    """, (product_id,))

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    if not rows:
        return {
            "success": False,
            "reason": "Product not found."
        }

    sizes = []

    for row in rows:
        sizes.append(row[8])

    product = {
        "product_id": rows[0][0],
        "name": rows[0][1],
        "category": rows[0][2],
        "price": float(rows[0][3]),
        "color": rows[0][4],
        "gender": rows[0][5],
        "material": rows[0][6],
        "fit": rows[0][7],
        "sizes": sizes
    }

    return {
        "success": True,
        "product": product
    }

