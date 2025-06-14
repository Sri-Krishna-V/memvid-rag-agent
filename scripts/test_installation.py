#!/usr/bin/env python3
"""
Installation and setup verification script for Memvid RAG Agent
"""

import sys
import os
import importlib
from pathlib import Path
from typing import Dict, List, Tuple


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def check_python_version() -> bool:
    """Check if Python version is compatible"""
    print_section("Python Version Check")

    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 9:
        print("✅ Python version is compatible (3.9+)")
        return True
    else:
        print("❌ Python version is not compatible. Requires Python 3.9 or higher")
        return False


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required dependencies are installed"""
    print_section("Dependency Check")

    # Core dependencies
    required_packages = [
        "langgraph",
        "langchain_core",
        "langchain",
        "memvid",
        "langchain_openai",
        "langchain_anthropic",
        "langchain_google_genai",
        "PyPDF2",
        "faiss",
        "sentence_transformers",
        "cv2",
        "numpy",
        "pandas",
        "dotenv",
        "pydantic"
    ]

    # Alternative package names for some modules
    package_mapping = {
        "cv2": "opencv-python",
        "dotenv": "python-dotenv",
        "PyPDF2": "PyPDF2"
    }

    installed = []
    missing = []

    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
            installed.append(package)
        except ImportError:
            actual_name = package_mapping.get(package, package)
            print(f"❌ {package} (install with: pip install {actual_name})")
            missing.append(actual_name)

    success = len(missing) == 0
    return success, missing


def check_api_keys() -> Dict[str, bool]:
    """Check for API key configuration"""
    print_section("API Key Configuration")

    # Try to load from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not available, checking environment variables only")

    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY")
    }

    configured_keys = {}
    for key_name, key_value in api_keys.items():
        if key_value and key_value.strip():
            print(f"✅ {key_name} configured")
            configured_keys[key_name] = True
        else:
            print(f"❌ {key_name} not found")
            configured_keys[key_name] = False

    if any(configured_keys.values()):
        print(f"\n✅ At least one API key is configured")
        return configured_keys
    else:
        print(f"\n❌ No API keys configured. Please set up at least one in .env file")
        return configured_keys


def test_memvid_basic_functionality():
    """Test basic Memvid functionality"""
    print_section("Memvid Basic Functionality Test")

    try:
        from memvid import MemvidEncoder, MemvidRetriever

        # Test encoder initialization
        encoder = MemvidEncoder()
        print("✅ MemvidEncoder initialized successfully")

        # Test adding simple text
        test_chunks = [
            "This is a test document about artificial intelligence.",
            "Machine learning is a subset of AI that focuses on algorithms.",
            "Neural networks are inspired by biological neural networks."
        ]

        encoder.add_chunks(test_chunks)
        print("✅ Text chunks added successfully")

        # Test video creation (in memory, not saved)
        temp_dir = Path("./temp_test")
        temp_dir.mkdir(exist_ok=True)

        video_path = temp_dir / "test_memory.mp4"
        index_path = temp_dir / "test_index.json"

        encoder.build_video(str(video_path), str(index_path))
        print("✅ Video memory created successfully")

        # Test retriever
        retriever = MemvidRetriever(str(video_path), str(index_path))
        print("✅ MemvidRetriever initialized successfully")

        # Test search
        results = retriever.search("artificial intelligence", top_k=2)
        if results:
            print(f"✅ Search successful. Found {len(results)} results")
        else:
            print("⚠️  Search returned no results")

        # Clean up
        if video_path.exists():
            video_path.unlink()
        if index_path.exists():
            index_path.unlink()
        temp_dir.rmdir()

        print("✅ Memvid basic functionality test passed")
        return True

    except Exception as e:
        print(f"❌ Memvid functionality test failed: {str(e)}")
        return False


def test_langgraph_functionality():
    """Test basic LangGraph functionality"""
    print_section("LangGraph Basic Functionality Test")

    try:
        from langgraph.graph import StateGraph, END, START
        from typing_extensions import TypedDict

        # Define a simple state
        class TestState(TypedDict):
            message: str
            count: int

        # Create a simple workflow
        workflow = StateGraph(TestState)

        def test_node(state):
            return {"message": "LangGraph test", "count": state.get("count", 0) + 1}

        workflow.add_node("test_node", test_node)
        workflow.set_entry_point("test_node")
        workflow.add_edge("test_node", END)

        app = workflow.compile()

        # Test execution
        result = app.invoke({"message": "", "count": 0})

        if result["message"] == "LangGraph test" and result["count"] == 1:
            print("✅ LangGraph basic functionality test passed")
            return True
        else:
            print("❌ LangGraph test failed - unexpected result")
            return False

    except Exception as e:
        print(f"❌ LangGraph functionality test failed: {str(e)}")
        return False


def test_agent_initialization():
    """Test agent initialization without API calls"""
    print_section("Agent Initialization Test")

    try:
        # Set a dummy API key for testing
        os.environ["OPENAI_API_KEY"] = "test-key-for-initialization"

        from memvid_rag.agent import MemvidRAGAgent

        # Test initialization (should not make API calls)
        agent = MemvidRAGAgent()
        print("✅ MemvidRAGAgent initialized successfully")

        # Test basic properties
        assert hasattr(agent, 'active_memories')
        assert hasattr(agent, 'memory_storage_path')
        assert hasattr(agent, 'llm')
        print("✅ Agent has required attributes")

        # Test memory storage path creation
        assert agent.memory_storage_path.exists()
        print("✅ Memory storage path created")

        return True

    except Exception as e:
        print(f"❌ Agent initialization test failed: {str(e)}")
        return False


def check_project_structure():
    """Check if project structure is correct"""
    print_section("Project Structure Check")

    required_files = [
        "requirements.txt",
        "langgraph.json",
        ".env.example",
        "memvid_rag/__init__.py",
        "memvid_rag/agent.py",
        "memvid_rag/config.py",
        "memvid_rag/utils/__init__.py",
        "memvid_rag/utils/state.py",
        "memvid_rag/utils/nodes.py",
        "memvid_rag/utils/tools.py"
    ]

    required_dirs = [
        "memvid_rag",
        "memvid_rag/utils",
        "scripts",
        "memories"
    ]

    missing_files = []
    missing_dirs = []

    # Check files
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")

    # Check directories
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✅ {dir_path}/")

    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")

    if missing_dirs:
        print(f"\n❌ Missing directories: {', '.join(missing_dirs)}")

    return len(missing_files) == 0 and len(missing_dirs) == 0


def provide_next_steps(results: Dict[str, bool]):
    """Provide guidance based on test results"""
    print_section("Next Steps")

    if all(results.values()):
        print("🎉 All tests passed! Your Memvid RAG Agent is ready to use.")
        print("\n📚 To get started:")
        print("1. Configure your API keys in .env file")
        print("2. Run: python scripts/interactive_chat.py")
        print("3. Try: python scripts/example_usage.py")
        print("4. Or use: langgraph dev (for web interface)")

    else:
        print("⚠️  Some issues need to be resolved:")

        if not results.get("python_version", True):
            print("\n🔧 Python Version:")
            print("   - Install Python 3.9 or higher")
            print("   - Use pyenv or conda to manage Python versions")

        if not results.get("dependencies", True):
            print("\n🔧 Dependencies:")
            print("   - Run: pip install -r requirements.txt")
            print("   - If issues persist, try: pip install --upgrade pip")

        if not results.get("api_keys", True):
            print("\n🔧 API Keys:")
            print("   - Copy .env.example to .env")
            print("   - Add your API keys to .env file")
            print("   - Get keys from: OpenAI, Anthropic, or Google AI Studio")

        if not results.get("memvid", True):
            print("\n🔧 Memvid:")
            print("   - Check OpenCV installation: pip install opencv-python")
            print("   - Try: pip install --upgrade memvid")

        if not results.get("project_structure", True):
            print("\n🔧 Project Structure:")
            print("   - Ensure all files were created properly")
            print("   - Check file permissions")


def main():
    """Run all tests and provide summary"""
    print_header("Memvid RAG Agent - Installation Verification")
    print("This script will verify your installation and configuration.")

    results = {}

    # Run all checks
    results["python_version"] = check_python_version()
    results["dependencies"], missing_deps = check_dependencies()
    results["api_keys"] = any(check_api_keys().values())
    results["project_structure"] = check_project_structure()
    results["memvid"] = test_memvid_basic_functionality()
    results["langgraph"] = test_langgraph_functionality()
    results["agent"] = test_agent_initialization()

    # Print summary
    print_header("Test Summary")

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if missing_deps:
        print(f"\nMissing dependencies:")
        print("pip install " + " ".join(missing_deps))

    # Provide guidance
    provide_next_steps(results)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
