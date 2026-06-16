# Pillai Center AI Chatbot

This is a RAG-based AI Customer Support Chatbot for Pillai Center.  
It answers questions using content from pillaicenter.com and academy.pillaicenter.com.

---

## What This Project Does

- Scrapes content from Pillai Center websites
- Stores data in a vector database (FAISS)
- Answers user questions using Groq AI (Llama 3.3 70B)
- Has a floating chat widget on the website
- Can auto-update content daily

---

## Files Included

- `app.py` → Main FastAPI server
- `chatbot.py` → Chat logic + Groq integration
- `config.py` → Settings and configuration
- `scraper.py` → Scrapes website content
- `vector_store.py` → Creates vector database
- `scheduler.py` → Daily auto update
- `static/` → Contains chatbot.css and chatbot.js
- `templates/` → Contains index.html
- `requirements.txt` → Python packages list
- `data/` → Scraped website content
- `faiss_index/` → Vector database files

---

## How to Run Locally

1. Install required packages:
   ```bash
   pip install -r requirements.txt

   Create a .env file and add your Groq API key:  GROQ_API_KEY=your_groq_api_key_here

   Run the chatbot Bash  terminal :   python -m uvicorn app:app --reload --port 8000

   Open in browser: : http://localhost:8000

