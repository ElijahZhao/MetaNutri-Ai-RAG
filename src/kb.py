"""Build ChromaDB vector store from KB chunk texts.

Input:  data/kb_foods.txt, data/kb_guidelines.txt
        DASHSCOPE_API_KEY in .env (Alibaba Bailian, text-embedding-v3, OpenAI-compatible endpoint)
Output: data/chroma_db/ (PersistentClient, collection "nutri_kb")

Run: python3 src/kb.py
"""
import os
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EMB_MODEL = "text-embedding-v3"
DIM = 1024
COLLECTION = "nutri_kb"
BATCH = 10  # DashScope embedding input limit per request

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def load_chunks():
    chunks = []
    with open("data/kb_foods.txt", encoding="utf-8") as f:
        text = f.read()
    for blk in re.split(r"\n(?=【)", text.strip()):
        blk = blk.strip()
        if blk:
            kind = "food" if blk.startswith("【食物") else "guideline"
            chunks.append({"type": kind, "text": blk})

    with open("data/kb_guidelines.txt", encoding="utf-8") as f:
        text = f.read()
    for blk in re.split(r"\n(?=【)", text.strip()):
        blk = blk.strip()
        if blk and blk.startswith("【"):
            chunks.append({"type": "guideline", "text": blk})
    return chunks


def embed_batch(texts):
    r = client.embeddings.create(model=EMB_MODEL, input=texts)
    return [d.embedding for d in r.data]


def main():
    import chromadb

    chunks = load_chunks()
    print(f"chunks: {len(chunks)} (food={sum(1 for c in chunks if c['type']=='food')}, "
          f"guideline={sum(1 for c in chunks if c['type']!='food')})")

    db = chromadb.PersistentClient(path="data/chroma_db")
    col = db.get_or_create_collection(
        COLLECTION, metadata={"hnsw:space": "cosine"}
    )
    if col.count() > 0:
        print(f"collection already has {col.count()} docs; delete to rebuild")
        return

    ids, docs, metas, vecs = [], [], [], []
    for i, c in enumerate(chunks):
        ids.append(f"chunk_{i:04d}")
        docs.append(c["text"])
        metas.append({"type": c["type"]})

    for b in range(0, len(chunks), BATCH):
        batch_texts = docs[b : b + BATCH]
        batch_ids = ids[b : b + BATCH]
        batch_metas = metas[b : b + BATCH]
        batch_vecs = embed_batch(batch_texts)
        vecs.extend(batch_vecs)
        col.add(ids=batch_ids, documents=batch_texts, embeddings=batch_vecs,
                metadatas=batch_metas)
        print(f"added {b + len(batch_texts)}/{len(chunks)}", flush=True)

    print(f"DONE: collection '{COLLECTION}' count={col.count()}")


if __name__ == "__main__":
    main()
