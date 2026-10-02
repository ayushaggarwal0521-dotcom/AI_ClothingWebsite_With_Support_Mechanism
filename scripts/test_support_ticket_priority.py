from app.services.support_ticket_service import determine_priority


test_messages = [
    "My payment was deducted but my order was not created.",
    "My package is delayed by 2 days and I need it urgently.",
    "My package is delayed by 2 days, but I don't need it urgently.",
    "I received the wrong size and want to return it.",
    "Can you tell me the size chart for this product?",
    "I want to know whether this shirt is available in blue."
]


for message in test_messages:
    priority = determine_priority(message)

    print(f"Message: {message}")
    print(f"Priority: {priority}")
    print("-" * 60)