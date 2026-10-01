from typing import List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from .vector_db.service import get_db_client


vector_store = get_db_client()

class RAGState(TypedDict):
    query: str               # Input query from the agent
    top_k: int               # Number of documents to retrieve
    raw_documents: List      # List of LangChain Document objects from Qdrant
    context: str             # Final formatted Top-K context string



async def vector_search(state: RAGState) -> dict:
    """Queries the Qdrant Vector Store using LangChain's async similarity search."""
    query = state["query"]
    
    raw_docs = await vector_store.asimilarity_search(
        query=query,
        k=10
    )
    
    return {"raw_documents": raw_docs}



async def top_k_filter(state: RAGState) -> dict:
    """
    Filters down to Top K results and compiles them into a clean context block.
    """
    raw_docs = state["raw_documents"]
    top_k_limit = state["top_k"]

    top_k_docs = raw_docs[:top_k_limit]
    formatted_context = "\n\n---\n\n".join([doc.page_content for doc in top_k_docs])
    
    return {"context": formatted_context}



rag_workflow = StateGraph(RAGState)

rag_workflow.add_node("vector_search", vector_search)
rag_workflow.add_node("top_k_filter", top_k_filter)

rag_workflow.add_edge(START, "vector_search")
rag_workflow.add_edge("vector_search", "top_k_filter")
rag_workflow.add_edge("top_k_filter", END)



rag = rag_workflow.compile()
