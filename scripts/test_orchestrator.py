from app.services.orchestrator import process_customer_message


customer_id = "CUST-016"


first_result = process_customer_message(
    customer_id,
    "My name is Ayush and I am building an AI clothing store."
)

print("\nFirst result:")
print(first_result)


second_result = process_customer_message(
    customer_id,
    "What am I building?"
)

print("\nSecond result:")
print(second_result)