"""
Node functions for LangGraph workflow in Memvid RAG Agent
"""

import os
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage

from .state import ConversationState
from .tools import (
    parse_query_intent,
    extract_document_paths,
    validate_file_paths,
    scan_directory_for_documents,
    generate_memory_name,
    create_ingestion_summary,
    format_search_results
)

logger = logging.getLogger(__name__)


async def analyze_query_node(state: ConversationState) -> ConversationState:
    """
    Analyze user query to determine intent and routing
    
    Args:
        state: Current conversation state
        
    Returns:
        Updated state with intent analysis
    """
    try:
        query = state["query"]
        logger.info(f"Analyzing query: {query}")

        # Parse query intent and extract information
        intent_info = parse_query_intent(query)

        state["intent"] = intent_info["intent"]
        state["processing_status"] = "analyzed"

        logger.info(f"Detected intent: {intent_info['intent']}")

    except Exception as e:
        logger.error(f"Error in query analysis: {e}")
        state["intent"] = "error"
        state["processing_status"] = "analysis_error"
        state["error_message"] = str(e)

    return state


def route_query(state: ConversationState) -> str:
    """
    Route query based on analyzed intent
    
    Args:
        state: Current conversation state
        
    Returns:
        Next node name to execute
    """
    intent = state.get("intent", "chat")

    routing = {
        "ingest": "document_ingestor",
        "search": "semantic_retriever",
        "chat": "semantic_retriever",
        "manage": "memory_manager",
        "error": "error_handler"
    }

    return routing.get(intent, "semantic_retriever")


async def ingest_documents_node(state: ConversationState, memvid_encoder_class, memvid_config: Dict[str, Any], storage_path: str) -> ConversationState:
    """
    Handle document ingestion into memvid videos
    
    Args:
        state: Current conversation state
        memvid_encoder_class: MemvidEncoder class
        memvid_config: Memvid configuration
        storage_path: Path to store memory videos
        
    Returns:
        Updated state with ingestion results
    """
    try:
        query = state["query"]
        logger.info(f"Starting document ingestion for query: {query}")

        # Extract document paths and directories
        document_paths = extract_document_paths(query)

        # If no explicit paths, check for directory reference
        if not document_paths:
            # Look for directory patterns in query
            import re
            dir_match = re.search(
                r'(["\']?)([^"\']*(?:documents?|files?|folder)[^"\']*)\1', query.lower())
            if dir_match:
                potential_dir = dir_match.group(2).strip()
                if os.path.exists(potential_dir):
                    document_paths = scan_directory_for_documents(
                        potential_dir)

        if not document_paths:
            state["response"] = """❌ No valid document paths found in your request. 

**To ingest documents, try:**
• `Ingest "document.pdf" "notes.txt"`
• `Process files in "documents/" folder`
• `Add "research_paper.pdf" to memory`

**Supported formats:** PDF, TXT, EPUB, MD, DOCX"""
            state["processing_status"] = "no_documents"
            return state

        # Validate file paths
        validation_result = validate_file_paths(document_paths)
        valid_paths = validation_result["valid"]
        invalid_paths = validation_result["invalid"]

        if not valid_paths:
            state["response"] = f"""❌ No valid documents found.

**Invalid paths:**
{chr(10).join(f'• {path}' for path in invalid_paths)}

**Supported formats:** {', '.join(validation_result['supported_extensions'])}"""
            state["processing_status"] = "invalid_documents"
            return state

        # Generate memory name
        memory_name = generate_memory_name(valid_paths)

        # Initialize encoder
        encoder = memvid_encoder_class()

        # Process documents
        ingestion_stats = {"processed": 0, "failed": 0, "total_chunks": 0}

        for doc_path in valid_paths:
            try:
                doc_path_obj = Path(doc_path)
                logger.info(f"Processing document: {doc_path}")

                if doc_path_obj.suffix.lower() == '.pdf':
                    encoder.add_pdf(str(doc_path))
                elif doc_path_obj.suffix.lower() == '.epub':
                    encoder.add_epub(str(doc_path))
                else:
                    # Handle text files
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    encoder.add_text(content, metadata={
                                     "source": doc_path_obj.name})

                ingestion_stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error processing {doc_path}: {e}")
                ingestion_stats["failed"] += 1
                continue

        if encoder.chunks:
            # Create storage directory
            storage_path_obj = Path(storage_path)
            storage_path_obj.mkdir(exist_ok=True)

            # Build video memory
            video_path = storage_path_obj / f"{memory_name}.mp4"
            index_path = storage_path_obj / f"{memory_name}_index.json"

            logger.info(f"Building video memory: {video_path}")
            build_stats = encoder.build_video(str(video_path), str(index_path))

            ingestion_stats["total_chunks"] = len(encoder.chunks)
            ingestion_stats["video_size_mb"] = video_path.stat(
            ).st_size / (1024*1024)

            # Store memory reference in state
            state["memory_paths"] = {
                "video": str(video_path),
                "index": str(index_path),
                "name": memory_name
            }

            # Create success response
            state["response"] = create_ingestion_summary(
                ingestion_stats, memory_name)

            if invalid_paths:
                state["response"] += f"\n\n⚠️ **Skipped files:**\n"
                state["response"] += "\n".join(
                    f"• {path}" for path in invalid_paths)
        else:
            state["response"] = "❌ No content could be extracted from the provided documents."

        state["processing_status"] = "ingestion_complete"

    except Exception as e:
        logger.error(f"Error during document ingestion: {e}")
        state["response"] = f"❌ Error during document ingestion: {str(e)}"
        state["processing_status"] = "ingestion_error"
        state["error_message"] = str(e)

    return state


async def retrieve_context_node(state: ConversationState, active_memories: Dict[str, Any]) -> ConversationState:
    """
    Retrieve relevant context from memvid memories
    
    Args:
        state: Current conversation state
        active_memories: Dictionary of active memory retrievers
        
    Returns:
        Updated state with retrieved context
    """
    try:
        query = state["query"]
        retrieved_chunks = []

        logger.info(f"Retrieving context for query: {query}")

        if not active_memories:
            state["context"] = []
            state["retrieved_chunks"] = []
            state["processing_status"] = "no_memories"
            return state

        # Search across all active memories
        for memory_name, retriever in active_memories.items():
            try:
                logger.info(f"Searching memory: {memory_name}")
                results = retriever.search(query, top_k=5)

                for i, (text, score) in enumerate(results):
                    chunk_data = {
                        "text": text,
                        "score": float(score),
                        "source_memory": memory_name,
                        "rank": i + 1
                    }
                    retrieved_chunks.append(chunk_data)

            except Exception as e:
                logger.error(f"Error searching memory {memory_name}: {e}")
                continue

        # Sort by relevance score and take top results
        retrieved_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        state["retrieved_chunks"] = retrieved_chunks[:10]

        # Extract text for context
        context_texts = [chunk["text"] for chunk in retrieved_chunks[:5]]
        state["context"] = context_texts

        state["processing_status"] = "context_retrieved"
        logger.info(f"Retrieved {len(context_texts)} context chunks")

    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        state["context"] = []
        state["retrieved_chunks"] = []
        state["processing_status"] = "retrieval_error"
        state["error_message"] = str(e)

    return state


async def assemble_context_node(state: ConversationState) -> ConversationState:
    """
    Assemble retrieved chunks into coherent context
    
    Args:
        state: Current conversation state
        
    Returns:
        Updated state with assembled context
    """
    try:
        chunks = state.get("retrieved_chunks", [])

        if not chunks:
            state["context"] = []
            state["processing_status"] = "no_context"
            return state

        # Create structured context with metadata
        context_parts = []
        for i, chunk in enumerate(chunks[:5], 1):
            source = chunk.get("source_memory", "unknown")
            score = chunk.get("score", 0)
            text = chunk.get("text", "")

            context_part = f"[Context {i}] (Relevance: {score:.3f}, Source: {source})\n{text}"
            context_parts.append(context_part)

        # Assemble final context
        assembled_context = "\n\n".join(context_parts)
        state["context"] = [assembled_context]
        state["processing_status"] = "context_assembled"

        logger.info(f"Assembled context from {len(context_parts)} chunks")

    except Exception as e:
        logger.error(f"Error assembling context: {e}")
        state["processing_status"] = "assembly_error"
        state["error_message"] = str(e)

    return state


async def generate_response_node(state: ConversationState, llm) -> ConversationState:
    """
    Generate response using LLM with retrieved context
    
    Args:
        state: Current conversation state
        llm: Language model instance
        
    Returns:
        Updated state with generated response
    """
    try:
        query = state["query"]
        context = state.get("context", [])

        logger.info(f"Generating response for query: {query}")

        if not context:
            response_prompt = f"""The user asked: "{query}"

However, no relevant context was found in the knowledge base. Please provide a helpful response explaining that no relevant information was found and suggest how they might:

1. Add relevant documents to the knowledge base
2. Refine their query to be more specific
3. Use different keywords

Be polite and helpful."""
        else:
            context_text = "\n\n".join(context)
            response_prompt = f"""Based on the following context from the knowledge base, please answer the user's question comprehensively and accurately.

**Context:**
{context_text}

**User Question:** "{query}"

**Instructions:**
- Provide a comprehensive answer based on the context provided
- If the context doesn't fully answer the question, acknowledge this limitation
- Use information only from the provided context
- Be specific and cite relevant details from the context
- If multiple sources provide different perspectives, mention this

Please provide your response:"""

        # Add conversation history for context
        messages = state.get("messages", [])
        messages.append(HumanMessage(content=response_prompt))

        # Generate response
        result = await llm.ainvoke(messages)
        response = result.content

        # Update conversation state
        state["response"] = response
        state["messages"] = messages + [AIMessage(content=response)]
        state["processing_status"] = "response_generated"

        logger.info("Response generated successfully")

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        state["response"] = f"❌ Error generating response: {str(e)}"
        state["processing_status"] = "generation_error"
        state["error_message"] = str(e)

    return state


async def manage_memory_node(state: ConversationState, active_memories: Dict[str, Any], storage_path: str) -> ConversationState:
    """
    Handle memory management operations
    
    Args:
        state: Current conversation state
        active_memories: Dictionary of active memory retrievers
        storage_path: Path where memory videos are stored
        
    Returns:
        Updated state with management results
    """
    try:
        query = state["query"].lower()

        if "list" in query or "show" in query:
            if active_memories:
                memory_info = []
                for name, retriever in active_memories.items():
                    try:
                        # Get memory statistics
                        video_path = Path(storage_path) / f"{name}.mp4"
                        if video_path.exists():
                            size_mb = video_path.stat().st_size / (1024*1024)
                            # Try to get chunk count from retriever
                            chunk_count = "unknown"
                            info = f"• **{name}**: {size_mb:.1f} MB"
                            memory_info.append(info)
                    except Exception:
                        memory_info.append(
                            f"• **{name}**: (stats unavailable)")

                response = f"📁 **Active Memory Stores:**\n" + \
                    "\n".join(memory_info)
            else:
                response = "📁 No memory stores currently loaded.\n\n💡 To get started:\n• Ingest documents with: `Add \"document.pdf\" to memory`"

        elif "stats" in query or "statistics" in query:
            if active_memories:
                total_memories = len(active_memories)
                total_size_mb = 0

                # Calculate total storage size
                storage_path_obj = Path(storage_path)
                if storage_path_obj.exists():
                    for video_file in storage_path_obj.glob("*.mp4"):
                        total_size_mb += video_file.stat().st_size / (1024*1024)

                response = f"""📊 **Memory Statistics:**

🎯 **Overview:**
• Total memory stores: {total_memories}
• Total storage size: {total_size_mb:.1f} MB
• Storage location: {storage_path}

💾 **Storage Efficiency:**
• Video-based compression provides 10x efficiency vs traditional databases
• Each memory can store millions of text chunks
• Offline-first design - no internet required for search"""
            else:
                response = "📊 No memory statistics available - no memories loaded."

        else:
            response = """🛠️ **Memory Management Commands:**

**View Information:**
• `list memories` - Show active memory stores
• `show statistics` - Display detailed statistics

**Usage:**
• Ask questions to search across all loaded memories
• Add documents with: `ingest "file.pdf"`

**Tips:**
• Memories persist between sessions
• Video files can be copied and shared
• Search works across all loaded memories simultaneously"""

        state["response"] = response
        state["processing_status"] = "memory_managed"

    except Exception as e:
        logger.error(f"Error in memory management: {e}")
        state["response"] = f"❌ Error in memory management: {str(e)}"
        state["processing_status"] = "management_error"
        state["error_message"] = str(e)

    return state


async def handle_errors_node(state: ConversationState) -> ConversationState:
    """
    Handle various error conditions
    
    Args:
        state: Current conversation state
        
    Returns:
        Updated state with error handling
    """
    status = state.get("processing_status", "unknown_error")
    error_message = state.get("error_message", "")

    error_responses = {
        "analysis_error": "❌ I encountered an error analyzing your query. Please try rephrasing your request.",
        "ingestion_error": "❌ There was an error processing your documents. Please check the file paths and formats.",
        "retrieval_error": "❌ I couldn't search the knowledge base properly. Please try a different query.",
        "generation_error": "❌ I encountered an error generating a response. Please try again.",
        "no_memories": "💡 No memory stores are currently loaded. Please ingest some documents first using: `Add \"document.pdf\" to memory`",
        "no_context": "🔍 No relevant information found for your query. Try:\n• Using different keywords\n• Adding relevant documents to memory\n• Being more specific in your question"
    }

    base_response = error_responses.get(
        status.split(":")[0],
        "❌ An unexpected error occurred. Please try again."
    )

    if error_message and "debug" in state.get("query", "").lower():
        state["response"] = f"{base_response}\n\n**Debug info:** {error_message}"
    else:
        state["response"] = base_response

    state["processing_status"] = "error_handled"

    return state
