from anthropic.types.beta import beta_request_mcp_server_tool_configuration_param
import logging
from typing import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph,START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm.factory import LLMFactory
from app.core.tools.ecommerce import get_order_details,get_shipment_status,get_customer_profile
from app.core.tools.rag import create_search_knowledge_tool

logger = logging.getLogger(__name__)

from typing import TypedDict, List, Optional, Literal


class SupportState(TypedDict):
    user_query: str
    order_id: Optional[str]
    customer_id: Optional[str]
    issue_type: Optional[str]
    
    # The router will populate this list (e.g., ["order_fetch", "policy_fetch"])
    required_fetches: List[Literal["order_fetch", "customer_fetch", "policy_fetch","shipment_fetch"]]

    # Parallel node outputs
    order: Optional[dict]
    shipment: Optional[dict]
    customer: Optional[dict]
    policy_context: Optional[str]

    resolution: Optional[dict]
    final_response: Optional[str]


class RequestAnalyzerOutput(TypedDict):
    order_id: Optional[str]
    customer_id: Optional[str]
    issue_type: Optional[str]
    # The LLM decides what data is missing/needed to solve the issue
    needed_information: List[Literal["order", "customer", "policy", "shipment"]]


request_analyzer_llm = LLMFactory.get_model().with_structured_output(RequestAnalyzerOutput)

search_knowledge_tool = create_search_knowledge_tool(top_k=2)

def request_analyzer(state: SupportState) -> dict:
    """Extracts order_id and issue_type from the user's initial query."""
    logger.info(f"Analyzing request: {state}")


    extracted_data = request_analyzer_llm.invoke(state["user_query"])
    
    mapping = {
        "order": "order_fetch",
        "customer": "customer_fetch",
        "policy": "policy_fetch",
        "shipment": "shipment_fetch"
    }
    required_nodes = [mapping[item] for item in extracted_data["needed_information"] if item in mapping]
    logger.debug(f'Required Nodes to call {required_nodes}')

    return {
        "order_id": extracted_data.get("order_id"),
        "customer_id": extracted_data.get("customer_id"),
        "issue_type": extracted_data.get("issue_type"),
        "required_fetches": required_nodes
    }



def order_fetch(state: SupportState) -> dict:
    """Fetches order data concurrently."""
    logger.debug(f'Fetching order data for Order Id: {state["order_id"]}')
    data = get_order_details.invoke(state["order_id"]) 
    return {"order": data}


def customer_fetch(state: SupportState) -> dict:
    """Fetches customer profile concurrently."""
    logger.debug(f'Fetching customer data for Customer Id: {state["customer_id"]}')
    data = get_customer_profile.invoke(state["customer_id"]) 
    return {"customer": data}


async def policy_fetch(state: SupportState) -> dict:
    """Fetches policy documents concurrently."""
    logger.debug(f'Fetching policy data for issue type: {state["issue_type"]}')
    query = f"{state['issue_type']} {str(state['user_query'])}"
    data = await search_knowledge_tool.ainvoke(query)
    return {"policy_context": data}


def shipment_fetch(state: SupportState) -> dict:
    """Fetches shipment data concurrently."""
    logger.debug(f'Fetching shipment data for Order Id: {state["order_id"]}')
    data = get_shipment_status.invoke(state["order_id"])
    return {"shipment": data}



def context_builder(state: SupportState) -> dict:
    """Executes ONLY after all triggered fetch nodes finish.
    
    Compiles or cleans up the gathered state before analysis.
    """
    logger.debug("All parallel fetches complete! Processing context...")
    return {} # State keys are already updated by the parallel nodes



def requirement_router(state: SupportState) -> List[str]:
    """Dynamically returns a list of all nodes that must run in parallel."""
    nodes_to_run = state.get("required_fetches", [])
    
    if not nodes_to_run:
        return ["context_builder"]
        
    return nodes_to_run





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

{required_info}

Determine the appropriate resolution."""
    ),
])

resolution_analyzer_llm = LLMFactory.get_model().with_structured_output(Resolution)

resolution_analyzer_chain = resolution_prompt | resolution_analyzer_llm

def resolution_analyzer(state: SupportState) -> dict:

    logger.debug(f"Analyzing resolution for query")

    required_info = ""

    if state.get("order"):
        required_info += f"Order Information:\n{state['order']}\n"
    
    if state.get("shipment"):
        required_info += f"Shipment Information:\n{state['shipment']}\n"
    
    if state.get("policy_context"):
        required_info += f"Relevant Policy:\n{state['policy_context']}\n"

    if state.get("customer"):
        required_info += f"Customer Profile:\n{state['customer']}\n"


    result = resolution_analyzer_chain.invoke({
        "user_query": state["user_query"],
        "required_info": required_info,
    })

    logger.debug(f"Resolution analyzer result: {result}")

    return {
        "resolution": result.model_dump()
    }



def response_generator(state: SupportState) -> dict:
    """Generates the final natural language response for the customer using the LLM."""

    logger.debug(f"Generating response for query")

    user_query = state["user_query"]
    resolution = state["resolution"]
    
    prompt = (
        "You are an empathetic, concise, and professional live chat support agent. "
        "Write a clear, brief, and helpful real-time chat response to the customer. "
        "Avoid email-style greetings (like 'Hello [Customer Name]') or formal sign-offs. "
        "Ensure it feels like a live chat conversation.\n\n"
        f"Customer's Original Query:\n\"{user_query}\"\n\n"
        f"Internal Resolution Details:\n{resolution}\n\n"
        "Draft the real-time chat reply for the customer now:"
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


wf.add_node("request_analyzer", request_analyzer)
wf.add_node("order_fetch", order_fetch)
wf.add_node("customer_fetch", customer_fetch)
wf.add_node("shipment_fetch", shipment_fetch)
wf.add_node("policy_fetch", policy_fetch)
wf.add_node("context_builder", context_builder)
wf.add_node("resolution_analyzer", resolution_analyzer)
wf.add_node("response_generator", response_generator)



wf.add_edge(START, "request_analyzer")

# The router returns a list. If it returns ["order_fetch", "policy_fetch"], 
# LangGraph spawns both threads concurrently.
wf.add_conditional_edges(
    "request_analyzer",
    requirement_router,
    {
        "order_fetch": "order_fetch",
        "customer_fetch": "customer_fetch",
        "policy_fetch": "policy_fetch",
        "shipment_fetch": "shipment_fetch",
        "context_builder": "context_builder" # Direct fallback edge
    }
)
# Pointing multiple independent nodes to the same target forces LangGraph to wait.
wf.add_edge("order_fetch", "context_builder")
wf.add_edge("customer_fetch", "context_builder")
wf.add_edge("policy_fetch", "context_builder")
wf.add_edge("shipment_fetch", "context_builder")

wf.add_edge("context_builder", "resolution_analyzer")
wf.add_edge("resolution_analyzer", "response_generator")
wf.add_edge("response_generator", END)


order_issue_resolutor = wf.compile()