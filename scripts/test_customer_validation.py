from app.services.support_ticket_service import create_support_ticket


print("TEST 1: Invalid customer")
result = create_support_ticket(
    customer_id="CUST-999",
    order_id=None,
    actual_message="Can you tell me the size chart?"
)
print(result)
print("-" * 60)


print("TEST 2: Order does not belong to customer")
result = create_support_ticket(
    customer_id="CUST-001",
    order_id="ORD-090",
    actual_message="Where is my order?"
)
print(result)
print("-" * 60)

print("TEST 3: Valid customer without order")
result = create_support_ticket(
    customer_id="CUST-001",
    order_id=None,
    actual_message="Can you tell me the size chart?"
)
print(result)
print("-" * 60)