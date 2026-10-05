from typing import List, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent


def get_react_agent(llm: Any, tools: List[Any], system_message: str = None) -> Any:
    """
    Utility function to quickly initialize a modern ReAct Agent using LangGraph.
    
    Args:
        llm: The initialized Language Model instance.
        tools: A list of @tool decorated functions.
        system_message: Custom behavior instructions for the D2C chatbot.
        
    Returns:
        CompiledGraph: A modern runnable object that manages the reasoning-acting loop.
    """
    if not system_message:
        system_message = (
            "You are a precise and helpful AI assistant equipped with external tools to interact with data and perform tasks.\n"
            "Guidelines for Tool Usage:\n"
            "1. Grounded in Tools: Always rely on the provided tools to answer questions that require external data, lookups, or actions. Never guess, assume, or fabricate information.\n"
            "2. Explicit Information: If a tool returns a result, use that exact information in your response. If a tool returns an error or no data, honestly state that you could not retrieve or perform the action based on the tool's response.\n"
            "3. Logical Continuity: Use the conversation history to keep track of context, names, IDs, or previous actions so the user does not have to repeat themselves.\n"
            "4. Professional Tone: Communicate the results clearly and naturally to the user. Do not mention technical tool names, function signatures, or variable names in your chat responses."
        )


    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="messages"),
    ])

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=prompt
    )
