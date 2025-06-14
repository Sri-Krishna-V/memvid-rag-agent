"""
Helper tools and utility functions for Memvid RAG Agent
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Set up logging
logger = logging.getLogger(__name__)


def extract_document_paths(query: str) -> List[str]:
    """
    Extract document paths from user query using pattern matching
    
    Args:
        query: User input string containing potential file paths
        
    Returns:
        List of extracted file paths
    """
    # Pattern to match quoted file paths
    quoted_patterns = [
        r'"([^"]+\.[a-zA-Z]{2,4})"',  # Double quotes
        r"'([^']+\.[a-zA-Z]{2,4})'",  # Single quotes
    ]

    # Pattern to match unquoted file paths
    unquoted_patterns = [
        r'(\b[\w\-_./\\]+\.[a-zA-Z]{2,4})\b',  # Basic file paths
        r'([/\\]?[\w\-_./\\]+\.[a-zA-Z]{2,4})',  # Paths with slashes
    ]

    paths = []

    # Try quoted patterns first (more reliable)
    for pattern in quoted_patterns:
        matches = re.findall(pattern, query)
        paths.extend(matches)

    # If no quoted paths found, try unquoted patterns
    if not paths:
        for pattern in unquoted_patterns:
            matches = re.findall(pattern, query)
            # Filter out common false positives
            filtered_matches = [
                match for match in matches
                if not any(fp in match.lower() for fp in ['www.', 'http', '.com', '.org'])
            ]
            paths.extend(filtered_matches)

    # Clean and validate paths
    cleaned_paths = []
    for path in paths:
        cleaned_path = path.strip()
        if cleaned_path and len(cleaned_path) > 1:
            cleaned_paths.append(cleaned_path)

    return list(set(cleaned_paths))  # Remove duplicates


def validate_file_paths(paths: List[str]) -> Dict[str, List[str]]:
    """
    Validate file paths and categorize them
    
    Args:
        paths: List of file paths to validate
        
    Returns:
        Dictionary with valid, invalid, and supported paths
    """
    valid_paths = []
    invalid_paths = []
    supported_extensions = {'.pdf', '.txt', '.epub', '.md', '.docx'}

    for path in paths:
        path_obj = Path(path)

        if path_obj.exists():
            if path_obj.suffix.lower() in supported_extensions:
                valid_paths.append(str(path_obj))
            else:
                invalid_paths.append(f"{path} (unsupported format)")
        else:
            invalid_paths.append(f"{path} (file not found)")

    return {
        "valid": valid_paths,
        "invalid": invalid_paths,
        "supported_extensions": list(supported_extensions)
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def sanitize_memory_name(name: str) -> str:
    """Sanitize memory name for file system compatibility"""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Strip leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Limit length
    if len(sanitized) > 50:
        sanitized = sanitized[:50]

    return sanitized or "memory"


def generate_memory_name(documents: List[str] = None) -> str:
    """Generate a descriptive memory name based on documents"""
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if documents and len(documents) == 1:
        # Use document name if single file
        doc_name = Path(documents[0]).stem
        return sanitize_memory_name(f"{doc_name}_{timestamp}")
    elif documents and len(documents) > 1:
        # Use generic name for multiple files
        return f"documents_{timestamp}"
    else:
        return f"memory_{timestamp}"


def extract_directory_from_query(query: str) -> Optional[str]:
    """Extract directory path from user query"""
    # Look for directory patterns
    directory_patterns = [
        r'"([^"]+/)"',  # Quoted directory ending with /
        r"'([^']+/)'",  # Single quoted directory
        r'([/\\]?[\w\-_.]+[/\\])',  # Unquoted directory path
    ]

    for pattern in directory_patterns:
        matches = re.findall(pattern, query)
        if matches:
            return matches[0]

    return None


def scan_directory_for_documents(directory: str) -> List[str]:
    """Scan directory for supported document files"""
    supported_extensions = {'.pdf', '.txt', '.epub', '.md', '.docx'}
    documents = []

    try:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            for file_path in dir_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    documents.append(str(file_path))
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")

    return documents


def parse_query_intent(query: str) -> Dict[str, Any]:
    """
    Parse user query to determine intent and extract relevant information
    
    Args:
        query: User input string
        
    Returns:
        Dictionary with intent and extracted information
    """
    query_lower = query.lower()

    # Intent detection patterns
    ingestion_patterns = [
        'ingest', 'add', 'load', 'import', 'process', 'index',
        'upload', 'include', 'incorporate'
    ]

    search_patterns = [
        'search', 'find', 'what', 'how', 'when', 'where', 'why',
        'explain', 'describe', 'tell me', 'show me'
    ]

    management_patterns = [
        'list', 'show', 'stats', 'statistics', 'status',
        'manage', 'delete', 'remove', 'clear'
    ]

    # Check for document paths
    document_paths = extract_document_paths(query)
    directory_path = extract_directory_from_query(query)

    # Determine intent
    intent = "chat"  # default

    if any(pattern in query_lower for pattern in ingestion_patterns) or document_paths or directory_path:
        intent = "ingest"
    elif any(pattern in query_lower for pattern in management_patterns):
        intent = "manage"
    elif any(pattern in query_lower for pattern in search_patterns):
        intent = "search"

    return {
        "intent": intent,
        "document_paths": document_paths,
        "directory_path": directory_path,
        "original_query": query
    }


def create_ingestion_summary(stats: Dict[str, Any], memory_name: str) -> str:
    """Create a user-friendly summary of document ingestion"""
    processed = stats.get("processed", 0)
    failed = stats.get("failed", 0)
    total_chunks = stats.get("total_chunks", 0)
    video_size = stats.get("video_size_mb", 0)

    summary = f"✅ Successfully created memory '{memory_name}'\n\n"
    summary += f"📊 **Statistics:**\n"
    summary += f"• Processed files: {processed}\n"
    summary += f"• Failed files: {failed}\n"
    summary += f"• Total text chunks: {total_chunks}\n"
    summary += f"• Video memory size: {video_size:.1f} MB\n\n"
    summary += f"🔍 You can now search this memory by asking questions about the content."

    return summary


def format_search_results(chunks: List[Dict[str, Any]], query: str) -> str:
    """Format search results for display"""
    if not chunks:
        return f"❌ No relevant content found for: '{query}'"

    result = f"🔍 **Search Results for:** '{query}'\n\n"

    for i, chunk in enumerate(chunks[:3], 1):  # Show top 3 results
        text = chunk.get("text", "")[
            :200] + "..." if len(chunk.get("text", "")) > 200 else chunk.get("text", "")
        score = chunk.get("score", 0)
        source = chunk.get("source_memory", "unknown")

        result += f"**Result {i}** (Score: {score:.3f}, Source: {source})\n"
        result += f"{text}\n\n"

    return result
