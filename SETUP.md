# Setup Instructions for Memvid RAG Agent

Complete step-by-step guide to set up the Memvid RAG Agent with LangGraph.

## 📋 Prerequisites

Before starting, ensure you have:

- **Python 3.9 or higher** (3.11+ recommended)
- **4GB+ RAM** (8GB+ recommended for large documents)
- **2GB+ free disk space**
- **Internet connection** (for initial setup and LLM API calls)

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Project Directory

```bash
mkdir memvid-rag-project
cd memvid-rag-project
```

### Step 2: Download Project Files

If you received this as a package, extract all files. If cloning from a repository:

```bash
git clone <repository-url> .
```

### Step 3: Set Up Python Environment

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure API Keys

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your preferred text editor
nano .env  # or code .env, vim .env, etc.
```

Add at least one API key:

```env
# Choose one or more providers
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here
```

### Step 6: Test Installation

```bash
python scripts/test_installation.py
```

If all tests pass, you're ready to go! 🎉

## 🔑 Getting API Keys

### OpenAI (ChatGPT)

1. Visit [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in to your account
3. Navigate to **API Keys** in your dashboard
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-`)
6. Add billing information if required

**Cost:** Pay-per-use, ~$0.01-0.03 per query

### Anthropic (Claude)

1. Visit [Anthropic Console](https://console.anthropic.com)
2. Sign up or log in to your account
3. Go to **API Keys** section
4. Click **"Create Key"**
5. Copy the key (starts with `sk-ant-`)
6. Add billing information

**Cost:** Pay-per-use, competitive pricing

### Google (Gemini)

1. Visit [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API key"**
4. Create a new project if needed
5. Generate and copy the API key
6. Some usage may be free initially

**Cost:** Generous free tier, then pay-per-use

## 📁 Project Structure Overview

After setup, your project should look like this:

```
memvid-rag-project/
├── 📄 README.md                    # Main documentation
├── 📄 requirements.txt             # Python dependencies
├── 📄 langgraph.json              # LangGraph configuration
├── 📄 .env.example                # Environment template
├── 📄 .env                        # Your API keys (created by you)
├── 📄 .gitignore                  # Git ignore rules
├── 📁 memvid_rag/                 # Main package
│   ├── 📄 __init__.py
│   ├── 📄 agent.py                # Main RAG agent
│   ├── 📄 config.py               # Configuration management
│   └── 📁 utils/                  # Utility modules
│       ├── 📄 __init__.py
│       ├── 📄 state.py            # LangGraph states
│       ├── 📄 nodes.py            # Processing nodes
│       └── 📄 tools.py            # Helper functions
├── 📁 scripts/                    # Utility scripts
│   ├── 📄 test_installation.py    # Installation tests
│   ├── 📄 interactive_chat.py     # Chat interface
│   └── 📄 example_usage.py        # Usage examples
├── 📁 tests/                      # Unit tests
├── 📁 memories/                   # Video storage (created automatically)
└── 📁 demo_content/               # Sample documents (created by scripts)
```

## 🧪 Testing Your Setup

### 1. Run Installation Tests

```bash
python scripts/test_installation.py
```

This checks:
- ✅ Python version compatibility
- ✅ All dependencies installed
- ✅ API keys configured
- ✅ Basic functionality

### 2. Try the Example Script

```bash
python scripts/example_usage.py
```

This will:
- Create sample documents
- Demonstrate document ingestion
- Show semantic search capabilities
- Test memory management

### 3. Interactive Chat

```bash
python scripts/interactive_chat.py
```

Start chatting with your agent!

## 🌐 Web Interface (Optional)

For a visual interface using LangGraph Studio:

### Install LangGraph CLI

```bash
pip install "langgraph-cli[inmem]"
```

### Start Development Server

```bash
langgraph dev
```

Open your browser to the provided URL (usually `http://localhost:8000`).

## 🛠️ Troubleshooting

### Common Issues

**❌ `ModuleNotFoundError: No module named 'memvid'`**

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**❌ `ImportError: No module named 'cv2'`**

```bash
pip install opencv-python
```

**❌ API Key Errors**

- Check `.env` file exists and has correct format
- Ensure no extra spaces around API keys
- Verify API key is valid and has billing set up

**❌ Memory/Performance Issues**

- Reduce chunk size in configuration
- Close other applications to free RAM
- Process smaller documents first

**❌ Permission Errors on Windows**

- Run command prompt as Administrator
- Or use: `python -m pip install --user package-name`

### Getting Help

1. **Check the logs**: Look for error messages in the console
2. **Run diagnostics**: `python scripts/test_installation.py`
3. **Try minimal example**: Start with simple text ingestion
4. **Check documentation**: README.md has detailed usage info

## ⚙️ Advanced Configuration

### Custom Storage Location

```bash
export MEMVID_STORAGE_PATH="/path/to/your/memories"
```

### Performance Tuning

Edit `.env` file:

```env
# For large documents
MEMVID_CHUNK_SIZE=1024
MEMVID_OVERLAP=100

# For better compression
MEMVID_VIDEO_FPS=60
MEMVID_FRAME_SIZE=512
```

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
```

### Multiple LLM Providers

Configure multiple API keys to switch between providers:

```env
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

## 🎯 Next Steps

Once setup is complete:

1. **📚 Read the README.md** for detailed usage examples
2. **🧪 Try example_usage.py** to see all features
3. **💬 Use interactive_chat.py** for real-time interaction
4. **📄 Add your own documents** to the memories folder
5. **🌐 Explore the web interface** with `langgraph dev`

## 📞 Support

If you encounter issues:

- Check this setup guide first
- Run the test installation script
- Review the troubleshooting section
- Look at example code for reference

## 🎉 Success!

If you've reached this point with all tests passing, congratulations! 

Your Memvid RAG Agent is ready to revolutionize how you store, search, and interact with your knowledge base using cutting-edge video-based storage technology.

Happy knowledge building! 🚀