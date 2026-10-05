from typing import Dict, Any, List
# Import the official LangChain tool decorator
from langchain_core.tools import tool

# ==========================================
# 1. HARDCODED STATIC DATASET (Source of Truth)
# ==========================================

# Customer database
MOCK_CUSTOMER_DB = {
    "CUST-101": {
        "customer_id": "CUST-101",
        "customer_name": "Aarav Sharma",
        "membership": "Gold",
        "previous_support_cases": [
            {"case_id": "CASE-901", "subject": "Wrong Item Size", "status": "Closed"}
        ],
        "account_status": "Active"
    },
    "CUST-202": {
        "customer_id": "CUST-202",
        "customer_name": "Ananya Iyer",
        "membership": "Platinum",
        "previous_support_cases": [],
        "account_status": "Active"
    },
    "CUST-303": {
        "customer_id": "CUST-303",
        "customer_name": "Rohan Verma",
        "membership": "Silver",
        "previous_support_cases": [
            {"case_id": "CASE-402", "subject": "Promo Code Not Working", "status": "Resolved"},
            {"case_id": "CASE-511", "subject": "Refund Status", "status": "Closed"}
        ],
        "account_status": "Flagged"
    }
}

# Order database (Linked to Customer IDs)
MOCK_ORDER_DB = {
    "ORD-8821": {
        "order_id": "ORD-8821",
        "customer_id": "CUST-101",
        "product": "AuraGlow Face Serum",
        "order_date": "01 Oct 2026",
        "delivery_date": "05 Oct 2026",
        "order_status": "Shipped"
    },
    "ORD-4492": {
        "order_id": "ORD-4492",
        "customer_id": "CUST-202",
        "product": "ZenFit Smart Band",
        "order_date": "03 Oct 2026",
        "delivery_date": "07 Oct 2026",
        "order_status": "Processing"
    },
    "ORD-1104": {
        "order_id": "ORD-1104",
        "customer_id": "CUST-303",
        "product": "EcoThread Cotton Hoodie",
        "order_date": "25 Sep 2026",
        "delivery_date": "29 Sep 2026",
        "order_status": "Delivered"
    }
}

# Shipment tracking database (Linked to Order IDs)
MOCK_SHIPMENT_DB = {
    "ORD-8821": {
        "order_id": "ORD-8821",
        "status": "In Transit",
        "current_location": "Hyderabad Hub",
        "expected_delivery": "05 Oct 2026"
    },
    "ORD-4492": {
        "order_id": "ORD-4492",
        "status": "At Sorting Facility",
        "current_location": "Mumbai Sort Facility",
        "expected_delivery": "07 Oct 2026"
    },
    "ORD-1104": {
        "order_id": "ORD-1104",
        "status": "Delivered",
        "current_location": "Delhi Distribution Center",
        "expected_delivery": "29 Sep 2026"
    }
}



@tool
def get_order_details(order_id: str) -> dict:
    """Retrieves the complete order breakdown, items, dates, and current fulfillment status for a given order ID.

    Args:
        order_id: The unique alphanumeric identifier of the customer's order (e.g., 'ORD-8821').
    """
    # Returns the exact database record or a clean error message if the LLM hallucinated an ID
    return MOCK_ORDER_DB.get(
        order_id, 
        {"error": f"Order ID '{order_id}' not found in the database."}
    )


@tool
def get_shipment_status(order_id: str) -> dict:
    """Fetches real-time tracking logs, current physical location, and estimated delivery dates from the logistics partner for a specific order.

    Args:
        order_id: The unique alphanumeric identifier of the order being tracked (e.g., 'ORD-8821').
    """
    return MOCK_SHIPMENT_DB.get(
        order_id, 
        {"error": f"No shipment tracking tracking data found for Order ID '{order_id}'."}
    )


@tool
def get_customer_profile(customer_id: str) -> dict:
    """Retrieves user CRM profile data, loyalty membership tier, account validity status, and historical customer support interactions.

    Args:
        customer_id: The unique identifier of the customer (e.g., 'CUST-101').
    """
    return MOCK_CUSTOMER_DB.get(
        customer_id, 
        {"error": f"Customer Profile for ID '{customer_id}' not found."}
    )

