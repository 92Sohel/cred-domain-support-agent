"""Two local retrieval collections. Uses deterministic token cosine in MOCK_LLM mode.

The collection contract intentionally mirrors Chroma's upsert/query boundary, so a
SentenceTransformers+Chroma adapter can replace LocalCollection without changing callers.
"""
from __future__ import annotations
from collections import Counter
import json, math, re
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = ROOT / "knowledge_base" / "policies.json"
TOKEN = re.compile(r"[a-zA-Z]{2,}")
STOP_WORDS = {"a", "an", "and", "are", "at", "be", "can", "do", "for", "how", "i", "in", "is", "it", "my", "of", "on", "the", "to", "what", "when", "who", "will", "with", "you", "your"}
GROUNDING_THRESHOLD = 0.10  # calibrated in docs/threshold_calibration.md

def tokens(text: str) -> Counter[str]:
    return Counter(token for token in TOKEN.findall(text.lower()) if token not in STOP_WORDS)

def cosine(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(value * b.get(key, 0) for key, value in a.items())
    norm_a = math.sqrt(sum(v*v for v in a.values()))
    norm_b = math.sqrt(sum(v*v for v in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

def fixed_chunks(text: str, size: int = 180, overlap: int = 40) -> list[str]:
    return [text[start:start+size] for start in range(0, len(text), size-overlap) if text[start:start+size].strip()]

def sentence_chunks(text: str, max_sentences: int = 2) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [" ".join(sentences[i:i+max_sentences]) for i in range(0, len(sentences), max_sentences)]

class LocalCollection:
    def __init__(self, name: str): self.name, self.rows = name, []
    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        self.rows = [{"id": i, "text": d, "metadata": m, "vector": tokens(d)} for i, d, m in zip(ids, documents, metadatas)]
    def query(self, query_text: str, n_results: int = 3) -> list[dict]:
        q = tokens(query_text)
        return sorted(({**row, "similarity": cosine(q, row["vector"])} for row in self.rows), key=lambda r: r["similarity"], reverse=True)[:n_results]

class ChromaSentenceTransformerCollection:
    """Persistent local ChromaDB collection with SentenceTransformers embeddings."""
    def __init__(self, name: str):
        import chromadb
        from sentence_transformers import SentenceTransformer
        self.name = name
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path=str(ROOT / "chroma_data"))
        self.collection = client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> None:
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=self.embedder.encode(documents).tolist())
    def query(self, query_text: str, n_results: int = 3) -> list[dict]:
        result = self.collection.query(query_embeddings=self.embedder.encode([query_text]).tolist(), n_results=n_results, include=["documents", "metadatas", "distances"])
        return [{"id": item_id, "text": text, "metadata": metadata, "similarity": round(1 - distance, 4)} for item_id, text, metadata, distance in zip(result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0])]

class RAGCore:
    def __init__(self):
        self.documents = json.loads(KB_PATH.read_text(encoding="utf-8"))
        collection_cls = LocalCollection
        self.backend = "local_deterministic"
        if os.getenv("RAG_BACKEND", "chroma").lower() == "chroma":
            try:
                import chromadb  # noqa: F401
                import sentence_transformers  # noqa: F401
                collection_cls = ChromaSentenceTransformerCollection
                self.backend = "chromadb_sentence_transformers"
            except ImportError:
                pass
        self.collections = {"fixed_overlap": collection_cls("cred_fixed_overlap"), "sentence": collection_cls("cred_sentence")}
        self.cache: dict[str, tuple[str, list[dict]]] = {}
        self.llm_calls = 0
        self.index_all()
    def index_all(self) -> None:
        for strategy, chunker in (("fixed_overlap", fixed_chunks), ("sentence", sentence_chunks)):
            ids=[]; docs=[]; metadata=[]
            for doc in self.documents:
                # Index the title with the chunk: users naturally phrase questions
                # using policy headings (for example, "NRI account eligibility").
                for index, chunk in enumerate(chunker(doc["title"] + ". " + doc["text"])):
                    ids.append(f"{doc['id']}-{index}"); docs.append(chunk); metadata.append({"parent_id": doc["id"], "title": doc["title"]})
            self.collections[strategy].upsert(ids, docs, metadata)
    def add_document(self, doc_id: str, title: str, text: str) -> None:
        self.documents.append({"id": doc_id, "title": title, "text": text}); self.index_all(); self.cache.clear()
    def retrieve(self, query: str, strategy: str = "sentence", k: int = 3) -> list[dict]:
        return self.collections[strategy].query(query, k)
    def answer(self, query: str, strategy: str = "sentence") -> tuple[str, list[dict], bool]:
        normalized = " ".join(query.lower().split())
        if normalized in self.cache:
            answer, hits = self.cache[normalized]
            return answer, hits, True
        hits = self.retrieve(query, strategy)
        if not hits or hits[0]["similarity"] < GROUNDING_THRESHOLD:
            answer = "I don't know based on the available Cred policy knowledge base."
        else:
            self.llm_calls += 1
            # Deterministic mock grounded generation: only retrieved text becomes answer.
            answer = " ".join(hit["text"] for hit in hits[:2])
        self.cache[normalized] = (answer, hits)
        return answer, hits, False
