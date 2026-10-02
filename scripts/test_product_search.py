from app.services.product_service import search_products


result = search_products(
    category="T-Shirts",
    color="White",
    fit="Slim",
    max_price=1000
)


print(result)