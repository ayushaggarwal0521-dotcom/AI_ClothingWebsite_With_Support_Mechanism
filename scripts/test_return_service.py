from app.services.return_service import create_return

result = create_return(
    "ORD-012",
    "ITEM-031",
    1,
    "Trying to return it again"
)

print(result)