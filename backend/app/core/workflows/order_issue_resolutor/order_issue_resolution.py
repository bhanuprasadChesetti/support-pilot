import logging
from typing import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph,START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm.factory import LLMFactory
from app.core.tools.ecommerce import get_order_details,get_shipment_status
from app.core.tools.rag import create_search_knowledge_tool

logger = logging.getLogger(__name__)


class SupportState(TypedDict):
    user_query: str

    order_id: str | None
    customer_id: str | None
    issue_type: str | None

    order: dict | None
    shipment: dict | None

    policy_context: str | None

    resolution: dict | None

    final_response: str | None



class RequestAnalyzerOutput(TypedDict):
    order_id: str
    issue_type: str

request_analyzer_llm = LLMFactory.get_model().with_structured_output(RequestAnalyzerOutput)

search_knowledge_tool = create_search_knowledge_tool(top_k=2)

def request_analyzer(state: SupportState) -> dict:
    """Extracts order_id and issue_type from the user's initial query."""
    logger.debug(f"Analyzing request: {state['user_query']}")
    extracted_data = request_analyzer_llm.invoke(state["user_query"])
    return {
        "order_id": extracted_data["order_id"],
        "issue_type": extracted_data["issue_type"]
    }


def order_investigator(state: SupportState) -> dict:
    """Fetches order and shipment data using the extracted order_id."""
    logger.debug(f"Investigating order: {state['order_id']}")
    
    order_id = state["order_id"]
    order_data = get_order_details.invoke(order_id)
    shipment_data = get_shipment_status.invoke(order_id)

    logger.debug(f"Order data: {order_data}")
    logger.debug(f"Shipment data: {shipment_data}")

    return {
        "order": order_data,
        "shipment": shipment_data
    }



async def policy_retriever(state: SupportState) -> dict:
    """Retrieves relevant company policies based on the extracted issue_type."""
    logger.debug(f"Retrieving policy for issue type: {state['issue_type']}")
    issue_type = state["issue_type"]
    
    query = f"{issue_type} {str(state["user_query"])}"
    policy_content = await search_knowledge_tool.ainvoke(query)

    return {
        "policy_context": policy_content
    }





class Resolution(BaseModel):
    decision: str = Field(
        description="The recommended resolution for the customer."
    )
    reason: str = Field(
        description="Why this resolution is appropriate based on the order, shipment, and policy."
    )
    actions: list[str] = Field(
        description="Actions that should be taken to resolve the issue."
    )



resolution_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a SupportPilot resolution analyst.

Determine the appropriate resolution for the customer's request using ONLY:
1. Customer request
2. Order information
3. Shipment information
4. Retrieved company policy

Do not invent facts or policy rules.

If the available information is insufficient to make a decision,
clearly state what information is missing."""
    ),
    (
        "human",
        """Customer Request:
{user_query}

Order Information:
{order}

Shipment Information:
{shipment}

Relevant Policy:
{policy_context}

Determine the appropriate resolution."""
    ),
])

resolution_analyzer_llm = LLMFactory.get_model().with_structured_output(Resolution)

resolution_analyzer_chain = resolution_prompt | resolution_analyzer_llm

def resolution_analyzer(state: SupportState) -> dict:

    logger.debug(f"Analyzing resolution for query")
    result = resolution_analyzer_chain.invoke({
        "user_query": state["user_query"],
        "order": state["order"],
        "shipment": state["shipment"],
        "policy_context": state["policy_context"],
    })

    return {
        "resolution": result.model_dump()
    }



def response_generator(state: SupportState) -> dict:
    """Generates the final natural language response for the customer using the LLM."""

    logger.debug(f"Generating response for query")

    user_query = state["user_query"]
    resolution = state["resolution"]
    
    prompt = (
        "You are an empathetic and professional customer support assistant. "
        "Write a clear, polite, and helpful final response to the customer based on their query and our internal resolution.\n\n"
        f"Customer's Original Query:\n\"{user_query}\"\n\n"
        f"Internal Resolution Details:\n{resolution}\n\n"
        "Draft the final response to the customer now:"
    )
    
    llm = LLMFactory.get_model()
    response = llm.invoke(prompt)
    
    final_text = response.content if hasattr(response, 'content') else str(response)
    
    return {
        "final_response": final_text
    }



def ask_for_order_id(state: SupportState) -> dict:
    """Executed if no order_id was found in the user query."""
    logger.info('Missing Order id asking for Order ID')
    return {
        "final_response": "I see you are having an issue, but I couldn't find your order number. Could you please provide your Order ID?"
    }


def route_after_analysis(state: SupportState) -> str:
    """Checks if order_id exists and routes accordingly."""
    if state.get("order_id"):
        return "order_investigator"  # Go to regular flow
    return "ask_for_order_id"        # Divert to fallback flow



wf = StateGraph(SupportState)

# Add all functional nodes to the graph
wf.add_node("request_analyzer", request_analyzer)
wf.add_node("order_investigator", order_investigator)
wf.add_node("policy_retriever", policy_retriever)
wf.add_node("resolution_analyzer", resolution_analyzer)
wf.add_node("response_generator", response_generator)
wf.add_node("ask_for_order_id", ask_for_order_id)

# Define the sequential edge control flow
wf.add_edge(START, "request_analyzer")
wf.add_conditional_edges(
    "request_analyzer",
    route_after_analysis,
    {
        "order_investigator": "order_investigator",
        "ask_for_order_id": "ask_for_order_id"
    }
)

wf.add_edge("ask_for_order_id", END)
wf.add_edge("request_analyzer", "order_investigator")
wf.add_edge("order_investigator", "policy_retriever")
wf.add_edge("policy_retriever", "resolution_analyzer")
wf.add_edge("resolution_analyzer", "response_generator")
wf.add_edge("response_generator", END)


order_issue_resolutor = wf.compile()
