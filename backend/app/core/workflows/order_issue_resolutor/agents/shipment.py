from langchain.agents import create_agent
from langchain_core.tools import tool

from app.core.llm.service import llm
from app.core.tools.ecommerce import get_shipment_status,get_tracking_events

shipment_agent = create_agent(
    model=llm,
    tools=[
        get_shipment_status,
        get_tracking_events,
    ],
    system_prompt="""
You are the Shipment Specialist.

Your responsibility is to investigate shipment and delivery status.

You can:
- retrieve shipment status
- retrieve tracking events
- determine the current delivery state

Do not retrieve customer information.
Do not interpret company policy.

Return a concise factual result.
""",
)





@tool
def shipment_agent_tool(request: str) -> str:
    """
    Delegate a shipment investigation to the Shipment Specialist.
    """

    result = shipment_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": request,
            }
        ]
    })

    return result["messages"][-1].content