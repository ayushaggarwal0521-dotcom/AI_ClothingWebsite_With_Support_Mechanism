import json
import os
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from app.database import get_connection
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ALLOWED_PRIORITIES = {"HIGH", "MEDIUM", "LOW"}

def determine_priority(message: str):

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": """
You are a customer support priority classifier for an online clothing store.

Classify the customer's message into exactly one of these priorities:

HIGH
MEDIUM
LOW

HIGH:
- Financial problems
- Serious problems
- Explicitly urgent issues
- Issues with significant customer impact

MEDIUM:
- Order problems
- Delivery problems
- Return or exchange problems
- Normal customer complaints that are not explicitly urgent

LOW:
- General questions
- Product information requests
- Size or availability questions
- Other non-urgent requests

Important:
- Understand the meaning of the entire message.
- Pay attention to negation.
- For example, "I don't need it urgently" should NOT be classified as HIGH merely because the word "urgently" appears.
- Return only valid JSON.

JSON format:
{
    "priority": "HIGH",
    "reason": "short explanation"
}
"""
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )

    result = json.loads(response.output_text)

    priority = result.get("priority")
    reason = result.get("reason")

    if priority not in ALLOWED_PRIORITIES:
        raise ValueError(f"Invalid priority returned by AI: {priority}")

    return {
        "priority": priority,
        "reason": reason
    }



def customer_exists(customer_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM customers
        WHERE customer_id = %s
    """, (customer_id,))

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    return row is not None



def order_belongs_to_customer(order_id: str, customer_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM orders
        WHERE order_id = %s
          AND customer_id = %s
    """, (order_id, customer_id))

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    return row is not None



def create_support_ticket(
    customer_id: str,
    actual_message: str,
    order_id: str | None = None
):
    # Step 1: Validate customer
    if not customer_exists(customer_id):
        return {
            "success": False,
            "message": f"Customer {customer_id} does not exist."
        }

    # Step 2: Validate order belongs to customer
    if order_id is not None:
        if not order_belongs_to_customer(order_id, customer_id):
            return {
                "success": False,
                "message": f"Order {order_id} is not associated with customer {customer_id}."
            }

    # Step 3: Determine priority using AI
    priority_result = determine_priority(actual_message)

    priority = priority_result["priority"]
    priority_reason = priority_result["reason"]

    # Step 4: Generate support ticket ID
    support_ticket_id = "TKT-" + str(uuid.uuid4())[:8]

    # Step 5: Insert ticket into database
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO support_tickets (
                support_ticket_id,
                customer_id,
                order_id,
                actual_message,
                ticket_status,
                priority
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            support_ticket_id,
            customer_id,
            order_id,
            actual_message,
            "OPEN",
            priority
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

    return {
        "success": True,
        "support_ticket_id": support_ticket_id,
        "customer_id": customer_id,
        "order_id": order_id,
        "actual_message": actual_message,
        "ticket_status": "OPEN",
        "priority": priority,
        "priority_reason": priority_reason
    }