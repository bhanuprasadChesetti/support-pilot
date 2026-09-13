import logging
from typing import Dict, Any, List, Optional, AsyncIterator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from .factory import LLMFactory

logger = logging.getLogger(__name__)

class LLMService:

    @classmethod
    def _build_prompt_chain(
        cls, 
        provider: str,
        model: str,
        system_prompt: str, 
        user_prompt: str, 
        temperature: float,
        timeout: float = 120.0,
    ):
        """
        Internal helper to assemble the template and attach fallback chains natively.
        """

        model_inst = LLMFactory.get_model(provider=provider, model=model, temperature=temperature, timeout=timeout)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
  
        # Connect using standard LangChain pipeline expression syntax
        return prompt_template | model_inst

    @classmethod
    def _build_chat_prompt_chain(
        cls, 
        provider: str,
        model: str,
        system_prompt: str, 
        messages: List[Dict[str, Any]], 
        temperature: float,
        timeout: float = 120.0,
    ):
        """
        Internal helper to assemble a chat prompt template from history, tool messages and attach model.
        """
        model_inst = LLMFactory.get_model(provider=provider, model=model, temperature=temperature, timeout=timeout)

        prompt_objects = [SystemMessage(content=system_prompt)]

        for msg in messages:
            role = str(msg.get("role", "user")).lower()
            content = msg.get("content", "") or ""

            if role in ("user", "human"):
                prompt_objects.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                tool_calls = msg.get("tool_calls")
                prompt_objects.append(AIMessage(content=content, tool_calls=tool_calls or []))
            elif role == "system":
                prompt_objects.append(SystemMessage(content=content))
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                name = msg.get("name", "")
                prompt_objects.append(ToolMessage(content=content, tool_call_id=tool_call_id, name=name))
            else:
                prompt_objects.append(HumanMessage(content=content))

        prompt_template = ChatPromptTemplate.from_messages(prompt_objects)
        return prompt_template | model_inst

    @classmethod
    async def generate_chat_response(
        cls,
        provider: str,
        model: str,
        messages: List[Dict[str, Any]],
        system_prompt: str = "You are a helpful assistant.",
        prompt_variables: Optional[Dict[str, Any]] = None,
        temperature: float = 0,
        timeout: float = 120.0,
    ) -> str:
        """
        Executes a request passing full conversation message history and support for all roles (system, user, assistant, tool) to the LLM.
        """
        variables = prompt_variables or {}
        chain = cls._build_chat_prompt_chain(
            provider=provider, 
            model=model, 
            system_prompt=system_prompt, 
            messages=messages, 
            temperature=temperature,
            timeout=timeout,
        )
        response = await chain.ainvoke(variables)
        return str(response.content)

    @classmethod
    async def stream_chat_response(
        cls,
        provider: str,
        model: str,
        messages: List[Dict[str, Any]],
        system_prompt: str = "You are a helpful assistant.",
        prompt_variables: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        timeout: float = 120.0,
    ) -> AsyncIterator[str]:
        """
        Asynchronously streams token sequences chunk-by-chunk for multi-turn conversation history.
        """
        variables = prompt_variables or {}
        chain = cls._build_chat_prompt_chain(
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            messages=messages,
            temperature=temperature,
            timeout=timeout,
        )

        async for chunk in chain.astream(variables):
            if chunk.content:
                yield str(chunk.content)

    @classmethod
    async def generate_response(
        cls,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        prompt_variables: Optional[Dict[str, Any]] = None,
        temperature: float = 0,
        timeout: float = 120.0,
    ) -> str:
        """
        Executes a single async request and blocks cleanly until the whole response returns.
        """

        variables = prompt_variables or {}
        chain = cls._build_prompt_chain(provider, model, system_prompt, user_prompt, temperature, timeout=timeout)
        
        response = await chain.ainvoke(variables)
        return str(response.content)

    @classmethod
    async def stream_response(
        cls,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        prompt_variables: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        timeout: float = 120.0,
    ) -> AsyncIterator[str]:
        """
        Asynchronously streams the text content chunk-by-chunk for direct FastAPI UI consumption.
        """
        variables = prompt_variables or {}

        chain = cls._build_prompt_chain(provider, model, system_prompt, user_prompt, temperature, timeout=timeout)
        
        # Yields tokens in real-time as they stream out of whichever provider is currently handling the call
        async for chunk in chain.astream(variables):
            if chunk.content:
                yield str(chunk.content)

