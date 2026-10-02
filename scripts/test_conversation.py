from app.services.conversation_service import (
    create_conversation,
    send_customer_message
)


conversation = create_conversation()

conversation_id = conversation["conversation_id"]

print("\nConversation created:")
print(conversation)


for i in range(1, 22):

    result = send_customer_message(
        conversation_id,
        f"Test message number {i}"
    )

    print(f"\n--- Message {i} ---")
    print("Status:", result.get("status"))
    print("Message count:", result.get("customer_message_count"))
    print("Limit reached:", result.get("message_limit_reached"))
    print("Success:", result.get("success"))

    if result.get("error"):
        print("Error:", result.get("error"))