from langchain.agents import create_agent
from langchain_core.tools import tool
from app.core.llm.service import llm
from app.core.tools.rag import create_search_knowledge_tool

search_policy = create_search_knowledge_tool(top_k=3)

policy_agent = create_agent(
    model=llm,
    tools=[
        search_policy,
    ],
    system_prompt="""
You are the Policy Specialist.

Your responsibility is to investigate company policies.

You can:
- search policy documentation
- identify relevant policy rules
- explain policy eligibility requirements

Do not execute business actions.

Return the relevant policy information
and explain which conditions must be satisfied.
""",
)



@tool
def policy_agent_tool(request: str) -> str:
    """
    Delegate a policy investigation to the Policy Specialist.
    """

    result = policy_agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": request,
            }
        ]
    })

    return result["messages"][-1].content