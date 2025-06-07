# Memvid RAG Agent with LangGraph

A complete implementation of a Retrieval Augmented Generation (RAG) system using Memvid for video-based knowledge storage and LangGraph for stateful agent orchestration.

## 🎯 Features

- **Video-Based Knowledge Storage**: Uses Memvid to encode text chunks into MP4 videos for efficient storage and retrieval
- **Stateful Agent Orchestration**: Leverages LangGraph for complex conversation flows and document processing pipelines
- **Multi-LLM Support**: Compatible with OpenAI, Anthropic, and Google Gemini
- **Lightning-Fast Retrieval**: Sub-second semantic search across millions of text chunks
- **10x Storage Efficiency**: Video compression reduces memory footprint dramatically
- **Offline-First**: Works completely offline once videos are generated
- **Easy Document Ingestion**: Supports PDF, EPUB, and text files

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- At least 4GB RAM
- 2GB free disk space

### Installation

1. **Clone or create project directory**:
```bash
mkdir memvid-rag-project
cd memvid-rag-project
```

2. **Create virtual environment**:
```bash
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Test installation**:
```bash
python scripts/test_installation.py
```

### Basic Usage

1. **Start the agent**:
```python
from memvid_rag.agent import MemvidRAGAgent
import asyncio

async def main():
    agent = MemvidRAGAgent(
        llm_provider="openai",  # or "anthropic" or "google"
        memory_storage_path="./memories"
    )
    
    # Ingest documents
    response = await agent.query(
        'Please ingest the document "example.pdf"'
    )
    print(response)
    
    # Ask questions
    response = await agent.query(
        "What are the main topics in the document?"
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

2. **Using the interactive CLI**:
```bash
python scripts/interactive_chat.py
```

3. **Web interface** (optional):
```bash
langgraph dev
# Open http://localhost:8000 in browser
```

## 📁 Project Structure

```
memvid-rag-project/
├── memvid_rag/              # Main package
│   ├── __init__.py
│   ├── agent.py             # Main RAG agent implementation
│   ├── config.py            # Configuration management
│   ├── utils/               # Utility modules
│   │   ├── __init__.py
│   │   ├── state.py         # LangGraph state definitions
│   │   ├── nodes.py         # LangGraph node functions
│   │   └── tools.py         # Helper tools and functions
├── scripts/                 # Utility scripts
│   ├── test_installation.py # Installation verification
│   ├── interactive_chat.py  # CLI chat interface
│   └── example_usage.py     # Usage examples
├── memories/                # Storage for Memvid videos
├── demo_content/            # Sample documents for testing
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── test_integration.py
├── requirements.txt         # Python dependencies
├── langgraph.json          # LangGraph configuration
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# LLM Provider API Keys (choose one or more)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here

# Optional: LangSmith for debugging (recommended)
LANGSMITH_API_KEY=your-langsmith-key-here
LANGSMITH_PROJECT=memvid-rag-project
LANGSMITH_TRACING=true

# Optional: Custom storage paths
MEMVID_STORAGE_PATH=./memories
LOG_LEVEL=INFO
```

### Memvid Configuration

Customize Memvid settings in `memvid_rag/config.py`:

```python
MEMVID_CONFIG = {
    "chunk_size": 512,
    "overlap": 50,
    "embedding_model": "sentence-transformers/all-mpnet-base-v2",
    "video_fps": 30,
    "frame_size": 256,
    "index_type": "Flat"  # or "IVF" for large datasets
}
```

## 📖 Usage Examples

### Document Ingestion

```python
# Ingest PDF files
await agent.query('Ingest "research_paper.pdf" "manual.pdf"')

# Ingest text files
await agent.query('Add text file "notes.txt" to memory')

# Ingest from directory
await agent.query('Process all documents in "documents/" folder')
```

### Semantic Search

```python
# Simple questions
response = await agent.query("What is machine learning?")

# Complex queries
response = await agent.query(
    "Compare the approaches mentioned in the research paper"
)

# Memory management
response = await agent.query("Show memory statistics")
response = await agent.query("List all loaded memories")
```

### Advanced Features

```python
# Load existing memories
agent.load_existing_memories("./backup_memories")

# Get detailed statistics
stats = agent.get_memory_stats()
print(f"Total memories: {stats['total_memories']}")
print(f"Total chunks: {stats['total_chunks']}")

# Custom memory creation
result = await agent.ingest_documents(
    document_paths=["doc1.pdf", "doc2.txt"],
    memory_name="custom_memory_2024"
)
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Test installation
python scripts/test_installation.py

# Test with sample documents
python scripts/example_usage.py
```

## 🛠️ Development

### Adding New Features

1. **Add new nodes** in `memvid_rag/utils/nodes.py`
2. **Update state** in `memvid_rag/utils/state.py`
3. **Modify agent** in `memvid_rag/agent.py`
4. **Add tests** in `tests/`

### Custom LLM Providers

To add support for new LLM providers, extend the `_initialize_llm` method in `agent.py`:

```python
def _initialize_llm(self, provider: str, model_name: str = None):
    if provider == "your_provider":
        return YourProviderLLM(
            api_key=self.api_key,
            model=model_name or "default-model"
        )
    # ... existing providers
```

## 🔍 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure virtual environment is activated
2. **API Key Errors**: Check `.env` file configuration
3. **Memory Issues**: Reduce chunk size in config for large documents
4. **Video Processing Errors**: Install OpenCV dependencies

### Performance Optimization

- Use smaller chunk sizes (256-512) for faster processing
- Enable IVF indexing for datasets > 10,000 chunks
- Use SSD storage for video memories
- Increase frame rate (fps) for more compression

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = MemvidRAGAgent(debug=True)
```

## 📚 Documentation

- [Memvid Documentation](https://github.com/Olow304/memvid)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [API Reference](docs/api_reference.md)
- [Architecture Guide](docs/architecture.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Memvid](https://github.com/Olow304/memvid) - Revolutionary video-based AI memory
- [LangGraph](https://github.com/langchain-ai/langgraph) - Stateful agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework

## 📞 Support

For issues and questions:

- Create an issue in this repository
- Check the troubleshooting section
- Review the documentation

---

**Ready to revolutionize your knowledge management? Start building with Memvid RAG Agent!** 🚀