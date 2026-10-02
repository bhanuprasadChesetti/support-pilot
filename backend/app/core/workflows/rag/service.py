from typing import List
from typing_extensions import TypedDict
from sentence_transformers import CrossEncoder
from langgraph.graph import StateGraph, START, END
from .vector_db.service import get_vector_store


vector_store = get_vector_store()

# Initialize the Cross-Encoder model once (e.g., during your app startup)
# 'ms-marco-MiniLM' models are fast, lightweight, and excellent for RAG reranking
reranker_model = CrossEncoder("mixedbread-ai/mxbai-rerank-large-v2")


class RAGState(TypedDict):
    query: str               # Input query from the agent
    top_k: int               # Number of documents to retrieve
    raw_documents: List      # List of LangChain Document objects from Qdrant
    context: str             # Final formatted Top-K context string



async def vector_search(state: RAGState) -> dict:
    """Queries the Qdrant Vector Store using LangChain's async similarity search."""
    query = state["query"]
    
    k = state["top_k"] * 3

    raw_docs = await vector_store.asimilarity_search(
        query=query,
        k=k
    )
    
    return {"raw_documents": raw_docs}




def rerank_documents(state: dict) -> dict:
    """
    Reranks a list of Document objects using mixedbread-ai/mxbai-rerank-large-v2.
    
    Expected state structure:
    state = {
        'query': 'Kubernetes Job Hierarchy',
        'top_k': 5,
        'raw_documents': [Document(...), Document(...)]
    }
    """
    query = state.get("query", "")
    raw_docs = state.get("raw_documents", [])
    final_top_k = state.get("top_k", 5)

    
    if not raw_docs:
        state["reranked_documents"] = []
        return state

    
    doc_texts = [doc.page_content for doc in raw_docs]
    query_doc_pairs = [[query, text] for text in doc_texts]
    
    
    scores = reranker_model.predict(query_doc_pairs)
    docs_with_scores = list(zip(raw_docs, scores))
    docs_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    reranked_docs = [doc for doc, score in docs_with_scores[:final_top_k]]
    state["reranked_documents"] = reranked_docs

    return state


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
