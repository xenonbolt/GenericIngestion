# Universal Agentic Intelligence Platform

Welcome to the **Universal Agentic Intelligence Platform**! 

This project is a powerful, ready-to-use AI assistant built using a **Multi-Agent Architecture** (via LangGraph). It is designed to be easily understandable for beginners while containing advanced, enterprise-grade features under the hood.

With this platform, you can chat with an intelligent agent, upload documents (PDFs, Images, Audio, Video, CSVs), automatically extract their metadata, and perform **Hybrid Searches** where the agent queries both structured relationships and unstructured semantic data to answer your questions.

---

## ✨ Features at a Glance

1. **Multimodal Ingestion**: Upload text, PDFs, Images, Audio, Video, and CSVs.
2. **AI Magic Auto-Fill**: Let Gemini's Vision/Audio models automatically read your files and generate Summaries, Categories, and Tags for you!
3. **Hybrid Search (Vector + Graph)**: 
   - *Structured data (CSVs)* is turned into an interactive knowledge graph.
   - *Unstructured data (PDFs/Images)* is split into text and stored in a vector database for semantic search. 
4. **Live Agent Trace**: See exactly what the AI agent is thinking and doing in real-time on a visual flowchart (React Flow).
5. **Dual-Layer Memory**: The bot remembers what you said just now (short-term) and learns facts about you forever (long-term using MongoDB).

---

## 🛠 Prerequisites (What you need installed)

If you are a beginner, make sure you download and install these three things before continuing:

1. **Python 3.10 or higher**: [Download Python here](https://www.python.org/downloads/). This runs the backend logic.
2. **Node.js (version 18+)**: [Download Node.js here](https://nodejs.org/). This runs the frontend website.
3. **MongoDB**: A database that runs on your computer to store the agent's memory.
   - *Linux (Ubuntu)*: Run `sudo apt install mongodb` in your terminal.
   - *Windows/Mac*: Download [MongoDB Community Server](https://www.mongodb.com/try/download/community).
   - **Important**: Make sure MongoDB is running! (On Linux: `sudo systemctl start mongod`).

---

## 🚀 Step-by-Step Setup Guide

### Step 1: Clone the Repository
Open a terminal and navigate to this project folder.

---

### Step 2: Configure Environment Variables (.env)
The backend needs a few secret keys to talk to the AI models. 
1. Navigate into the `backend` folder.
2. Open the file named `.env` in a text editor (create it if it doesn't exist).
3. Add your API keys. It should look like this:

```env
# Which AI provider to use: 'google' (Gemini) or 'openai' (GPT)
LLM_PROVIDER="google"

# Your API Keys (Get these from Google AI Studio or OpenAI Dashboard)
GEMINI_API_KEY="your-gemini-key-here"
OPENAI_API_KEY="your-openai-key-here"

# (Optional) Observability keys for tracking agent performance
POSTHOG_API_KEY=""
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_SECRET_KEY=""

# (Optional) Set to "true" to use native python audio/video extraction instead of Gemini
NATIVE_MEDIA_EXTRACTION="false"
```

---

### Step 3: Start the Python Backend Server
Keep your terminal open inside the `backend` folder and run the following commands:

```bash
# 1. Create a virtual environment (a safe bubble for Python packages)
python3 -m venv venv

# 2. Activate the virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 3. Install all required Python packages (this might take a minute!)
pip install -r requirements.txt

# 4. Start the backend server
uvicorn main:app --reload --port 8000
```
*Great! You should see text saying the server is running on `http://127.0.0.1:8000`. Leave this terminal window open.*

---

### Step 4: Start the React Frontend Website
Open a **new, second terminal window**, and navigate into the `frontend` directory of the project.

```bash
# 1. Install Node modules
npm install

# 2. Start the website
npm run dev
```
*You will see a link like `http://localhost:5173`. Click it or copy it into your web browser!*

---

## 📖 How to Use the Application

Once you open the website in your browser, here is how you interact with the platform:

### 1. Ingesting Knowledge (Uploading Files)
- Look at the top left of the chat window for a **Cloud Upload Icon**. Click it!
- A modal will pop up. Choose a file from your computer (e.g., a PDF report, a picture, or a CSV).
- **The Magic Wand**: Click the "Auto-Fill" button. The system will send your file to the AI, which will read it, write a short summary, pick a category, and generate tags—all automatically!
- Click **Ingest to Brain** to save it. 

### 2. Chatting & Intelligent Search
- Start typing in the chat box on the left.
- Ask questions about the files you uploaded (e.g., "Summarize the report I just uploaded" or "What does the graph say?").
- The **Multi-Agent System** goes to work:
  1. **Intent Analyzer**: Decides if it needs to search your uploaded files or just chat normally.
  2. **Retrieval Agent**: Searches the Vector database (ChromaDB) and the Knowledge Graph (NetworkX).
  3. **Relevance Evaluator**: Double-checks if the retrieved data actually answers your question!

### 3. Watching the AI Think (Live Trace)
- As you chat, look at the right side of the screen.
- You will see a visual flowchart drawing itself. This is the **Live Agent Trace**. It shows you exactly which "Node" the AI is currently thinking in (like checking memory, analyzing intent, or searching the database).

---

## 🏗 What's Happening Under the Hood? (For the Curious)

If you're wondering how this works technically:
- **LangGraph**: Used to orchestrate the AI agents. Instead of one AI trying to do everything, LangGraph splits tasks into smaller nodes (Intent -> Search -> Evaluate -> Respond).
- **ChromaDB**: A local Vector Database. When you upload PDFs or text, they are chopped into pieces, turned into math vectors, and saved here for lightning-fast semantic search.
- **NetworkX**: A Knowledge Graph. When you upload structured CSVs, rows are turned into interconnected nodes (e.g., `Company A` -> `buys` -> `Company B`).
- **WebSockets**: The backend pushes live updates to the React frontend through WebSockets, which is how the visual flowchart animates instantly!

---

## 🗺️ Deep Dive Walkthrough
Want to learn more about how the Multi-Agent Hybrid Search, Pandas Agent, and Langfuse Telemetry work? 
👉 **[Read the Full Technical Walkthrough Here](./Walkthrough.md)**
