import logging
from typing import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph,START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.messages import SystemMessage, HumanMessage


from app.core.llm.factory import LLMFactory
from app.core.tools.ecommerce import get_order_details,get_shipment_status,get_customer_profile
from app.core.tools.rag import create_search_knowledge_tool

logger = logging.getLogger(__name__)

from typing import TypedDict, List, Optional, Literal


llm = LLMFactory.get_model()

class SupportState(TypedDict, total=False):
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

    actions: list[dict]

    action_plan: dict

    # Current action being processed
    current_action_index: int 

    approval_request: dict | None
    approval_decision: dict | None

    execution_results: list[dict]

    workflow_status: str


from typing import Literal, List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class RequestAnalyzerOutput(BaseModel):
    order_id: Optional[str] = Field(default=None, description="The extracted order ID (e.g., ORD-1234) if mentioned.")
    customer_id: Optional[str] = Field(default=None, description="The customer ID if mentioned.")
    issue_type: Optional[str] = Field(default=None, description="The core issue category (e.g. 'damaged product', 'cancellation', 'shipping delay').")
    needed_information: List[Literal["order", "customer", "policy", "shipment"]] = Field(
        description="Select which components need to be fetched to solve this query."
    )

# 2. Setup the parser
parser = PydanticOutputParser(pydantic_object=RequestAnalyzerOutput)

# 3. Build a manual prompt containing the explicit JSON schema and format instructions
request_analyzer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a precise data extraction agent. Analyze the customer query and extract the required information.\n\n"
        "You MUST output your response as a valid **JSON** object conforming strictly to this schema:\n"
        "```json\n{schema}\n```\n\n"
        "{format_instructions}"
    ),
    ("human", "{user_query}")
])

request_analyzer_llm = llm.with_structured_output(RequestAnalyzerOutput)

search_knowledge_tool = create_search_knowledge_tool(top_k=2)

def request_analyzer(state: SupportState) -> dict:
    """Extracts order_id and issue_type from the user's initial query."""
    logger.info(f"Analyzing request: {state}")


    extracted_data = request_analyzer_llm.invoke(state["user_query"])

    extracted_data = extracted_data.model_dump()
    
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





class ResolutionAnalysis(BaseModel):
    resolution: str = Field(
        description="Clear description of how the customer's issue should be resolved."
    )

    reason: str = Field(
        description="Reason explaining why this resolution is appropriate based on the available context."
    )

    action_required: bool = Field(
        description="Whether executing one or more business actions is required to resolve the issue."
    )

    action_summary: list[str] = Field(
        default_factory=list,
        description=(
            "High-level actions hints that may be required for action planner agent"
            "Do not provide tool names, arguments, or execution order."
        )
    )




resolution_analyzer_llm = llm.with_structured_output(ResolutionAnalysis)




def resolution_analyzer(state: SupportState):

    logger.debug("Analyzing the customer query for resolution...")

    required_info = ""

    if state.get("order"):
        required_info += f"Order Information:\n{state['order']}\n"
    
    if state.get("shipment"):
        required_info += f"Shipment Information:\n{state['shipment']}\n"
    
    if state.get("policy_context"):
        required_info += f"Relevant Policy:\n{state['policy_context']}\n"

    if state.get("customer"):
        required_info += f"Customer Profile:\n{state['customer']}\n"


    messages = [
        SystemMessage(
            content="""
You are a customer-support resolution analyzer.

Your job is to analyze the customer's request and all available
information collected by the workflow.

Determine:

1. What is the correct resolution for the customer's issue?
2. Why is this resolution appropriate?
3. Whether any business action must be performed to achieve the resolution.
4. If actions are required, describe them at a high level.

Important rules:

- Base your decision only on the provided information.
- Do not invent missing information.
- Do not execute any tools.
- Do not decide detailed tool execution order.
- Do not provide tool arguments.
- Do not provide tool names.
- If the issue can be resolved simply by providing information,
  action_required should be false.
- If a business-side effect is required, action_required should be true.
"""
        ),
        HumanMessage(
            content=f"""
Customer request:
{state["user_query"]}

Requirements identified:
{required_info}
"""
        ),
    ]

    result = resolution_analyzer_llm.invoke(messages)


    return {
        "resolution": result.model_dump()
    }






class ApprovalRequest(BaseModel):
    action_id: str
    action: str
    arguments: dict = Field(default_factory=dict)
    reason: str
    approval_type: str

    
class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    approver_id: str
    reason: str | None = None


from langgraph.types import interrupt
from .actions.metadata import ACTION_DEFINITIONS

def approval_gate(state: SupportState):
    action_plan = state["action_plan"]

    for action in action_plan["actions"]:
        action_name = action["action"]

        action_definition = next(
            (
                definition
                for definition in ACTION_DEFINITIONS
                if definition.name == action_name
            ),
            None,
        )

        if action_definition is None:
            raise ValueError(
                f"Unknown action definition: {action_name}"
            )

        if not action_definition.requires_approval:
            continue

        approval_request = ApprovalRequest(
            action_id=action["id"],
            action=action_name,
            arguments=action.get("arguments", {}),
            reason=action["reason"],
            approval_type=action_definition.approval_type,
        )

        decision = interrupt(
            approval_request.model_dump()
        )

        approval_decision = ApprovalDecision.model_validate(decision)

        if approval_decision.decision == "rejected":
            return {
                "approval_request": approval_request.model_dump(),
                "approval_decision": approval_decision.model_dump(),
                "workflow_status": "rejected",
            }

        return {
            "approval_request": approval_request.model_dump(),
            "approval_decision": approval_decision.model_dump(),
        }

    return {
        "workflow_status": "approved",
    }




from pydantic import BaseModel, Field


class PlannedAction(BaseModel):
    id: str = Field(
        description="Unique identifier for this action within the plan."
    )

    action: str = Field(
        description="Name of the action to execute."
    )

    arguments: dict = Field(
        default_factory=dict,
        description="Arguments required by the action's tool."
    )

    reason: str = Field(
        description="Why this action is needed for the resolution."
    )


class ActionPlan(BaseModel):
    actions: list[PlannedAction] = Field(
        description="Ordered list of actions required to achieve the resolution."
    )

action_planner_llm = llm.with_structured_output(ActionPlan)

from .actions.metadata import action_catalog

def get_action_definition(action_name: str):
    action_definition = next(
        (
            definition
            for definition in ACTION_DEFINITIONS
            if definition.name == action_name
        ),
        None,
    )

    if action_definition is None:
        raise ValueError(
            f"Unknown action: {action_name}"
        )

    return action_definition

def action_planner(state: SupportState):

    logger.debug(f"Creating action plan with resolution: {state.get('resolution')}")

    messages = [
        SystemMessage(
            content=f"""
You are an action planning agent.

Your job is to create an ordered action plan that achieves
the resolution determined by the resolution analyzer.

You have access to the following action definitions:

{action_catalog}

Rules:

1. Only use actions from the provided action definitions.
2. Do not invent actions.
3. Use the provided context to determine tool arguments.
4. Do not execute any tools.
5. Create only the actions necessary to achieve the resolution.
6. The actions list must represent the proposed execution order.
7. Respect the requirements and outputs of actions when determining
   the logical order.
8. If an action requires information produced by another action,
   place the producing action first.
9. Do not add unnecessary actions.
"""
        ),
        HumanMessage(
            content=f"""
Customer request:
{state["user_query"]}

Resolution analysis:
{state["resolution"]}
"""
        ),
    ]

    result = action_planner_llm.invoke(messages)


    action_plan = result.model_dump()

    # Add runtime information AFTER LLM planning
    for action in action_plan["actions"]:

        action_definition = get_action_definition(
            action["action"]
        )

        if action_definition.requires_approval:
            action["approval_status"] = "pending"
        else:
            action["approval_status"] = "not_required"

    return {
        "action_plan": action_plan,
        "current_action_index": 0,
    }


from .actions.metadata import TOOL_REGISTRY
def action_executor(state: SupportState):

    logger.debug(f'executing actions: {state["action_plan"]}')

    action_plan = state["action_plan"]
    current_index = state["current_action_index"]

    actions = action_plan["actions"]

    # All actions completed
    if current_index >= len(actions):
        return {
            "workflow_status": "completed",
        }

    current_action = actions[current_index]

    # -----------------------------------------
    # Approval check
    # -----------------------------------------

    approval_status = current_action["approval_status"]

    if approval_status == "pending":
        return {
            "approval_request": {
                "action_id": current_action["id"],
                "action": current_action["action"],
                "arguments": current_action.get("arguments", {}),
                "reason": current_action["reason"],
                "approval_type": get_action_definition(
                    current_action["action"]
                ).approval_type,
            },
            "workflow_status": "approval_required",
        }

    if approval_status == "rejected":
        return {
            "workflow_status": "approval_rejected",
        }

    # -----------------------------------------
    # not_required OR approved
    # → execute action
    # -----------------------------------------

    action_definition = get_action_definition(
        current_action["action"]
    )

    logger.debug(f'Action running: {action_definition.name}')
    tool = TOOL_REGISTRY.get(action_definition.tool_name)

    if tool is None:
        return {
            "workflow_status": "failed",
            "execution_results": [
                *state.get("execution_results", []),
                {
                    "action_id": current_action["id"],
                    "action": current_action["action"],
                    "status": "failed",
                    "error": (
                        f"Tool not found: "
                        f"{action_definition.tool_name}"
                    ),
                },
            ],
        }


    try:
        result = tool.invoke(
            current_action.get("arguments", {})
        )

        current_action["status"] = "completed"

        return {
            "action_plan": action_plan,
            "execution_results": [
                *state.get("execution_results", []),
                {
                    "action_id": current_action["id"],
                    "action": current_action["action"],
                    "status": "completed",
                    "result": result,
                },
            ],
            "current_action_index": current_index + 1,
            "workflow_status": "action_completed",
        }

    except Exception as exc:

        return {
            "execution_results": [
                *state.get("execution_results", []),
                {
                    "action_id": current_action["id"],
                    "action": current_action["action"],
                    "status": "failed",
                    "error": str(exc),
                },
            ],
            "workflow_status": "failed",
        }


def approval_node(state: SupportState):

    logger.debug(f'Approval needed for Action: {state["approval_request"]['action']} by {state["approval_request"]['approval_type']}')

    approval_request = state["approval_request"]

    decision = interrupt(approval_request)

    approval_decision = ApprovalDecision.model_validate(
        decision
    )

    action_plan = state["action_plan"]
    current_index = state["current_action_index"]

    current_action = action_plan["actions"][current_index]

    if approval_decision.decision == "approved":

        current_action["approval_status"] = "approved"

        return {
            "action_plan": action_plan,
            "approval_decision": approval_decision.model_dump(),
            "workflow_status": "approval_approved",
        }

    current_action["approval_status"] = "rejected"

    return {
        "action_plan": action_plan,
        "approval_decision": approval_decision.model_dump(),
        "workflow_status": "approval_rejected",
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


def resolution_router(state: SupportState) -> str:
    """Checks if order_id exists and routes accordingly."""
    next = ""
    logger.debug(f"Resolution: {state}")
    
    if state.get("resolution",{}).get("action_required") == True:
        next = "action_planner"                 # Go to action planner
    else:
        next = "response_generator"               # Go to response generator

    logger.debug(f"Routing to {next}")
    return next



def executor_router(state: SupportState):

    status = state["workflow_status"]

    if status == "approval_required":
        return "approval"

    if status == "action_completed":
        return "executor"

    if status in {"completed", "failed", "approval_rejected"}:
        return "response_generator"

    raise ValueError(
        f"Unknown workflow status: {status}"
    )


def approval_router(state: SupportState):

    if state["workflow_status"] == "approval_approved":
        return "executor"

    if state["workflow_status"] == "approval_rejected":
        return "response_generator"

    raise ValueError(
        f"Unknown approval status: {state['workflow_status']}"
    )

order_issue_resolutor = StateGraph(SupportState)


order_issue_resolutor.add_node("request_analyzer", request_analyzer)
order_issue_resolutor.add_node("order_fetch", order_fetch)
order_issue_resolutor.add_node("customer_fetch", customer_fetch)
order_issue_resolutor.add_node("shipment_fetch", shipment_fetch)
order_issue_resolutor.add_node("policy_fetch", policy_fetch)
order_issue_resolutor.add_node("context_builder", context_builder)
order_issue_resolutor.add_node("resolution_analyzer", resolution_analyzer)
order_issue_resolutor.add_node("action_planner", action_planner)
order_issue_resolutor.add_node("action_executor", action_executor)
order_issue_resolutor.add_node("approval_node", approval_node)
order_issue_resolutor.add_node("response_generator", response_generator)



order_issue_resolutor.add_edge(START, "request_analyzer")

# The router returns a list. If it returns ["order_fetch", "policy_fetch"], 
# LangGraph spawns both threads concurrently.
order_issue_resolutor.add_conditional_edges(
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
order_issue_resolutor.add_edge("order_fetch", "context_builder")
order_issue_resolutor.add_edge("customer_fetch", "context_builder")
order_issue_resolutor.add_edge("policy_fetch", "context_builder")
order_issue_resolutor.add_edge("shipment_fetch", "context_builder")

order_issue_resolutor.add_edge("context_builder", "resolution_analyzer")
order_issue_resolutor.add_conditional_edges(
    "resolution_analyzer",
    resolution_router,
    {
        "action_planner": "action_planner",
        "response_generator": "response_generator",
    },
)



# Planner → Executor
order_issue_resolutor.add_edge(
    "action_planner",
    "action_executor",
)


# Executor → next step
order_issue_resolutor.add_conditional_edges(
    "action_executor",
    executor_router,
    {
        "approval": "approval_node",
        "executor": "action_executor",
        "response_generator": "response_generator",
    },
)


# Approval → executor or response
order_issue_resolutor.add_conditional_edges(
    "approval_node",
    approval_router,
    {
        "executor": "action_executor",
        "response_generator": "response_generator",
    },
)


# Response → END
order_issue_resolutor.add_edge(
    "response_generator",
    END,
)
