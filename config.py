
import os
from pathlib import Path

# Base paths - support env override for Render persistent disk
BASE_DIR = Path(__file__).parent.resolve()

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
FAISS_DIR = Path(os.getenv("FAISS_DIR", BASE_DIR / "faiss_index"))

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)

# Data files
WEBSITE_DATA_FILE = DATA_DIR / "website_data.json"
FAISS_INDEX_FILE = FAISS_DIR / "index.faiss"
FAISS_METADATA_FILE = FAISS_DIR / "metadata.json"
SEEN_URLS_FILE = DATA_DIR / "seen_urls.json"

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_PAGE_CONTENT = 8000

# Embeddings
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# LLM
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.2
GROQ_MAX_TOKENS = 1024

# RAG
TOP_K = 5

# Sitemap sources
SITEMAPS = {
    "main": "https://www.pillaicenter.com/sitemap.xml",
    "academy": "https://academy.pillaicenter.com/sitemap_index.xml"
}

# URL filtering rules
INCLUDE_KEYWORDS = {
    "main": ["about", "teaching", "teachings", "free", "special", "blog"],
    "academy": ["event", "events", "shop", "about"]
}

EXCLUDE_PATTERNS = [
    "calendar", "lesson", "lessons", "login", "cart", "checkout", 
    "search", "account", "download", ".pdf", "wp-json", "wp-admin",
    "media", "video", "image", "wp-content/uploads"
]

# Headers for scraping
SCRAPE_HEADERS = {
    "User-Agent": "PillaiCenter-Bot/1.0[](https://www.pillaicenter.com)"
}

# System prompt for LLM
SYSTEM_PROMPT = """You are a helpful and friendly assistant for Pillai Center and Pillai Center Academy.

Rules for every response:
- Always reply in **clear bullet points**.
- Use short and simple sentences.
- If giving suggestions, make each point clear and easy to understand.
- If the user asks for health, spiritual, or teaching-related advice, structure the answer in bullet points.
- Never give long paragraphs.
- If you don’t have the information, say "Sorry, I could not find that information in the knowledge base" and then show 3-4 suggested questions as bullet points.
- Always be polite and helpful.
"""

# Chat history limit
MAX_HISTORY = 10

# Scheduler time (runs daily at 3 AM IST)
SCHEDULER_HOUR = 3
SCHEDULER_MINUTE = 0

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"