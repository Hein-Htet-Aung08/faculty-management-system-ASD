import hashlib
import importlib
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import requests

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

CORPUS_DIR = APP_DIR / "corpus"
CORPUS_FILE = CORPUS_DIR / "corpus.jsonl"
IDF_FILE = CORPUS_DIR / "idf.json"
CHROMA_DIR = APP_DIR / "chroma_db"
AUDIT_FILE = APP_DIR / "rag-audit.jsonl"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

COLLECTION_NAME = "research_grant_corpus"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
TOP_K_DEFAULT = 5
EMBED_DIM = 1024

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "with",
    "is", "are", "this", "that", "into", "using", "based", "via", "from",
}
_WORD_RE = re.compile(r"[a-z0-9]+")
_SKIP_REPO_NAMES = {
    "node_modules", ".git", "venv", ".venv", "__pycache__",
    "data", "chroma_db", "corpus",
}


# chunking

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    pieces = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        pieces.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return pieces


# deterministic embeddings

def _words(text):
    return [w for w in _WORD_RE.findall((text or "").lower()) if w not in _STOPWORDS]


def _hash_bucket(token, dim=EMBED_DIM):
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return int(digest, 16) % dim


def _buckets_for(text):
    tokens = _words(text)
    buckets = [_hash_bucket(t) for t in tokens]
    buckets += [_hash_bucket(f"{a}_{b}") for a, b in zip(tokens, tokens[1:])]
    return buckets


def _raw_vector(text):
    vec = [0.0] * EMBED_DIM
    for bucket in _buckets_for(text):
        vec[bucket] += 1.0
    return vec


def compute_idf(documents):
    n_docs = max(len(documents), 1)
    doc_freq = [0] * EMBED_DIM
    for text in documents:
        for bucket in set(_buckets_for(text)):
            doc_freq[bucket] += 1
    return [math.log((n_docs + 1) / (df + 1)) + 1.0 for df in doc_freq]


def _load_idf():
    if IDF_FILE.is_file():
        try:
            return json.loads(IDF_FILE.read_text())
        except (ValueError, OSError):
            pass
    return [1.0] * EMBED_DIM


def _save_idf(idf):
    IDF_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDF_FILE.write_text(json.dumps(idf), encoding="utf-8")


def embed_texts(texts, idf=None):
    if idf is None:
        idf = _load_idf()
    vectors = []
    for text in texts:
        raw = _raw_vector(text)
        weighted = [v * idf[i] for i, v in enumerate(raw)]
        norm = math.sqrt(sum(v * v for v in weighted)) or 1.0
        vectors.append([v / norm for v in weighted])
    return vectors


# ChromaDB persistent store

_client = None


def _get_client():
    global _client
    if _client is None:
        import chromadb

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_collection():
    client = _get_client()
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=None)


def reset_collection():
    client = _get_client()
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    return client.create_collection(name=COLLECTION_NAME, embedding_function=None)


# audit log

def append_audit(entry):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **entry}
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# corpus loaders

# ============================================================
# Each student adds their own loader below, in the order
# student 1 -> 5. Missing/failed loaders are skipped (logged,
# not crashed) by load_all_database_chunks(), so this list is
# safe to keep fully "live" - no need to comment a slot out
# while that student's loader.py doesn't exist yet.
# ============================================================
_STUDENT_LOADERS = [
    ("student_1_andy.loader", "load_staff_chunks"),        # Student 1: Andy Lam (Staff Management)
    ("student_2_hein.loader", "load_teaching_chunks"),      # Student 2: Hein Htet Aung (Teaching, Subject & Classroom Allocation)
    ("student_3_tristan.loader", "load_workload_chunks"),   # Student 3: Tristan Lim (Workload & Availability Management)
    ("student_4_nicholas.loader", "load_research_chunks"),  # Student 4: Nicholas Hatzidimitriou (Research & Grant Management)
    ("student_5_matthew.loader", "load_performance_chunks"),# Student 5: Matthew Barnard (Performance & Professional Development)
]


def load_all_database_chunks():
    chunks = []
    for module_name, fn_name in _STUDENT_LOADERS:
        try:
            module = importlib.import_module(module_name)
            loader_fn = getattr(module, fn_name)
            chunks.extend(loader_fn())
        except Exception as exc:
            print(f"[rag_pipeline] loader {module_name}.{fn_name} unavailable or failed: {exc}")
    return chunks


def load_report_chunks():
    reports_dir = REPO_ROOT / "reports"
    if not reports_dir.is_dir():
        return []

    chunks = []
    for path in sorted(reports_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(reports_dir)
        chunks.append({"id": f"report-{rel}", "text": text, "tier": "tier_2", "source": "reports"})
    return chunks


def load_repository_chunks():
    if not REPO_ROOT.is_dir():
        return []

    entries = sorted(
        p.name
        for p in REPO_ROOT.iterdir()
        if p.name not in _SKIP_REPO_NAMES and not p.name.startswith(".")
    )
    text = (
        f"The faculty management system repository ({REPO_ROOT.name}/) "
        f"consists of the following top-level components: {', '.join(entries)}."
    )
    return [{"id": "repo-structure", "text": text, "tier": "tier_3", "source": "repository"}]


# corpus assembly

def _finalize_chunks(raw_records):
    finalized = []
    for record in raw_records:
        pieces = chunk_text(record["text"])
        if len(pieces) <= 1:
            finalized.append(record)
            continue
        for i, piece in enumerate(pieces):
            finalized.append(
                {"id": f"{record['id']}-{i}", "text": piece, "tier": record["tier"], "source": record["source"]}
            )
    return finalized


def refresh_corpus():
    raw = []
    raw.extend(load_all_database_chunks())
    raw.extend(load_report_chunks())
    raw.extend(load_repository_chunks())

    chunks = _finalize_chunks(raw)

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")

    collection = reset_collection()
    if chunks:
        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{"tier": c["tier"], "source": c["source"]} for c in chunks]
        idf = compute_idf(documents)
        _save_idf(idf)
        embeddings = embed_texts(documents, idf=idf)
        collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    print(f"[rag_pipeline] corpus refreshed: {len(chunks)} chunk(s) indexed.")
    return chunks


def _load_corpus_chunks():
    if not CORPUS_FILE.is_file():
        return []
    chunks = []
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


# retrieval

def lexical_fallback_retrieve(query, k=TOP_K_DEFAULT):
    chunks = _load_corpus_chunks()
    query_words = set(_words(query))

    scored = []
    for chunk in chunks:
        score = len(query_words & set(_words(chunk["text"])))
        scored.append((score, chunk))
    scored.sort(key=lambda pair: -pair[0])

    results = []
    for score, chunk in scored[:k]:
        results.append(
            {
                "id": chunk["id"],
                "text": chunk["text"],
                "tier": chunk["tier"],
                "source": chunk["source"],
                "score": score,
                "retrieval_method": "lexical_fallback",
            }
        )
    return results


def retrieve_context(query, k=TOP_K_DEFAULT):
    try:
        collection = get_collection()
        count = collection.count()
        if count == 0:
            return lexical_fallback_retrieve(query, k=k)

        query_embedding = embed_texts([query])[0]
        results = collection.query(query_embeddings=[query_embedding], n_results=min(k, count))

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        retrieved = []
        for i, chunk_id in enumerate(ids):
            metadata = metadatas[i] or {}
            retrieved.append(
                {
                    "id": chunk_id,
                    "text": documents[i],
                    "tier": metadata.get("tier"),
                    "source": metadata.get("source"),
                    "distance": distances[i],
                    "retrieval_method": "vector",
                }
            )
        return retrieved
    except Exception as exc:
        print(f"[rag_pipeline] vector retrieval failed ({type(exc).__name__}: {exc}); falling back to lexical retrieval.")
        return lexical_fallback_retrieve(query, k=k)


def confidence_from_results(results):
    if not results:
        return "low"

    top = results[0]
    if top.get("retrieval_method") == "lexical_fallback":
        score = top.get("score", 0)
        if score >= 3:
            return "medium"
        return "low"

    distance = top.get("distance")
    if distance is None:
        return "medium"
    if distance < 1.35:
        return "high"
    if distance < 1.7:
        return "medium"
    return "low"


# generation

def generate_with_ollama(system_prompt, user_prompt, max_tokens=400, temperature=0.2):
    try:
        from openai import OpenAI

        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            return None, f"empty response from model {OLLAMA_MODEL!r}"
        return content, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


_ANSWER_SYSTEM_PROMPT = (
    "You are an assistant for a university Faculty Management System, "
    "covering staff records, teaching/subject/classroom allocation, "
    "workload and availability, research and grant management, and "
    "performance and professional development. Answer ONLY using the "
    "retrieved context given below - never invent staff, projects, grants, "
    "publications, allocations, or figures that are not present in it. If "
    "the context does not contain enough information to answer, say so "
    "explicitly rather than guessing. Reference the chunk IDs (in brackets) "
    "that support each part of your answer.\n\n"
)


def answer_question(question, k=TOP_K_DEFAULT):
    results = retrieve_context(question, k=k)
    confidence_category = confidence_from_results(results)

    if results:
        context_block = "\n".join(f"[{r['id']}] {r['text']}" for r in results)
    else:
        context_block = "No relevant context was retrieved."

    user_prompt = (
        f"Question: {question}\n\n"
        f"Retrieved context:\n{context_block}\n\n"
        "Answer the question using only the context above, and reference the "
        "chunk IDs that support your answer."
    )

    answer_text, error = generate_with_ollama(_ANSWER_SYSTEM_PROMPT, user_prompt)
    final_answer = answer_text if not error else f"[LLM ERROR: {error}]"
    citations = [r["id"] for r in results]

    result = {
        "question": question,
        "answer": final_answer,
        "citations": citations,
        "confidence_category": confidence_category,
        "retrieved_count": len(results),
    }

    append_audit(
        {
            "question": question,
            "answer": final_answer,
            "citations": citations,
            "confidence_category": confidence_category,
        }
    )

    return result


if __name__ == "__main__":
    print("Refreshing corpus...")
    refresh_corpus()

    print("\nRetrieval test:")
    results = retrieve_context("What grants are linked to active research projects?", k=5)
    for r in results:
        print(f"  [{r['tier']}] {r['id']}: {r['text'][:80]}...")

    print("\nAnswer test:")
    answer = answer_question("Summarize the current funding status across all research projects.")
    print(json.dumps(answer, indent=2))
