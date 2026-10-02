from openai import OpenAI
from dotenv import load_dotenv
import os


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# Create a new OpenAI conversation
conversation = client.conversations.create()

print("Conversation ID:")
print(conversation.id)


# First message
response = client.responses.create(
    model="gpt-5.6-luna",
    conversation=conversation.id,
    input="My name is Ayush and I am building an AI clothing store."
)

print("\nFirst response:")
print(response.output_text)


# Second message using the SAME conversation
response = client.responses.create(
    model="gpt-5.6-luna",
    conversation=conversation.id,
    input="What am I building?"
)

print("\nSecond response:")
print(response.output_text)