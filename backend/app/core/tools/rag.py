from langchain_core.tools import tool

from app.core.workflows.rag.service import rag


def create_search_knowledge_tool(
    top_k: int,
    name: str = "search_knowledge",
    description: str = (
        "Search the internal knowledge base to retrieve relevant context "
        "and information needed to answer the user's question accurately."
    ),
):
    @tool(name, description=description)
    async def search_knowledge(query: str) -> str:
        result = await rag.ainvoke({
            "query": query,
            "top_k": top_k,
        })

        return result["context"]

    return search_knowledge