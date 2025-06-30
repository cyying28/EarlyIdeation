# mapsAIReview

# AI-Powered Restaurant Review Analysis System

An intelligent Chrome extension that scrapes Google Maps restaurant reviews and provides AI-powered analysis using RAG (Retrieval-Augmented Generation) technology.

## Prerequisites

- **Python 3.8+**
- **Google Chrome** browser
- **API Keys** from:
  - [Scrapingdog](https://scrapingdog.com/) (for review scraping)
  - [OpenAI](https://platform.openai.com/api-keys) (for AI analysis)
  - [Cohere](https://dashboard.cohere.ai/api-keys) (for embeddings - free tier available)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd mapsAIReview
pip install -r requirements.txt
```

### 2. Create Environment File

Create a `.env` file in the `mapsAIReview/` directory:

```env
# Scrapingdog API Key (for scraping Google Maps reviews)
# Get from: https://scrapingdog.com/
DOG_KEY=your_scrapingdog_api_key_here

# OpenAI API Key (for GPT analysis)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Cohere API Key (for text embeddings)
# Get from: https://dashboard.cohere.ai/api-keys (free tier available)
COHERE_API_KEY=your_cohere_api_key_here
```

### 3. Start the Server

```bash
python extension_server.py
```

### 4. Install Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **"Developer mode"** (toggle in top right)
3. Click **"Load unpacked"**
4. Select the `chrome-extension` folder from this project
5. Extension icon should appear in Chrome toolbar

### 5. Use the System

1. **Navigate to any restaurant** on Google Maps
2. **Click the extension icon** in Chrome toolbar
3. **Ask questions** like:
   - "How is the food quality?"
   - "What's the service like?"
   - "Is it good for families?"
   - "What are the best dishes?"
4. **Get AI-powered insights** based on actual customer reviews!
