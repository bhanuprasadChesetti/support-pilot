import logging
from typing import List
from typing_extensions import TypedDict
from sentence_transformers import CrossEncoder

from typing import Literal
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Send,Overwrite
from langgraph.graph import StateGraph, START, END
import operator

from typing import Annotated, TypedDict
from langchain_core.documents import Document

from .vector_db.service import get_vector_store
from .prompts.templates import (
    QUERY_ENHANCEMENT_PROMPT,
    RETRIEVAL_QUALITY_EVALUATION_PROMPT
)
from app.core.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class QueryEnhancementOutput(BaseModel):
    """
    The output schema for the QueryEnhancement chain.
    """
    enhanced_queries: list[str] = Field(
        min_length=1,
        description="One or more retrieval-optimized queries"
    )


class RetrievalEvaluation(BaseModel):
    verdict: str
    score: float
    supported_information: list[str]
    missing_information: list[str]
    evaluator_feedback: str

def create_query_enhancment_chain():

    llm = LLMFactory.get_model()

    prompt = ChatPromptTemplate.from_messages([
        ("system", QUERY_ENHANCEMENT_PROMPT),
        (
            "human",
            """
Original User Query:
{query}

Previous Enhanced Queries:
{previous_enhanced_queries}

Retrieval Attempt:
{attempt}

Retrieval Quality Evaluator Feedback:
{evaluator_feedback}

"""
        ),
    ])

    structured_llm = llm.with_structured_output(
        QueryEnhancementOutput
    )

    chain = prompt | structured_llm

    return chain


def create_retrieval_evaluation_chain():

    llm = LLMFactory.get_model()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            RETRIEVAL_QUALITY_EVALUATION_PROMPT
        ),
        (
            "human",
            """
User Original Query:
{original_query}

Retrieved Evidence:
{retrieved_evidence}
"""
        ),
    ])

    structured_llm = llm.with_structured_output(
        RetrievalEvaluation
    )

    chain = prompt | structured_llm

    return chain


class RAGState(TypedDict, total=False):

    query: str

    enhanced_queries: list[str]

    top_k: int

    reranked_documents: Annotated[
        list[Document],
        operator.add,
    ]

    final_documents: list[Document]

    context: str

    # Retrieval evaluation
    retrieval_attempt: int
    retrieval_evaluation: RetrievalEvaluation
    evaluator_feedback : str



class RetrievalState(TypedDict, total=False):

    query: str

    top_k: int

    raw_documents: list[Document]

    reranked_documents: list[Document]


class RetrievalStateOutputSchema(TypedDict, total=False):

    reranked_documents: list[Document]


reranker_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2",
    device="cpu"
)

vector_store = get_vector_store()

query_enhancement_chain = (
    create_query_enhancment_chain()
)

retrieval_evaluation_chain = (
    create_retrieval_evaluation_chain()
)


def query_enhancement(state: RAGState) -> dict:

    query = state["query"]

    attempt = state.get(
        "retrieval_attempt",
        1
    )

    previous_enhanced_queries = state.get(
        "enhanced_queries",[]
    )

    evaluator_feedback = state.get(
        "evaluator_feedback",None
    )

    logger.info(
        f"Original RAG query : {query}"
    )

    logger.info(
        f"Retrieval attempt : {attempt}"
    )

    if evaluator_feedback:

        logger.info(
            f"Retrieval evaluator feedback : "
            f"{evaluator_feedback}"
        )

    result = query_enhancement_chain.invoke({
        "query": query,
        "previous_enhanced_queries": previous_enhanced_queries,
        "evaluator_feedback": evaluator_feedback,
        "attempt": attempt,
    })

    logger.info(
        f"Got {len(result.enhanced_queries)} Enhanced Queries "
        f"{result.enhanced_queries}"
    )

    return {
        "enhanced_queries": result.enhanced_queries
    }




def retrive_query(state: RAGState):

    return [
        Send(
            "retrieval_subgraph",
            {
                "query": query,
                "top_k": state["top_k"],
            },
        )
        for query in state["enhanced_queries"]
    ]


async def hybrid_search(
    state: RetrievalState
) -> dict:

    """Queries the Qdrant Vector Store using LangChain's async similarity search."""

    query = state["query"]

    logger.debug(
        f'Hybrid search query : {query}'
    )

    k = state["top_k"] * 2

    raw_docs = await vector_store.asimilarity_search(
        query=query,
        k=k
    )

    return {
        "raw_documents": raw_docs
    }


def rerank_documents(
    state: RetrievalState
) -> dict:

    query = state["query"]

    logger.debug(
        f'Reranking documents for query : {query}'
    )

    raw_docs = state.get(
        "raw_documents",
        []
    )

    top_k = state["top_k"]

    if not raw_docs:

        return {
            "reranked_documents": []
        }

    query_doc_pairs = [
        [
            query,
            doc.page_content
        ]
        for doc in raw_docs
    ]

    scores = reranker_model.predict(
        query_doc_pairs
    )

    ranked = sorted(
        zip(
            raw_docs,
            scores
        ),
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "reranked_documents": [
            doc
            for doc, _ in ranked[:top_k]
        ]
    }


def deduplicate_documents(
    documents: list[Document]
) -> list[Document]:

    seen = set()

    unique_documents = []

    for doc in documents:

        chunk_id = doc.metadata.get(
            "_id"
        )

        # Fallback if chunk_id doesn't exist
        if chunk_id is None:
            chunk_id = doc.page_content

        if chunk_id in seen:
            continue

        seen.add(chunk_id)

        unique_documents.append(doc)

    return unique_documents


def aggregate_results(
    state: RAGState
) -> dict:

    # At this point LangGraph has already merged all
    # parallel reranker outputs.
    #
    # Example:
    #
    # Query 1 → [D1, D2, D3]
    # Query 2 → [D2, D4, D5]
    # Query 3 → [D1, D6, D7]
    #
    # reducer:
    #
    # [D1,D2,D3,D2,D4,D5,D1,D6,D7]

    logger.debug(
        'Aggregating results'
    )

    documents = state.get(
        "reranked_documents",
        []
    )

    unique_documents = deduplicate_documents(
        documents
    )

    logger.info(
        f'No of unique documents: '
        f'{len(unique_documents)}'
    )

    return {
        "final_documents": unique_documents
    }


async def format_context(
    state: RAGState
) -> dict:

    documents = state["final_documents"]

    formatted_context = (
        "\n\n---\n\n".join(
            [
                doc.page_content
                for doc in documents
            ]
        )
    )

    return {
        "context": formatted_context
    }

async def retrieval_evaluator(
    state: RAGState
) -> dict:

    logger.info(
        "Running retrieval evaluator"
    )

    result = await retrieval_evaluation_chain.ainvoke({
        "original_query": state["query"],
        "retrieved_evidence": state["context"],
    })

    attempt = state.get(
        "retrieval_attempt",
        1
    )

    # --------------------------------------------------------
    # Prepare collective feedback for Query Enhancement
    # --------------------------------------------------------

    evaluator_feedback = f"""
Retrieval Verdict:
{result.verdict}

Retrieval Score:
{result.score}

Supported Information:
{result.supported_information}

Missing Information:
{result.missing_information}

Evaluator Feedback:
{result.evaluator_feedback}
""".strip()

    logger.info(
        f"Retrieval evaluation attempt "
        f"{attempt}: {result}"
    )

    logger.info(
        f"Collective evaluator feedback: "
        f"{evaluator_feedback}"
    )

    return {
        "retrieval_evaluation": result,
        "evaluator_feedback": evaluator_feedback,
        "retrieval_attempt": attempt,
    }

def prepare_retry(
    state: RAGState
) -> dict:

    current_attempt = state.get(
        "retrieval_attempt",
        1
    )

    next_attempt = current_attempt + 1

    logger.info(
        f"Preparing retrieval retry. "
        f"Next attempt: {next_attempt}"
    )

    return {
        "retrieval_attempt": next_attempt,

        # IMPORTANT:
        #
        # Because reranked_documents uses operator.add,
        # attempt-1 documents would otherwise remain in the
        # state during attempt-2.
        #
        # We return an empty list here so the next retrieval
        # starts with a clean result set.
        "reranked_documents": Overwrite([]),
    }


def route_after_evaluation(
    state: RAGState
):

    evaluation = state[
        "retrieval_evaluation"
    ]

    attempt = state.get(
        "retrieval_attempt",
        1
    )

    logger.info(
        f"Routing after evaluation. "
        f"Attempt={attempt}, "
        f"Verdict={evaluation.verdict}"
    )

    # --------------------------------------------------------
    # GOOD
    #
    # Evidence is sufficient.
    #
    # Future:
    #     evaluator → agent
    #
    # For now:
    #     evaluator → END
    # --------------------------------------------------------

    if evaluation.verdict == "good":

        return "success"

    # --------------------------------------------------------
    # BAD + ATTEMPT 1
    #
    # Retry retrieval using evaluator feedback.
    # --------------------------------------------------------

    if attempt == 1:

        return "retry"

    # --------------------------------------------------------
    # BAD + ATTEMPT 2
    #
    # No more retrieval attempts.
    #
    # Use whatever evidence we have.
    # --------------------------------------------------------

    return "fallback"


def build_rag_graph():

    # ========================================================
    # RETRIEVAL SUBGRAPH
    # ========================================================

    retrival_graph = StateGraph(
        RetrievalState,
        output_schema=RetrievalStateOutputSchema
    )

    retrival_graph.add_node(
        "hybrid_search",
        hybrid_search
    )

    retrival_graph.add_node(
        "rerank",
        rerank_documents
    )

    retrival_graph.add_edge(
        START,
        "hybrid_search"
    )

    retrival_graph.add_edge(
        "hybrid_search",
        "rerank"
    )

    retrival_graph.add_edge(
        "rerank",
        END
    )

    retrieval_subgraph = (
        retrival_graph.compile()
    )

    # ========================================================
    # MAIN RAG GRAPH
    # ========================================================

    rag_graph = StateGraph(
        RAGState
    )

    rag_graph.add_node(
        "query_enhancement",
        query_enhancement
    )

    rag_graph.add_node(
        "retrieval_subgraph",
        retrieval_subgraph
    )

    rag_graph.add_node(
        "aggregate_results",
        aggregate_results
    )

    rag_graph.add_node(
        "format_context",
        format_context
    )

    rag_graph.add_node(
        "retrieval_evaluator",
        retrieval_evaluator
    )

    rag_graph.add_node(
        "prepare_retry",
        prepare_retry
    )

    rag_graph.add_edge(
        START,
        "query_enhancement"
    )

    # ========================================================
    # FAN OUT
    #
    # query_enhancement
    #        ↓
    # retrive_query()
    #        ↓
    # Send(...)
    #        ↓
    # multiple retrieval subgraph executions
    # ========================================================

    rag_graph.add_conditional_edges(
        "query_enhancement",
        retrive_query,
        [
            "retrieval_subgraph"
        ]
    )

    rag_graph.add_edge(
        "retrieval_subgraph",
        "aggregate_results"
    )

    rag_graph.add_edge(
        "aggregate_results",
        "format_context"
    )

    rag_graph.add_edge(
        "format_context",
        "retrieval_evaluator"
    )

    # ========================================================
    # EVALUATOR ROUTING
    #
    # GOOD
    #   ↓
    # END
    #
    # BAD + attempt 1
    #   ↓
    # prepare_retry
    #   ↓
    # query_enhancement
    #
    # BAD + attempt 2
    #   ↓
    # END
    # ========================================================

    rag_graph.add_conditional_edges(
        "retrieval_evaluator",
        route_after_evaluation,
        {
            "success": END,
            "retry": "prepare_retry",
            "fallback": END,
        }
    )

    rag_graph.add_edge(
        "prepare_retry",
        "query_enhancement"
    )

    return rag_graph.compile()


rag = build_rag_graph()