
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config import (
    WEBSITE_DATA_FILE, FAISS_INDEX_FILE, FAISS_METADATA_FILE,
    CHUNK_SIZE, CHUNK_OVERLAP, EMBED_MODEL_NAME, TOP_K
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | vector_store | %(message)s")
logger = logging.getLogger(__name__)

_embed_model = None


def get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        logger.info(f"Loading embedding model: {EMBED_MODEL_NAME}")
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME, device="cpu")
    return _embed_model


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    if not text or len(text) < 50:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_website_data() -> List[Dict]:
    if not WEBSITE_DATA_FILE.exists():
        logger.error("website_data.json not found. Run scraper.py first!")
        return []
    with open(WEBSITE_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_chunks_from_data(data: List[Dict]) -> Tuple[List[str], List[Dict]]:
    all_chunks = []
    all_metadata = []

    for page in tqdm(data, desc="Chunking pages"):
        chunks = chunk_text(page.get("content", ""))
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "url": page.get("url", ""),
                "title": page.get("title", ""),
                "chunk_index": i,
                "chunk_text": chunk
            })
    logger.info(f"Created {len(all_chunks)} chunks")
    return all_chunks, all_metadata


def create_faiss_index(chunks: List[str], metadata: List[Dict]) -> Tuple[faiss.Index, List[Dict]]:
    model = get_embed_model()
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    
    embeddings = model.encode(
        chunks,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype(np.float32))
    logger.info(f"FAISS index created with {index.ntotal} vectors")
    return index, metadata


def save_index(index: faiss.Index, metadata: List[Dict]):
    FAISS_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_FILE))
    
    with open(FAISS_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    logger.info("FAISS index and metadata saved successfully")


def load_index() -> Optional[Tuple[faiss.Index, List[Dict]]]:
    if not (FAISS_INDEX_FILE.exists() and FAISS_METADATA_FILE.exists()):
        return None
    try:
        index = faiss.read_index(str(FAISS_INDEX_FILE))
        with open(FAISS_METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors")
        return index, metadata
    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        return None


def search_similar(query: str, top_k: int = TOP_K) -> List[Dict]:
    loaded = load_index()
    if loaded is None:
        logger.error("FAISS index not found. Run vector_store.py first!")
        return []

    index, metadata = loaded
    if index.ntotal == 0:
        return []

    model = get_embed_model()
    query_vec = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)

    scores, indices = index.search(query_vec, min(top_k, index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1 or idx >= len(metadata):
            continue
        meta = metadata[idx]
        results.append({
            "score": float(score),
            "url": meta.get("url", ""),
            "title": meta.get("title", ""),
            "chunk_text": meta.get("chunk_text", "")
        })
    return results


def build_or_load_index(force_rebuild: bool = False):
    if not force_rebuild:
        loaded = load_index()
        if loaded:
            return loaded

    logger.info("Building new FAISS index...")
    data = load_website_data()
    if not data:
        raise RuntimeError("No data found. Run scraper.py first!")

    chunks, metadata = build_chunks_from_data(data)
    index, metadata = create_faiss_index(chunks, metadata)
    save_index(index, metadata)
    return index, metadata


if __name__ == "__main__":
    print("Building vector index...")
    build_or_load_index()
    print("Vector index ready!")