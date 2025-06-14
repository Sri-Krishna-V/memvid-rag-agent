"""
Basic tests for Memvid RAG Agent
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing"""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-123'}):
        yield 'test-key-123'


@pytest.fixture
def temp_storage():
    """Provide temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_config_loading():
    """Test configuration loading"""
    from memvid_rag.config import get_config, get_memvid_config

    config = get_config()
    assert hasattr(config, 'MEMVID_CHUNK_SIZE')
    assert hasattr(config, 'DEFAULT_LLM_PROVIDER')

    memvid_config = get_memvid_config()
    assert 'chunk_size' in memvid_config
    assert 'embedding_model' in memvid_config


def test_agent_initialization_with_mock_key(mock_api_key, temp_storage):
    """Test agent initialization with mocked dependencies"""

    # Mock memvid imports to avoid actual installation requirement
    with patch.dict('sys.modules', {
        'memvid': MagicMock(),
        'memvid.MemvidEncoder': MagicMock(),
        'memvid.MemvidRetriever': MagicMock()
    }):
        # Mock LLM initialization
        with patch('memvid_rag.agent.ChatOpenAI') as mock_llm:
            mock_llm.return_value = MagicMock()

            from memvid_rag.agent import MemvidRAGAgent

            agent = MemvidRAGAgent(
                llm_provider="openai",
                memory_storage_path=str(temp_storage)
            )

            assert agent.llm_provider == "openai"
            assert agent.memory_storage_path == temp_storage
            assert hasattr(agent, 'active_memories')
            assert hasattr(agent, 'session_data')


def test_tools_functions():
    """Test utility functions"""
    from memvid_rag.utils.tools import (
        extract_document_paths,
        validate_file_paths,
        parse_query_intent,
        sanitize_memory_name
    )

    # Test document path extraction
    query1 = 'Ingest "document.pdf" and "notes.txt"'
    paths = extract_document_paths(query1)
    assert "document.pdf" in paths
    assert "notes.txt" in paths

    # Test query intent parsing
    intent_info = parse_query_intent("What is machine learning?")
    assert intent_info["intent"] == "search"

    intent_info = parse_query_intent('Add "file.pdf" to memory')
    assert intent_info["intent"] == "ingest"

    # Test memory name sanitization
    sanitized = sanitize_memory_name("My<>Document|Memory")
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert "|" not in sanitized


def test_state_definitions():
    """Test state type definitions"""
    from memvid_rag.utils.state import ConversationState, DocumentState

    # This mainly tests that imports work and types are defined
    assert ConversationState
    assert DocumentState


@pytest.mark.asyncio
async def test_node_functions_with_mocks():
    """Test node functions with mocked dependencies"""
    from memvid_rag.utils.nodes import analyze_query_node, handle_errors_node
    from memvid_rag.utils.state import ConversationState

    # Test query analysis
    state = ConversationState(
        messages=[],
        query="What is AI?",
        context=[],
        retrieved_chunks=[],
        response="",
        intent="",
        processing_status="",
        session_id="test",
        memory_paths={},
        error_message=None
    )

    result = await analyze_query_node(state)
    assert result["intent"] in ["search", "chat", "ingest", "manage", "error"]
    assert result["processing_status"] == "analyzed"

    # Test error handling
    error_state = ConversationState(
        messages=[],
        query="test",
        context=[],
        retrieved_chunks=[],
        response="",
        intent="",
        processing_status="analysis_error",
        session_id="test",
        memory_paths={},
        error_message="Test error"
    )

    result = await handle_errors_node(error_state)
    assert "error" in result["response"].lower()

if __name__ == "__main__":
    pytest.main([__file__])
