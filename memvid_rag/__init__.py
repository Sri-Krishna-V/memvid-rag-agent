"""
Memvid RAG Agent with LangGraph

A complete implementation of a Retrieval Augmented Generation (RAG) system 
using Memvid for video-based knowledge storage and LangGraph for stateful 
agent orchestration.
"""

__version__ = "1.0.0"
__author__ = "Memvid RAG Team"

from .agent import MemvidRAGAgent
from .config import get_config

__all__ = ["MemvidRAGAgent", "get_config"]
