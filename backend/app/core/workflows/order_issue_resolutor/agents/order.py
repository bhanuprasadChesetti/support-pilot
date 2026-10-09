from langchain.agents import create_agent
from langchain_core.tools import tool



from app.core.llm.service import llm
from app.core.tools.ecommerce import (
    get_order_details,
    get_shipment_status,
)



order_agent = create_agent(
    model=llm,
    tools=[
        get_order_details,
        get_shipment_status,
    ],
    system_prompt="""
You are an Order Specialist.

Your responsibility is to investigate order-related questions.

You can:
- retrieve order details
- retrieve shipment status

Use the available tools when necessary.

Do not answer questions outside your responsibility.

Return a concise factual result based on the information you retrieved.
""",
)






@tool
def order_agent_tool(request: str) -> str:
    """
    Retrieve order information for customer-support resolution.

    Use this tool ONLY to look up facts such as order status,
    payment amount, order items, and cancellation eligibility.

    This tool must never cancel an order, issue a refund,
    or perform any other business-side effect.

    The request must describe the information to retrieve,
    not an action to execute.
    """

    result = order_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": request,
            }
        ]
    })

    return result["messages"][-1].content