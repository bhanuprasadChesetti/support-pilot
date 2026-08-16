import logging
from typing import Dict, Any, Optional, AsyncIterator
from langchain_core.prompts import ChatPromptTemplate
 
from .factory import LLMFactory

logger = logging.getLogger(__name__)

class LLMService:

    @classmethod
    def _build_prompt_chain(
        cls, 
        provider: str,
        model:str,
        system_prompt: str, 
        user_prompt: str, 
        temperature: float
    ):
        """
        Internal helper to assemble the template and attach fallback chains natively.
        """

        model = LLMFactory.get_model(provider=provider,model=model,temperature=temperature)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
  
        # 5. Connect using standard LangChain pipeline expression syntax
        return prompt_template | model

    @classmethod
    async def generate_response(
        cls,
        provider: str,
        model:str,
        system_prompt: str,
        user_prompt: str,
        prompt_variables: Optional[Dict[str, Any]] = None,
        temperature: float = 0
    ) -> str:
        """
        Executes a single async request and blocks cleanly until the whole response returns.
        """

        variables = prompt_variables or {}
        chain = cls._build_prompt_chain(provider,model,system_prompt,user_prompt,temperature)
        
        response = await chain.ainvoke(variables)
        return str(response.content)

    @classmethod
    async def stream_response(
        cls,
        provider: str,
        model:str,
        system_prompt: str,
        user_prompt: str,
        prompt_variables: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Asynchronously streams the text content chunk-by-chunk for direct FastAPI UI consumption.
        """
        variables = prompt_variables or {}

        chain = cls._build_prompt_chain(provider,model,system_prompt,user_prompt,temperature)
        
        # Yields tokens in real-time as they stream out of whichever provider is currently handling the call
        async for chunk in chain.astream(variables):
            if chunk.content:
                yield str(chunk.content)
