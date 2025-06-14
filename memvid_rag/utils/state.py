"""
State definitions for LangGraph workflow
"""

from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage


class ConversationState(TypedDict):
    """State for managing conversation flow and context"""
    messages: List[BaseMessage]
    query: str
    context: List[str]
    retrieved_chunks: List[Dict[str, Any]]
    response: str
    intent: str
    processing_status: str
    session_id: str
    memory_paths: Dict[str, str]
    error_message: Optional[str]


class DocumentState(TypedDict):
    """State for document ingestion and processing"""
    documents: List[str]
    video_path: str
    index_path: str
    ingestion_stats: Dict[str, Any]
    processing_errors: List[str]
    memory_name: str


class RetrievalState(TypedDict):
    """State for retrieval operations"""
    search_query: str
    search_results: List[Dict[str, Any]]
    relevance_scores: List[float]
    context_window: str
    retrieval_metadata: Dict[str, Any]


class ManagementState(TypedDict):
    """State for memory management operations"""
    operation: str  # "list", "stats", "load", "delete"
    memory_info: Dict[str, Any]
    operation_result: str
