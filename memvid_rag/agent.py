"""
Main Memvid RAG Agent implementation using LangGraph
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# Import memvid components
try:
    from memvid import MemvidEncoder, MemvidRetriever
except ImportError:
    raise ImportError(
        "Memvid library not found. Install with: pip install memvid")

# Import local modules
from .config import get_config, get_memvid_config, get_available_providers
from .utils.state import ConversationState
from .utils.nodes import (
    analyze_query_node,
    route_query,
    ingest_documents_node,
    retrieve_context_node,
    assemble_context_node,
    generate_response_node,
    manage_memory_node,
    handle_errors_node
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemvidRAGAgent:
    """
    Advanced RAG agent built with LangGraph that integrates memvid for 
    video-based knowledge storage and retrieval.
    """

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        memory_storage_path: Optional[str] = None,
        config_overrides: Optional[Dict] = None,
        debug: bool = False
    ):
        """
        Initialize the Memvid RAG Agent
        
        Args:
            llm_provider: LLM provider ("openai", "anthropic", "google")
            api_key: API key for the LLM provider
            model_name: Specific model name to use
            memory_storage_path: Path to store memory videos
            config_overrides: Override default configuration
            debug: Enable debug logging
        """
        # Set up logging level
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)

        # Load configuration
        self.config = get_config()
        self.memvid_config = get_memvid_config()

        # Apply config overrides
        if config_overrides:
            self.memvid_config.update(config_overrides)

        # Set up LLM provider
        self.llm_provider = llm_provider or self.config.DEFAULT_LLM_PROVIDER
        self.api_key = api_key or self._get_api_key(self.llm_provider)
        self.model_name = model_name or self.config.DEFAULT_MODEL_NAME

        # Validate LLM setup
        if not self.api_key:
            available_providers = get_available_providers()
            if available_providers:
                self.llm_provider = available_providers[0]
                self.api_key = self._get_api_key(self.llm_provider)
                logger.warning(
                    f"No API key for {llm_provider}, using {self.llm_provider}")
            else:
                raise ValueError(
                    "No valid API keys found. Please set API keys in .env file.")

        # Initialize LLM
        self.llm = self._initialize_llm(self.llm_provider, self.model_name)

        # Set up storage
        self.memory_storage_path = Path(
            memory_storage_path or self.config.MEMVID_STORAGE_PATH)
        self.memory_storage_path.mkdir(exist_ok=True)

        # Initialize LangGraph
        self.graph = self._build_graph()
        self.app = self.graph.compile()

        # Active memory stores and session data
        self.active_memories: Dict[str, MemvidRetriever] = {}
        self.session_data: Dict[str, Any] = {}

        # Load existing memories on startup
        self._load_existing_memories()

        logger.info(f"MemvidRAGAgent initialized with {self.llm_provider} LLM")
        logger.info(f"Storage path: {self.memory_storage_path}")
        logger.info(f"Loaded {len(self.active_memories)} existing memories")

    def _get_api_key(self, provider: str) -> str:
        """Retrieve API key based on provider"""
        key_mapping = {
            "openai": self.config.OPENAI_API_KEY,
            "anthropic": self.config.ANTHROPIC_API_KEY,
            "google": self.config.GOOGLE_API_KEY
        }
        return key_mapping.get(provider, "")

    def _initialize_llm(self, provider: str, model_name: str):
        """Initialize LLM based on provider"""
        try:
            if provider == "openai":
                return ChatOpenAI(
                    api_key=self.api_key,
                    model=model_name or "gpt-4-turbo-preview",
                    temperature=0.7
                )
            elif provider == "anthropic":
                return ChatAnthropic(
                    anthropic_api_key=self.api_key,
                    model=model_name or "claude-3-sonnet-20240229",
                    temperature=0.7
                )
            elif provider == "google":
                return ChatGoogleGenerativeAI(
                    google_api_key=self.api_key,
                    model=model_name or "gemini-1.5-pro",
                    temperature=0.7
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for RAG operations"""

        workflow = StateGraph(ConversationState)

        # Add nodes for different processing stages
        workflow.add_node("query_analyzer", self._wrap_analyze_query)
        workflow.add_node("document_ingestor", self._wrap_ingest_documents)
        workflow.add_node("semantic_retriever", self._wrap_retrieve_context)
        workflow.add_node("context_assembler", self._wrap_assemble_context)
        workflow.add_node("response_generator", self._wrap_generate_response)
        workflow.add_node("memory_manager", self._wrap_manage_memory)
        workflow.add_node("error_handler", self._wrap_handle_errors)

        # Define the workflow edges and routing logic
        workflow.set_entry_point("query_analyzer")

        workflow.add_conditional_edges(
            "query_analyzer",
            route_query,
            {
                "document_ingestor": "document_ingestor",
                "semantic_retriever": "semantic_retriever",
                "memory_manager": "memory_manager",
                "error_handler": "error_handler"
            }
        )

        workflow.add_edge("document_ingestor", END)
        workflow.add_edge("semantic_retriever", "context_assembler")
        workflow.add_edge("context_assembler", "response_generator")
        workflow.add_edge("response_generator", END)
        workflow.add_edge("memory_manager", END)
        workflow.add_edge("error_handler", END)

        return workflow

    # Wrapper methods to inject dependencies into nodes
    async def _wrap_analyze_query(self, state: ConversationState) -> ConversationState:
        return await analyze_query_node(state)

    async def _wrap_ingest_documents(self, state: ConversationState) -> ConversationState:
        # Update active memories after ingestion
        result = await ingest_documents_node(
            state, MemvidEncoder, self.memvid_config, str(
                self.memory_storage_path)
        )

        # Load the new memory if successful
        if result.get("memory_paths") and "name" in result["memory_paths"]:
            memory_name = result["memory_paths"]["name"]
            video_path = result["memory_paths"]["video"]
            index_path = result["memory_paths"]["index"]

            try:
                self.active_memories[memory_name] = MemvidRetriever(
                    video_path, index_path)
                logger.info(f"Loaded new memory: {memory_name}")
            except Exception as e:
                logger.error(f"Error loading new memory {memory_name}: {e}")

        return result

    async def _wrap_retrieve_context(self, state: ConversationState) -> ConversationState:
        return await retrieve_context_node(state, self.active_memories)

    async def _wrap_assemble_context(self, state: ConversationState) -> ConversationState:
        return await assemble_context_node(state)

    async def _wrap_generate_response(self, state: ConversationState) -> ConversationState:
        return await generate_response_node(state, self.llm)

    async def _wrap_manage_memory(self, state: ConversationState) -> ConversationState:
        return await manage_memory_node(state, self.active_memories, str(self.memory_storage_path))

    async def _wrap_handle_errors(self, state: ConversationState) -> ConversationState:
        return await handle_errors_node(state)

    def _load_existing_memories(self) -> Dict[str, str]:
        """Load existing memvid memories from storage directory"""
        loaded_memories = {}

        try:
            for video_file in self.memory_storage_path.glob("*.mp4"):
                memory_name = video_file.stem
                index_file = video_file.with_name(f"{memory_name}_index.json")

                if index_file.exists():
                    try:
                        retriever = MemvidRetriever(
                            str(video_file), str(index_file))
                        self.active_memories[memory_name] = retriever
                        loaded_memories[memory_name] = str(video_file)
                        logger.debug(f"Loaded memory: {memory_name}")
                    except Exception as e:
                        logger.error(
                            f"Error loading memory {memory_name}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error scanning for existing memories: {e}")

        return loaded_memories

    async def query(self, user_input: str, session_id: str = "default") -> str:
        """
        Main query interface for the RAG agent
        
        Args:
            user_input: User's question or command
            session_id: Session identifier for conversation tracking
            
        Returns:
            Agent's response string
        """

        # Initialize session if needed
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                "messages": [],
                "created_at": datetime.now()
            }

        # Prepare initial state
        initial_state = ConversationState(
            messages=self.session_data[session_id]["messages"],
            query=user_input,
            context=[],
            retrieved_chunks=[],
            response="",
            intent="",
            processing_status="initialized",
            session_id=session_id,
            memory_paths={},
            error_message=None
        )

        # Process through the graph
        try:
            logger.info(f"Processing query: {user_input}")
            result = await self.app.ainvoke(initial_state)

            # Update session data
            if "messages" in result:
                self.session_data[session_id]["messages"] = result["messages"]

            response = result.get("response", "❌ No response generated.")
            logger.info(
                f"Query processed successfully. Status: {result.get('processing_status', 'unknown')}")

            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"❌ Error processing query: {str(e)}"

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about loaded memories"""
        stats = {
            "total_memories": len(self.active_memories),
            "memory_details": {},
            "total_size_mb": 0,
            "storage_path": str(self.memory_storage_path)
        }

        # Calculate storage size and get memory details
        for name in self.active_memories.keys():
            try:
                video_path = self.memory_storage_path / f"{name}.mp4"
                if video_path.exists():
                    size_mb = video_path.stat().st_size / (1024*1024)
                    stats["memory_details"][name] = {
                        "size_mb": round(size_mb, 2),
                        "video_path": str(video_path)
                    }
                    stats["total_size_mb"] += size_mb
            except Exception as e:
                stats["memory_details"][name] = {"error": str(e)}

        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats

    async def ingest_documents(
        self,
        document_paths: List[str],
        memory_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for document ingestion
        
        Args:
            document_paths: List of paths to documents to ingest
            memory_name: Custom name for the memory (optional)
            
        Returns:
            Dictionary with ingestion results
        """

        # Format as a query for the graph
        paths_str = ", ".join(f'"{path}"' for path in document_paths)
        query = f"Please ingest these documents: {paths_str}"

        response = await self.query(query)

        return {
            "response": response,
            "memory_name": memory_name,
            "ingested_files": document_paths,
            "active_memories": list(self.active_memories.keys())
        }

    def list_memories(self) -> List[str]:
        """Get list of active memory names"""
        return list(self.active_memories.keys())

    def reload_memories(self) -> Dict[str, str]:
        """Reload memories from storage directory"""
        self.active_memories.clear()
        return self._load_existing_memories()

# Create the compiled app for LangGraph deployment


def create_app():
    """Create the LangGraph app for deployment"""
    agent = MemvidRAGAgent()
    return agent.app


# Export the app for langgraph.json
app = create_app()
