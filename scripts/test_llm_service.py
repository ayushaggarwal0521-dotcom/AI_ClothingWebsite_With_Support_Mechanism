from app.services.llm_service import (
    create_llm_conversation,
    send_message_to_llm
)


llm_conversation_id = create_llm_conversation()

print("LLM Conversation ID:")
print(llm_conversation_id)


first_response = send_message_to_llm(
    llm_conversation_id,
    "My name is Ayush and I am building an AI clothing store."
)

print("\nFirst response:")
print(first_response["response"])


second_response = send_message_to_llm(
    llm_conversation_id,
    "What am I building?"
)

print("\nSecond response:")
print(second_response["response"])