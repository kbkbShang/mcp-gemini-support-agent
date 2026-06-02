from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List

import numpy as np

from support_agent.config import KB_DIR

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_\-]{2,}")


@dataclass
class KBDoc:
    doc_id: str
    title: str
    path: Path
    content: str


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_PATTERN.findall(text)]


class KBIndex:
    def __init__(self, dim: int = 256) -> None:
        self.dim = dim
        self.docs: list[KBDoc] = []
        self._vectors = np.zeros((0, dim), dtype="float32")
        self._faiss_index = None
        self._load_docs()
        self._build_index()

    def _load_docs(self) -> None:
        files = sorted(KB_DIR.glob("*.md"))
        for idx, path in enumerate(files, start=1):
            content = path.read_text(encoding="utf-8")
            title = content.splitlines()[0].lstrip("# ").strip() if content else path.stem
            self.docs.append(KBDoc(doc_id=f"kb-{idx:03d}", title=title, path=path, content=content))

    def _embed(self, text: str) -> np.ndarray:
        vec = np.zeros((self.dim,), dtype="float32")
        for token in _tokenize(text):
            vec[hash(token) % self.dim] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def _build_index(self) -> None:
        if not self.docs:
            return
        self._vectors = np.vstack([self._embed(doc.content) for doc in self.docs]).astype("float32")
        if faiss is not None:
            self._faiss_index = faiss.IndexFlatIP(self.dim)
            self._faiss_index.add(self._vectors)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not self.docs:
            return []
        k = min(top_k, len(self.docs))
        qv = self._embed(query).reshape(1, -1).astype("float32")
        if self._faiss_index is not None:
            scores, indices = self._faiss_index.search(qv, k)
            idxs = indices[0].tolist()
            sims = scores[0].tolist()
        else:  # pragma: no cover
            sims_all = (self._vectors @ qv.T).reshape(-1)
            idxs = np.argsort(-sims_all)[:k].tolist()
            sims = [float(sims_all[i]) for i in idxs]
        results = []
        for i, score in zip(idxs, sims):
            doc = self.docs[i]
            snippet = " ".join(doc.content.split())[:220]
            results.append(
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "path": str(doc.path.relative_to(KB_DIR.parent.parent)),
                    "score": round(float(score), 4),
                    "snippet": snippet,
                }
            )
        return results

    def get_doc(self, doc_id: str) -> dict | None:
        for doc in self.docs:
            if doc.doc_id == doc_id:
                return {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "path": str(doc.path.relative_to(KB_DIR.parent.parent)),
                    "content": doc.content,
                }
        return None
