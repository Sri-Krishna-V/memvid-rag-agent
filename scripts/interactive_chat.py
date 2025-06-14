#!/usr/bin/env python3
"""
Interactive chat interface for Memvid RAG Agent
"""

import asyncio
import sys
import os
from pathlib import Path
import signal

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


class InteractiveChat:
    """Interactive chat interface for the RAG agent"""

    def __init__(self):
        self.agent = None
        self.session_id = "interactive_session"
        self.running = True

        # Set up signal handler for graceful exit
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n👋 Goodbye!")
        self.running = False
        sys.exit(0)

    def print_banner(self):
        """Print welcome banner"""
        print("=" * 70)
        print("🎥 MEMVID RAG AGENT - Interactive Chat")
        print("=" * 70)
        print("Video-based Knowledge Storage & Retrieval with LangGraph")
        print("")
        print("Commands:")
        print("  /help     - Show this help message")
        print("  /stats    - Show memory statistics")
        print("  /list     - List loaded memories")
        print("  /quit     - Exit the chat")
        print("  /clear    - Clear conversation history")
        print("")
        print("Example queries:")
        print('  Add "document.pdf" to memory')
        print('  What is machine learning?')
        print('  Process files in "documents/" folder')
        print("=" * 70)

    def initialize_agent(self):
        """Initialize the RAG agent with error handling"""
        try:
            print("🔧 Initializing Memvid RAG Agent...")

            # Check available providers
            providers = get_available_providers()
            if not providers:
                print("❌ No API keys found!")
                print("Please configure at least one API key in .env file:")
                print("  - OPENAI_API_KEY")
                print("  - ANTHROPIC_API_KEY")
                print("  - GOOGLE_API_KEY")
                return False

            print(f"✅ Available LLM providers: {', '.join(providers)}")

            # Initialize agent
            self.agent = MemvidRAGAgent(
                llm_provider=providers[0],  # Use first available
                debug=False
            )

            print(f"✅ Agent initialized with {self.agent.llm_provider}")

            # Show memory info
            stats = self.agent.get_memory_stats()
            if stats["total_memories"] > 0:
                print(
                    f"📁 Loaded {stats['total_memories']} existing memories ({stats['total_size_mb']:.1f} MB)")
            else:
                print("📁 No existing memories found. Add documents to get started!")

            return True

        except Exception as e:
            print(f"❌ Error initializing agent: {e}")
            print("\nTroubleshooting:")
            print("1. Run: python scripts/test_installation.py")
            print("2. Check your .env file configuration")
            print("3. Ensure all dependencies are installed")
            return False

    def handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if command was handled."""
        command = user_input.lower().strip()

        if command == "/help":
            self.print_banner()
            return True

        elif command == "/quit" or command == "/exit":
            print("👋 Goodbye!")
            self.running = False
            return True

        elif command == "/clear":
            # Clear conversation history
            if self.session_id in self.agent.session_data:
                self.agent.session_data[self.session_id]["messages"] = []
            print("🧹 Conversation history cleared")
            return True

        elif command == "/stats":
            stats = self.agent.get_memory_stats()
            print(f"\n📊 Memory Statistics:")
            print(f"  Total memories: {stats['total_memories']}")
            print(f"  Total storage: {stats['total_size_mb']:.1f} MB")
            print(f"  Storage path: {stats['storage_path']}")

            if stats['memory_details']:
                print(f"\n  Memory details:")
                for name, details in stats['memory_details'].items():
                    if 'size_mb' in details:
                        print(f"    • {name}: {details['size_mb']} MB")
                    else:
                        print(
                            f"    • {name}: {details.get('error', 'unknown')}")
            return True

        elif command == "/list":
            memories = self.agent.list_memories()
            if memories:
                print(f"\n📁 Active Memories ({len(memories)}):")
                for i, memory in enumerate(memories, 1):
                    print(f"  {i}. {memory}")
            else:
                print("\n📁 No memories currently loaded")
                print("💡 Add documents with: Add \"document.pdf\" to memory")
            return True

        return False

    async def chat_loop(self):
        """Main chat loop"""
        print(f"\n💬 Chat started! Type /help for commands or /quit to exit")
        print(f"🤖 Using {self.agent.llm_provider} LLM")

        while self.running:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    if self.handle_command(user_input):
                        continue

                # Process query through agent
                print("🤖 Agent: ", end="", flush=True)

                try:
                    response = await self.agent.query(user_input, self.session_id)
                    print(response)

                except KeyboardInterrupt:
                    print("\n⏸️  Query interrupted")
                    continue

                except Exception as e:
                    print(f"\n❌ Error processing query: {e}")
                    print("💡 Try rephrasing your question or use /help for commands")

            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Goodbye!")
                break

            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Type /quit to exit or continue chatting")

    def run(self):
        """Run the interactive chat"""
        self.print_banner()

        if not self.initialize_agent():
            return False

        try:
            asyncio.run(self.chat_loop())
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")

        return True


def main():
    """Main entry point"""
    # Check if we're in the right directory
    if not Path("memvid_rag").exists():
        print("❌ Please run this script from the project root directory")
        print("Current directory:", os.getcwd())
        return False

    # Start interactive chat
    chat = InteractiveChat()
    return chat.run()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
