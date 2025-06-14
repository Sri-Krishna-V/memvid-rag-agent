#!/usr/bin/env python3
"""
Example usage script for Memvid RAG Agent
"""

import asyncio
import sys
import os
from pathlib import Path
import tempfile

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from memvid_rag.agent import MemvidRAGAgent
    from memvid_rag.config import get_available_providers
except ImportError as e:
    print(f"❌ Error importing Memvid RAG Agent: {e}")
    print("Make sure you're running from the project root directory.")
    sys.exit(1)


def create_sample_documents():
    """Create sample documents for testing"""
    print("📝 Creating sample documents...")

    # Create demo_content directory
    demo_dir = Path("demo_content")
    demo_dir.mkdir(exist_ok=True)

    # Sample document 1: AI Overview
    ai_doc = demo_dir / "ai_overview.txt"
    ai_content = """Artificial Intelligence (AI) Overview

Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that can think and learn like humans. AI has become increasingly important in our daily lives and various industries.

Key Areas of AI:

1. Machine Learning (ML)
   - Supervised Learning: Learning from labeled data
   - Unsupervised Learning: Finding patterns in unlabeled data
   - Reinforcement Learning: Learning through trial and error

2. Natural Language Processing (NLP)
   - Text analysis and understanding
   - Language translation
   - Chatbots and conversational AI

3. Computer Vision
   - Image recognition and classification
   - Object detection
   - Medical imaging analysis

4. Robotics
   - Autonomous vehicles
   - Industrial automation
   - Service robots

Applications of AI:
- Healthcare: Diagnostic assistance, drug discovery
- Finance: Fraud detection, algorithmic trading
- Transportation: Autonomous vehicles, traffic optimization
- Entertainment: Recommendation systems, content generation
- Manufacturing: Quality control, predictive maintenance

AI Ethics and Considerations:
- Bias and fairness in AI systems
- Privacy and data protection
- Job displacement concerns
- Transparency and explainability
- Safety and security of AI systems

The future of AI holds great promise for solving complex problems and improving human life, but it also requires careful consideration of ethical implications and responsible development.
"""

    ai_doc.write_text(ai_content)

    # Sample document 2: Python Programming
    python_doc = demo_dir / "python_guide.txt"
    python_content = """Python Programming Guide

Python is a high-level, interpreted programming language known for its simplicity and readability. It has become one of the most popular programming languages worldwide.

Key Features of Python:

1. Simple and Easy to Learn
   - Clean and readable syntax
   - Minimal code required for tasks
   - Great for beginners and experts alike

2. Versatile and Powerful
   - Object-oriented programming support
   - Functional programming capabilities
   - Extensive standard library

3. Cross-platform Compatibility
   - Runs on Windows, macOS, Linux
   - Same code works across different platforms
   - Write once, run anywhere philosophy

Popular Python Libraries:

Data Science and AI:
- NumPy: Numerical computing
- Pandas: Data manipulation and analysis
- Matplotlib: Data visualization
- Scikit-learn: Machine learning
- TensorFlow/PyTorch: Deep learning

Web Development:
- Django: Full-featured web framework
- Flask: Lightweight web framework
- FastAPI: Modern API development

Automation and Scripting:
- Requests: HTTP library
- Beautiful Soup: Web scraping
- Selenium: Browser automation

Python Applications:
- Web development and APIs
- Data analysis and visualization
- Machine learning and AI
- Automation and scripting
- Scientific computing
- Game development
- Desktop applications

Best Practices:
- Follow PEP 8 style guide
- Use virtual environments
- Write clear documentation
- Test your code
- Use version control (Git)
- Handle exceptions properly

Python's philosophy: "Simple is better than complex" and "Readability counts" make it an excellent choice for both beginners and experienced developers.
"""

    python_doc.write_text(python_content)

    # Sample document 3: Data Science
    ds_doc = demo_dir / "data_science.txt"
    ds_content = """Data Science Fundamentals

Data Science is an interdisciplinary field that combines statistics, computer science, and domain expertise to extract insights from data. It has become crucial in today's data-driven world.

The Data Science Process:

1. Data Collection
   - Gathering data from various sources
   - APIs, databases, web scraping
   - Surveys and experiments

2. Data Cleaning and Preprocessing
   - Handling missing values
   - Removing outliers
   - Data normalization and standardization
   - Feature engineering

3. Exploratory Data Analysis (EDA)
   - Statistical summaries
   - Data visualization
   - Pattern identification
   - Hypothesis generation

4. Modeling and Analysis
   - Statistical modeling
   - Machine learning algorithms
   - Model selection and validation
   - Performance evaluation

5. Communication and Deployment
   - Results interpretation
   - Visualization and reporting
   - Model deployment
   - Monitoring and maintenance

Essential Skills for Data Scientists:

Technical Skills:
- Programming (Python, R, SQL)
- Statistics and probability
- Machine learning algorithms
- Data visualization
- Big data technologies

Soft Skills:
- Critical thinking
- Problem-solving
- Communication
- Business acumen
- Curiosity and continuous learning

Common Data Science Tools:
- Python: Pandas, NumPy, Scikit-learn
- R: ggplot2, dplyr, caret
- SQL: Data querying and manipulation
- Tableau/Power BI: Data visualization
- Jupyter Notebooks: Interactive development
- Git: Version control

Industry Applications:
- Healthcare: Predictive analytics, drug discovery
- Finance: Risk assessment, fraud detection
- Marketing: Customer segmentation, recommendation systems
- Technology: A/B testing, user behavior analysis
- Sports: Performance analytics, strategy optimization

The field of data science continues to evolve with new technologies and methodologies, making it an exciting and dynamic career path.
"""

    ds_doc.write_text(ds_content)

    return [str(ai_doc), str(python_doc), str(ds_doc)]


async def demo_basic_usage():
    """Demonstrate basic agent usage"""
    print("🎯 Demo 1: Basic Agent Initialization and Usage")
    print("-" * 50)

    # Check available providers
    providers = get_available_providers()
    if not providers:
        print("❌ No API keys configured. Please set up .env file first.")
        return False

    try:
        # Initialize agent
        print(f"🔧 Initializing agent with {providers[0]} provider...")
        agent = MemvidRAGAgent(
            llm_provider=providers[0],
            memory_storage_path="./memories"
        )

        print(f"✅ Agent initialized successfully!")
        print(f"   Provider: {agent.llm_provider}")
        print(f"   Storage: {agent.memory_storage_path}")

        # Show initial stats
        stats = agent.get_memory_stats()
        print(f"   Existing memories: {stats['total_memories']}")

        return agent

    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        return None


async def demo_document_ingestion(agent: MemvidRAGAgent):
    """Demonstrate document ingestion"""
    print("\n🎯 Demo 2: Document Ingestion")
    print("-" * 50)

    try:
        # Create sample documents
        sample_docs = create_sample_documents()
        print(f"✅ Created {len(sample_docs)} sample documents")

        # Ingest documents
        print("📥 Ingesting documents into memory...")

        # Method 1: Using the query interface
        docs_str = " ".join(f'"{doc}"' for doc in sample_docs)
        response = await agent.query(f"Please ingest these documents: {docs_str}")

        print("📋 Ingestion Response:")
        print(response)

        # Show updated stats
        stats = agent.get_memory_stats()
        print(f"\n📊 Updated Stats:")
        print(f"   Total memories: {stats['total_memories']}")
        print(f"   Total storage: {stats['total_size_mb']:.1f} MB")

        return True

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return False


async def demo_semantic_search(agent: MemvidRAGAgent):
    """Demonstrate semantic search capabilities"""
    print("\n🎯 Demo 3: Semantic Search and Q&A")
    print("-" * 50)

    # Sample queries to demonstrate different capabilities
    queries = [
        "What is machine learning?",
        "Tell me about Python programming features",
        "What are the steps in the data science process?",
        "How is AI used in healthcare?",
        "What Python libraries are good for data science?",
        "Compare supervised and unsupervised learning",
    ]

    try:
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Query {i}: {query}")
            print("🤖 Response:")

            response = await agent.query(query)
            print(response)

            # Add a small delay for readability
            await asyncio.sleep(1)

        return True

    except Exception as e:
        print(f"❌ Error during search demo: {e}")
        return False


async def demo_memory_management(agent: MemvidRAGAgent):
    """Demonstrate memory management features"""
    print("\n🎯 Demo 4: Memory Management")
    print("-" * 50)

    try:
        # List memories
        print("📋 Listing memories...")
        response = await agent.query("list memories")
        print(response)

        # Show statistics
        print("\n📊 Memory statistics...")
        response = await agent.query("show statistics")
        print(response)

        # Get programmatic stats
        stats = agent.get_memory_stats()
        print(f"\n🔧 Programmatic Stats:")
        print(f"   Memories: {list(stats['memory_details'].keys())}")

        return True

    except Exception as e:
        print(f"❌ Error in memory management demo: {e}")
        return False


async def demo_advanced_features(agent: MemvidRAGAgent):
    """Demonstrate advanced features"""
    print("\n🎯 Demo 5: Advanced Features")
    print("-" * 50)

    try:
        # Test conversation context
        print("🗣️ Testing conversation context...")

        await agent.query("What programming languages did we discuss?")

        # Test follow-up questions
        print("\n❓ Follow-up question...")
        response = await agent.query("What are its main applications?")
        print(f"🤖 Response: {response}")

        # Test complex queries
        print("\n🧠 Complex query...")
        response = await agent.query(
            "Create a comparison table of machine learning types mentioned in the documents"
        )
        print(f"🤖 Response: {response}")

        return True

    except Exception as e:
        print(f"❌ Error in advanced features demo: {e}")
        return False


def print_summary():
    """Print demo summary and next steps"""
    print("\n" + "=" * 70)
    print("🎉 DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\n✅ What you've learned:")
    print("  • How to initialize the Memvid RAG Agent")
    print("  • Document ingestion into video-based memory")
    print("  • Semantic search and question answering")
    print("  • Memory management operations")
    print("  • Advanced conversation features")

    print("\n🚀 Next steps:")
    print("  • Try the interactive chat: python scripts/interactive_chat.py")
    print("  • Add your own documents to the memories/ folder")
    print("  • Explore the web interface: langgraph dev")
    print("  • Check out the README.md for more advanced usage")

    print("\n📁 Generated files:")
    print("  • demo_content/: Sample documents")
    print("  • memories/: Video-based knowledge storage")

    print("\n💡 Tips:")
    print("  • Video memories are portable - copy .mp4 and .json files")
    print("  • Search works across all loaded memories simultaneously")
    print("  • Use specific queries for better results")


async def main():
    """Main demo function"""
    print("🎥 MEMVID RAG AGENT - COMPLETE DEMO")
    print("=" * 70)
    print("This demo will showcase all features of the Memvid RAG Agent.")
    print("Make sure you have configured API keys in .env file.")
    print("=" * 70)

    # Run demos in sequence
    agent = await demo_basic_usage()
    if not agent:
        return False

    success = await demo_document_ingestion(agent)
    if not success:
        return False

    success = await demo_semantic_search(agent)
    if not success:
        return False

    success = await demo_memory_management(agent)
    if not success:
        return False

    success = await demo_advanced_features(agent)
    if not success:
        return False

    print_summary()
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)
