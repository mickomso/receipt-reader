"""LangGraph workflow graph assembly.

LIMITATION: Uses MemorySaver (in-process, non-persistent checkpointer).
For production, replace with a SqliteSaver or PostgresSaver checkpoint adapter.
The checkpointer is isolated behind the `build_graph` factory so swapping it
later only requires changing this file.

The graph is compiled once per extractor instance and can be reused across
requests since LangGraph's invoke() is thread-safe when using MemorySaver.
"""

from __future__ import annotations

import functools
import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.workflow.base_extractor import BaseExtractor
from app.workflow.nodes import (
    extract_receipt,
    load_receipt,
    normalize_image,
    persist_result,
    route_result,
    validate_extraction,
    validate_totals,
)
from app.workflow.state import WorkflowState

logger = logging.getLogger(__name__)

# Node names
N_LOAD = "load_receipt"
N_NORMALIZE = "normalize_image"
N_EXTRACT = "extract_receipt"
N_VALIDATE = "validate_extraction"
N_VALIDATE_TOTALS = "validate_totals"
N_ROUTE = "route_result"
N_PERSIST = "persist_result"


def _should_continue(state: WorkflowState) -> str:
    """Route to END on failure, otherwise continue to next node."""
    if state.get("status") == "failed":
        return "persist_on_failure"
    return "continue"


def build_graph(extractor: BaseExtractor, repository) -> StateGraph:
    """Build and compile the receipt processing workflow.

    Args:
        extractor: Concrete BaseExtractor implementation (Gemini or fake).
        repository: ReceiptRepository instance for persistence.

    Returns:
        Compiled LangGraph runnable.
    """
    # Bind dependencies to nodes that require them
    _extract = functools.partial(extract_receipt, extractor=extractor)
    _persist = functools.partial(persist_result, repository=repository)

    builder = StateGraph(WorkflowState)

    # Register nodes
    builder.add_node(N_LOAD, load_receipt)
    builder.add_node(N_NORMALIZE, normalize_image)
    builder.add_node(N_EXTRACT, _extract)
    builder.add_node(N_VALIDATE, validate_extraction)
    builder.add_node(N_VALIDATE_TOTALS, validate_totals)
    builder.add_node(N_ROUTE, route_result)
    builder.add_node(N_PERSIST, _persist)

    # Entry point
    builder.set_entry_point(N_LOAD)

    # Edges with early-exit on failure
    def fail_or_next(next_node: str):
        def _route(state: WorkflowState) -> str:
            return N_PERSIST if state.get("status") == "failed" else next_node
        return _route

    builder.add_conditional_edges(N_LOAD, fail_or_next(N_NORMALIZE))
    builder.add_conditional_edges(N_NORMALIZE, fail_or_next(N_EXTRACT))
    builder.add_conditional_edges(N_EXTRACT, fail_or_next(N_VALIDATE))
    builder.add_conditional_edges(N_VALIDATE, fail_or_next(N_VALIDATE_TOTALS))
    builder.add_conditional_edges(N_VALIDATE_TOTALS, fail_or_next(N_ROUTE))
    builder.add_edge(N_ROUTE, N_PERSIST)
    builder.add_edge(N_PERSIST, END)

    # NOTE: MemorySaver is an in-process, non-persistent checkpoint store.
    # It is adequate for synchronous MVP execution but state is lost on restart.
    # To persist workflow state, swap MemorySaver for:
    #   from langgraph.checkpoint.sqlite import SqliteSaver
    #   checkpointer = SqliteSaver.from_conn_string("data/checkpoints.db")
    checkpointer = MemorySaver()

    return builder.compile(checkpointer=checkpointer)


def run_workflow(
    receipt_id: str,
    file_path: str,
    job_id: str,
    extractor: BaseExtractor,
    repository,
) -> WorkflowState:
    """Execute the processing workflow synchronously.

    Returns the final workflow state dict.
    """
    graph = build_graph(extractor, repository)
    initial_state: WorkflowState = {
        "receipt_id": receipt_id,
        "file_path": file_path,
        "job_id": job_id,
        "status": "processing",
        "error": None,
        "needs_review": False,
        "image_bytes": None,
        "image_mime": None,
        "extraction": None,
        "validation_report": None,
        "overall_confidence": None,
    }
    config = {"configurable": {"thread_id": receipt_id}}
    final_state = graph.invoke(initial_state, config=config)
    return final_state
