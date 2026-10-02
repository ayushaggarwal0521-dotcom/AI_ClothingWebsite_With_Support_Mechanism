from app.services.order_service import get_customer_order_statuses


result = get_customer_order_statuses("CUST-001")

print(result)