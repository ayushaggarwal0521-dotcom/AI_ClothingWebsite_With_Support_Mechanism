from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.storefront import router as storefront_router
from app.database import get_connection
from app.services.return_service import create_return
from pydantic import BaseModel
from app.services.order_service import get_order_status
from app.services.order_service import get_customer_order_statuses
from app.services.order_service import get_order_items
from app.services.refund_service import get_refund_status
from app.services.support_ticket_service import create_support_ticket
import uuid
from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    send_customer_message,
    send_assistant_message
)
from app.services.orchestrator import (
    get_mcp_tools,
    convert_mcp_tools_to_llm_tools,
    create_ask_customer_tool,
    process_message
)


app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(storefront_router)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/images", StaticFiles(directory=BASE_DIR / "dataset" / "raw"), name="images")



class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

class SupportTicketRequest(BaseModel):
    customer_id: str
    order_id: str | None = None
    actual_message: str

class ReturnRequest(BaseModel):
    order_id: str
    order_item_id: str
    return_quantity: int
    return_reason: str = ""


@app.get("/")
# This is a route decorator.
# When someone sends a GET request to /, use the function immediately below this decorator
def home():
    return {
        "message": "AI Clothing Store API is running"
    }



@app.get("/products")
def get_products():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            product_id,
            name,
            category,
            price
        FROM products
        ORDER BY product_id
    """)

    products = cursor.fetchall()
    # .fetchall() - brings those database rows into Python.

    cursor.close()
    connection.close()

    result = []

    for product in products:
        result.append({
            "product_id": product[0],
            "name": product[1],
            "category": product[2],
            "price": float(product[3]),
        })

    return result



@app.get("/products/{product_id}")
def get_product(product_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            product_id,
            name,
            category,
            price
        FROM products
        WHERE product_id = %s
    """, (product_id,))

    product = cursor.fetchone()

    cursor.close()
    connection.close()

    if product is None:
        return {
            "error": "Product not found"
        }

    return {
        "product_id": product[0],
        "name": product[1],
        "category": product[2],
        "price": float(product[3])
    }



@app.get("/customers/{customer_id}/orders")
def get_customer_orders(customer_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            order_id,
            order_date,
            status,
            total_amount
        FROM orders
        WHERE customer_id = %s
        ORDER BY order_date DESC
    """, (customer_id,))

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    result = []

    for order in orders:
        result.append({
            "order_id": order[0],
            "order_date": order[1],
            "status": order[2],
            "total_amount": float(order[3])
        })

    return result




@app.get("/orders/{order_id}")
def get_order(order_id: str):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            o.order_id,
            o.order_date,
            o.status,
            o.total_amount,
            oi.order_item_id,
            p.product_id,
            p.name,
            p.category,
            oi.quantity,
            oi.unit_price
        FROM orders o
        LEFT JOIN order_items oi
            ON o.order_id = oi.order_id
        LEFT JOIN products p
            ON oi.product_id = p.product_id
        WHERE o.order_id = %s
    """, (order_id,))

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    if not rows:
        return {
            "error": "Order not found"
        }

    first_row = rows[0]

    result = {
        "order_id": first_row[0],
        "order_date": first_row[1],
        "status": first_row[2],
        "total_amount": float(first_row[3]),
        "items": []
    }

    for row in rows:
        result["items"].append({
            "order_item_id": row[4],
            "product_id": row[5],
            "name": row[6],
            "category": row[7],
            "quantity": row[8],
            "unit_price": float(row[9])
        })

    return result




@app.post("/returns")
def create_return_request(request: ReturnRequest):

    result = create_return(
        request.order_id,
        request.order_item_id,
        request.return_quantity,
        request.return_reason
    )

    return result



@app.get("/orders/{order_id}/status")
def order_status(order_id: str):

    result = get_order_status(order_id)

    return result




@app.get("/customers/{customer_id}/orders/status")
def customer_order_statuses(customer_id: str):

    result = get_customer_order_statuses(customer_id)

    return result



@app.get("/orders/{order_id}/items")
def order_items(order_id: str):

    result = get_order_items(order_id)

    return result


@app.get("/returns/{return_id}/refund")
def refund_status(return_id: str):

    result = get_refund_status(return_id)

    return result



@app.post("/support-tickets")
def create_support_ticket_endpoint(request: SupportTicketRequest):

    result = create_support_ticket(
        customer_id=request.customer_id,
        order_id=request.order_id,
        actual_message=request.actual_message
    )

    return result


@app.post("/chat")
async def chat(request: ChatRequest):

    if request.conversation_id is None:

        conversation = create_conversation()

        customer_message = send_customer_message(
            conversation["conversation_id"],
            request.message
        )

        if not customer_message["success"]:
            return customer_message

    else:

        conversation = get_conversation(
            request.conversation_id
        )

        if conversation is None:
            return {
                "success": False,
                "message": "Conversation not found."
            }

        customer_message = send_customer_message(
            request.conversation_id,
            request.message
        )

        if not customer_message["success"]:
            return customer_message


    mcp_tools = await get_mcp_tools()

    llm_tools = convert_mcp_tools_to_llm_tools(mcp_tools)

    llm_tools.append(create_ask_customer_tool())

    ai_result = await process_message(
        conversation["llm_conversation_id"],
        request.message,
        llm_tools
    )

    if ai_result["type"] == "FINAL_RESPONSE":
        assistant_message = send_assistant_message(
            conversation["conversation_id"],
            ai_result["response"]
        )

    elif ai_result["type"] == "ASK_CUSTOMER":
        assistant_message = send_assistant_message(
            conversation["conversation_id"],
            ai_result["question"]
        )

    else:
        assistant_message = None

    return {
        "success": True,
        "conversation_id": conversation["conversation_id"],
        "customer_message_id": customer_message["message_id"],
        "assistant_message_id": (
            assistant_message["message_id"]
            if assistant_message
            else None
        ),
        "ai_result": ai_result
    }


# Storefront UI -> http://localhost:8000/store/
app.mount("/store", StaticFiles(directory=BASE_DIR / "frontend", html=True), name="store")
