from mcp.server import MCPServer
from typing import Optional


mcp = MCPServer("clothing_store")

import sys
from pathlib import Path

# project root (parent of mcp_server/) so "app.services" can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.product_service import (
    search_products as search_products_service,
    get_product_details as get_product_details_service
)
from app.services.order_service import (
    get_order_status as get_order_status_service,
    get_order_items as get_order_items_service,
    cancel_order as cancel_order_service,
    check_cancellation_eligibility as check_cancellation_eligibility_service
)

from app.services.return_service import (
    check_return_eligibility as check_return_eligibility_service,
    create_return as create_return_service,
    get_return_status as get_return_status_service
)
from app.services.refund_service import (
    get_refund_status as get_refund_status_service
)

@mcp.tool()
def search_products(
    category: Optional[str] = None,
    color: Optional[str] = None,
    gender: Optional[str] = None,
    material: Optional[str] = None,
    fit: Optional[str] = None,
    max_price: Optional[float] = None,
    size: Optional[str] = None
):
    
    """ 
    Search clothing products using optional filters such as
    category, color, gender, material, fit, maximum price, and size.
    Use this tool when the customer is looking for products.

    """
    return search_products_service(
        category=category,
        color=color,
        gender=gender,
        material=material,
        fit=fit,
        max_price=max_price,
        size=size
    )


@mcp.tool()
def get_product_details(product_id: str):
    """
    Get the details of a specific clothing product using its product ID.
    Use this tool when the customer asks for information about a specific product.
    """
    return get_product_details_service(product_id)

@mcp.tool()
def get_order_status(order_id: str):
    """
    Get the current status and delivery information for an order.
    Use this tool when the customer asks about the status or delivery of an order.
    """
    return get_order_status_service(order_id)

@mcp.tool()
def get_order_items(order_id: str):
    """
    Get the products and quantities included in an order.
    Use this tool when the customer asks what items are in an order.
    """
    return get_order_items_service(order_id)

@mcp.tool()
def check_cancellation_eligibility(order_id: str):
    """
    Check whether an order can still be cancelled. This is read-only and
    does NOT cancel anything. Use it first when the customer asks to cancel.
    """
    return check_cancellation_eligibility_service(order_id)

@mcp.tool()
def cancel_order(order_id: str):
    """
    Cancel an order. This is a real action. Only call it after the order is
    confirmed eligible AND the customer has explicitly confirmed they want
    to cancel it.
    """
    return cancel_order_service(order_id)

@mcp.tool()
def check_return_eligibility(
    order_id: str,
    order_item_id: str,
    return_quantity: int
):
    """
    Check whether a specific quantity of an order item is eligible for return.
    """
    return check_return_eligibility_service(
        order_id,
        order_item_id,
        return_quantity
    )


@mcp.tool()
def create_return(
    order_id: str,
    order_item_id: str,
    return_quantity: int,
    return_reason: str
):
    """
    Create a return request for an eligible order item.
    """
    return create_return_service(
        order_id,
        order_item_id,
        return_quantity,
        return_reason
    )
@mcp.tool()
def get_return_status(return_id: str):
    """
    Get the current status and details of a return request.
    Use this tool when the customer asks about the status of their return.
    """
    return get_return_status_service(return_id)

@mcp.tool()
def get_refund_status(return_id: str):
    """
    Get the refund status and details for a return request.
    Use this tool when the customer asks about their refund.
    """
    return get_refund_status_service(return_id)



if __name__ == "__main__":
    mcp.run()