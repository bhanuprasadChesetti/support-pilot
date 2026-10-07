
from pydantic import BaseModel, Field
from typing import Any


class ActionDefinition(BaseModel):
    name: str
    description: str

    # Name of the actual tool that performs the action
    tool_name: str

    # Information/state required before this action can execute
    requires: list[str] = Field(default_factory=list)

    # Information/state produced after successful execution
    produces: list[str] = Field(default_factory=list)

    # Whether this action changes something in the system
    side_effect: bool = False

    requires_approval: bool = False
    approval_type: str | None = None



ACTION_DEFINITIONS = [

    ActionDefinition(
        name="cancel_order",
        description="Cancel an eligible customer order.",
        tool_name="cancel_order",
        requires=["order_exists", "order_cancellable"],
        produces=["order_cancelled"],
        side_effect=True,
        requires_approval=True,
        approval_type="customer",
    ),

    ActionDefinition(
        name="initiate_refund",
        description="Initiate a refund for an eligible cancelled order.",
        tool_name="initiate_refund",
        requires=["order_cancelled", "refund_eligible"],
        produces=["refund_initiated"],
        side_effect=True,
        requires_approval=True,
        approval_type="manager",
    ),

    ActionDefinition(
        name="create_return",
        description="Create a return request for an eligible order.",
        tool_name="create_return",
        requires=["order_exists", "return_eligible"],
        produces=["return_created"],
        side_effect=True,
        requires_approval=False,
        approval_type=None,
    ),

]

from app.core.tools.ecommerce import cancel_order, initiate_refund, create_return
TOOL_REGISTRY = {
    "cancel_order": cancel_order,
    "initiate_refund": initiate_refund,
    "create_return": create_return,
}


def build_action_catalog():

    catalog = []

    for action in ACTION_DEFINITIONS:

        tool = TOOL_REGISTRY[action.name]

        catalog.append({
            "name": action.name,
            "description": action.description,
            "requires": action.requires,
            "produces": action.produces,
            "side_effect": action.side_effect,
            "tool_schema": tool.args_schema.model_json_schema(),
        })

    return catalog

action_catalog = build_action_catalog()

