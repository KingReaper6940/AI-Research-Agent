# 🔬 DeepResearch — AI-Powered Research Agent

An autonomous **multi-source deep research agent** built with **Retrieval-Augmented Generation (RAG)** patterns. Give it a complex question and it will decompose it into sub-queries, search across web, academic, and Wikipedia sources, evaluate credibility, and synthesize a comprehensive research report — all in real-time.

> Think of it as your own open-source **Perplexity Pro / Deep Research**.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-4285F4?logo=google&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **🧠 Query Decomposition** — Complex questions are automatically broken into targeted sub-queries
- **🔄 Iterative Deep-Dive** — Evaluates completeness, identifies gaps, and digs deeper automatically
- **🌐 Multi-Source Search** — Web (DuckDuckGo), Wikipedia, ArXiv, and Semantic Scholar
- **🛡️ Credibility Scoring** — Every source scored for reliability (domain reputation, source type, content quality)
- **⚠️ Contradiction Detection** — Flags when sources disagree
- **📝 Cited Reports** — Structured Markdown reports with inline citations and credibility badges
- **⚡ Real-Time Progress** — Live WebSocket feed showing research steps as they happen
- **🎨 Premium Web UI** — Dark-themed product website with glassmorphism design

## 🏗️ Architecture

```
User Query → Query Decomposer → Search Orchestrator
                                    ├── DuckDuckGo (Web)
                                    ├── Wikipedia
                                    ├── ArXiv (Academic)
                                    └── Semantic Scholar
                                         ↓
                                  Content Processor
                                         ↓
                                  Credibility Scorer
                                         ↓
                                  Agent Orchestrator ←──┐
                                    │                   │
                                    ├── Need more? ─────┘
                                    └── Done → Report Synthesizer → Markdown Report
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/KingReaper6940/AI-Research-Agent.git
cd AI-Research-Agent
pip install -r requirements.txt
```

### 2. Set Up API Key

Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey), then:

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

> **Free tier**: 15 requests/minute, 1M tokens/day — sufficient for research runs.

### 3. Run

```bash
python server.py
```

Open **http://localhost:8000** in your browser.

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Gemini 2.0 Flash |
| **Web Search** | DuckDuckGo |
| **Academic** | ArXiv API, Semantic Scholar API |
| **Context** | Wikipedia API |
| **Backend** | FastAPI + WebSocket |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Streaming** | WebSocket (real-time progress) |

## 📁 Project Structure

```
├── src/
│   ├── config.py        # Settings, API keys, credibility scores
│   ├── search.py        # Web + Wikipedia search
│   ├── academic.py      # ArXiv + Semantic Scholar
│   ├── processor.py     # Content cleaning & truncation
│   ├── decomposer.py    # LLM query decomposition
│   ├── credibility.py   # Source credibility scoring
│   ├── synthesizer.py   # Report generation with citations
│   └── agent.py         # Autonomous research orchestrator
├── static/              # Frontend (HTML/CSS/JS)
├── server.py            # FastAPI server
├── reports/             # Generated research reports
└── requirements.txt
```

## 💡 How It Works

1. **You ask a question** — e.g., *"What are the latest breakthroughs in nuclear fusion?"*
2. **Agent decomposes** — Breaks it into 3-5 targeted sub-queries
3. **Parallel search** — Searches DuckDuckGo, Wikipedia, ArXiv, and Semantic Scholar simultaneously
4. **Credibility filter** — Scores each source (-1 to 1) and filters low-quality results
5. **Completeness check** — Evaluates if the research covers all aspects
6. **Iterative loop** — If gaps exist, generates follow-up queries and searches again (up to 3 iterations)
7. **Synthesis** — Produces a structured Markdown report with inline citations

## 📄 License

MIT License — feel free to use, modify, and distribute.