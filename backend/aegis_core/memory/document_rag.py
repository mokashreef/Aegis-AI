"""
Aegis AI - Drag & Drop Local Document RAG Engine.
Provides zero-cloud, 100% private document ingestion (PDF, DOCX, TXT, MD, Code),
intelligent text chunking, SQLite FTS5 BM25 full-text indexing, and grounded
conversational retrieval-augmented generation.
"""

import re
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from aegis_core.memory.db import db_engine
from aegis_core.utils.logger import logger

RAG_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS local_documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER DEFAULT 1,
    FOREIGN KEY(doc_id) REFERENCES local_documents(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
    chunk_id, doc_id, filename, content, tokenize = 'unicode61'
);
"""


class DocumentRAGEngine:
    """Manages document text extraction, chunking, FTS5 storage, and semantic RAG retrieval."""

    def __init__(self, db=None):
        self.db = db or db_engine
        self._init_schema()

    def _init_schema(self) -> None:
        """Initializes RAG database tables and FTS5 virtual index."""
        try:
            with self.db.get_connection() as conn:
                conn.executescript(RAG_SCHEMA_SQL)
        except Exception as exc:
            logger.debug("RAG schema init notice: %s", exc)

    def extract_text(self, file_path: Path, filename: str) -> List[Dict[str, Any]]:
        """
        Extracts textual content and page markers from PDF, DOCX, TXT, MD, CSV, JSON, and source code.
        """
        ext = (Path(filename).suffix or file_path.suffix).lower().lstrip(".")
        pages: List[Dict[str, Any]] = []

        # 1. PDF Documents
        if ext == "pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(file_path))
                for idx, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    if txt.strip():
                        pages.append({"page": idx + 1, "text": txt.strip()})
            except Exception as exc:
                logger.warning("pypdf parsing failed for %s, trying raw text: %s", filename, exc)

        # 2. Microsoft Word Documents (.docx)
        elif ext in ("docx", "doc"):
            try:
                with zipfile.ZipFile(str(file_path)) as zf:
                    xml_content = zf.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for p in tree.iterfind(".//w:p", ns):
                    texts = [node.text for node in p.iterfind(".//w:t", ns) if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                full_text = "\n\n".join(paragraphs).strip()
                if full_text:
                    pages.append({"page": 1, "text": full_text})
            except Exception as exc:
                logger.warning("DOCX extraction failed for %s: %s", filename, exc)

        # 3. Plain Text, Markdown, Code, JSON, CSV
        if not pages:
            raw_bytes = file_path.read_bytes()
            text = ""
            for enc in ("utf-8", "utf-8-sig", "cp1256", "latin-1"):
                try:
                    text = raw_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            if text.strip():
                pages.append({"page": 1, "text": text.strip()})

        return pages

    def chunk_text(
        self,
        pages: List[Dict[str, Any]],
        chunk_size: int = 700,
        overlap: int = 120,
    ) -> List[Dict[str, Any]]:
        """Splits extracted text into overlapping chunks while preserving page provenance."""
        chunks = []
        chunk_index = 0

        for p in pages:
            page_num = p.get("page", 1)
            text = p.get("text", "")
            # Split by paragraphs or double newlines
            paragraphs = [para.strip() for para in re.split(r"\n\s*\n", text) if para.strip()]
            current_chunk = ""

            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 <= chunk_size:
                    current_chunk = f"{current_chunk}\n\n{para}".strip()
                else:
                    if current_chunk:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "page": page_num,
                            "content": current_chunk,
                        })
                        chunk_index += 1
                        # Retain overlap window from previous chunk
                        overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                        current_chunk = f"{overlap_text}\n\n{para}".strip()
                    else:
                        # Paragraph itself is larger than chunk_size
                        for i in range(0, len(para), chunk_size - overlap):
                            sub = para[i : i + chunk_size]
                            chunks.append({
                                "chunk_index": chunk_index,
                                "page": page_num,
                                "content": sub,
                            })
                            chunk_index += 1
                        current_chunk = ""

            if current_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "page": page_num,
                    "content": current_chunk,
                })
                chunk_index += 1

        return chunks

    def index_document(self, file_path: Path, filename: str) -> Dict[str, Any]:
        """Indexes a local document into SQLite FTS5 for instant sub-millisecond retrieval."""
        self._init_schema()
        pages = self.extract_text(file_path, filename)
        if not pages:
            raise ValueError(f"Could not extract any readable text from document: {filename}")

        chunks = self.chunk_text(pages)
        if not chunks:
            raise ValueError(f"Document produced zero chunks after processing: {filename}")

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        file_size = file_path.stat().st_size if file_path.exists() else 0
        ext = Path(filename).suffix.lower().lstrip(".")

        # Generate short summary / preview
        first_chunk = chunks[0]["content"] if chunks else ""
        summary = first_chunk[:200] + ("..." if len(first_chunk) > 200 else "")

        with self.db.get_connection() as conn:
            # 1. Insert into local_documents
            conn.execute(
                """
                INSERT INTO local_documents (id, filename, file_type, file_size, chunk_count, summary)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (doc_id, filename, ext, file_size, len(chunks), summary),
            )

            # 2. Insert into document_chunks and document_fts
            for c in chunks:
                chunk_id = f"{doc_id}_c{c['chunk_index']}"
                conn.execute(
                    """
                    INSERT INTO document_chunks (id, doc_id, chunk_index, content, page_number)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (chunk_id, doc_id, c["chunk_index"], c["content"], c["page"]),
                )
                conn.execute(
                    """
                    INSERT INTO document_fts (chunk_id, doc_id, filename, content)
                    VALUES (?, ?, ?, ?);
                    """,
                    (chunk_id, doc_id, filename, c["content"]),
                )

        logger.info(
            "Document '%s' successfully indexed (id: %s, chunks: %d, size: %d bytes)",
            filename,
            doc_id,
            len(chunks),
            file_size,
        )
        return {
            "doc_id": doc_id,
            "filename": filename,
            "file_type": ext,
            "file_size": file_size,
            "chunk_count": len(chunks),
            "summary": summary,
        }

    def query_chunks(
        self,
        query: str,
        doc_id: Optional[str] = None,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant excerpts using SQLite FTS5 BM25 match query
        with lexical fuzzy fallback.
        """
        self._init_schema()
        clean_words = [re.sub(r"[^\w\s]", "", w).strip() for w in query.split()]
        clean_words = [w for w in clean_words if len(w) > 1]
        results: List[Dict[str, Any]] = []

        if not clean_words:
            # If no alphanumeric words, just fetch the first few chunks of the document
            with self.db.get_connection() as conn:
                params: List[Any] = [top_k]
                sql = "SELECT id, doc_id, chunk_index, content, page_number FROM document_chunks "
                if doc_id:
                    sql += "WHERE doc_id = ? "
                    params.insert(0, doc_id)
                sql += "ORDER BY chunk_index ASC LIMIT ?;"
                rows = conn.execute(sql, tuple(params)).fetchall()
                for r in rows:
                    results.append({
                        "chunk_id": r[0],
                        "doc_id": r[1],
                        "chunk_index": r[2],
                        "content": r[3],
                        "page": r[4],
                        "score": 1.0,
                    })
            return results

        # 1. FTS5 Search
        fts_query = " OR ".join(f'"{w}"' for w in clean_words)
        try:
            with self.db.get_connection() as conn:
                if doc_id:
                    sql = """
                        SELECT f.chunk_id, f.doc_id, f.filename, f.content, c.page_number, c.chunk_index
                        FROM document_fts f
                        JOIN document_chunks c ON f.chunk_id = c.id
                        WHERE f.doc_id = ? AND document_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?;
                    """
                    rows = conn.execute(sql, (doc_id, fts_query, top_k)).fetchall()
                else:
                    sql = """
                        SELECT f.chunk_id, f.doc_id, f.filename, f.content, c.page_number, c.chunk_index
                        FROM document_fts f
                        JOIN document_chunks c ON f.chunk_id = c.id
                        WHERE document_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?;
                    """
                    rows = conn.execute(sql, (fts_query, top_k)).fetchall()

                for r in rows:
                    results.append({
                        "chunk_id": r[0],
                        "doc_id": r[1],
                        "filename": r[2],
                        "content": r[3],
                        "page": r[4],
                        "chunk_index": r[5],
                        "score": 1.0,
                    })
        except Exception as exc:
            logger.debug("FTS5 query exception: %s", exc)

        # 2. Fallback Substring / Keyword Scored Match if FTS yielded few results
        if len(results) < top_k:
            existing_ids = {r["chunk_id"] for r in results}
            with self.db.get_connection() as conn:
                sql = "SELECT id, doc_id, chunk_index, content, page_number FROM document_chunks "
                params_list: List[Any] = []
                if doc_id:
                    sql += "WHERE doc_id = ? "
                    params_list.append(doc_id)
                rows = conn.execute(sql, tuple(params_list)).fetchall()

                scored = []
                for r in rows:
                    if r[0] in existing_ids:
                        continue
                    cnt = r[3].lower()
                    score = sum(1 for w in clean_words if w.lower() in cnt)
                    if score > 0:
                        scored.append((score, r))

                scored.sort(key=lambda x: x[0], reverse=True)
                for score, r in scored[: (top_k - len(results))]:
                    results.append({
                        "chunk_id": r[0],
                        "doc_id": r[1],
                        "chunk_index": r[2],
                        "content": r[3],
                        "page": r[4],
                        "score": round(score / len(clean_words), 2),
                    })

        return results

    async def ask_document(
        self,
        query: str,
        doc_id: Optional[str] = None,
        language: str = "auto",
    ) -> Dict[str, Any]:
        """
        Executes grounded retrieval-augmented generation: pulls relevant excerpts
        and queries the local AI model with cited document context.
        """
        chunks = self.query_chunks(query=query, doc_id=doc_id, top_k=4)
        if not chunks:
            # If no chunks match, check if any documents exist
            all_docs = self.list_documents()
            if not all_docs:
                return {
                    "success": False,
                    "answer": (
                        "لم يتم تحميل أو سحب أي مستند محلي حتى الآن. "
                        "اسحب ملفاً (PDF, Word, Text) للبدء في سؤاله."
                    ),
                    "sources": [],
                    "chunks_retrieved": 0,
                }
            # Use the first document's introductory chunks
            first_doc = all_docs[0]
            chunks = self.query_chunks(query="", doc_id=first_doc["id"], top_k=3)

        doc_name = chunks[0].get("filename") if chunks else "المستند"
        excerpts_text = "\n\n".join(
            f"--- [مقتطف من الصفحة {c.get('page', 1)}]:\n{c.get('content', '')}"
            for c in chunks
        )

        is_arabic = (
            language == "ar"
            or any("\u0600" <= ch <= "\u06ff" for ch in query)
            or language == "auto"
        )

        from aegis_core.ai_runtime.base import LLMMessage
        from aegis_core.ai_runtime.router import ai_router

        sys_prompt = (
            "You are Aegis AI Local Document Specialist. "
            "Your task is to answer the user's question accurately, strictly based on the provided document excerpts. "
            "Do not hallucinate facts outside the excerpts. Mention specific page numbers where relevant."
        )
        user_prompt = (
            f"Document Excerpts from '{doc_name}':\n\n"
            f"{excerpts_text}\n\n"
            f"---\n"
            f"User Question: {query}\n"
            f"Instruction: Answer in {'Arabic' if is_arabic else 'English'} thoroughly with citations."
        )

        messages = [
            LLMMessage(role="system", content=sys_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        # Stream or gather answer from AI router
        answer_parts = []
        try:
            async for chunk in ai_router.stream_chat(messages=messages):
                if chunk.delta:
                    answer_parts.append(chunk.delta)
        except Exception as exc:
            logger.error("RAG synthesis error: %s", exc)
            answer_parts.append(f"تعذر استخلاص الإجابة من النموذج: {exc}")

        full_answer = "".join(answer_parts).strip()
        sources = [
            {
                "page": c.get("page", 1),
                "chunk_index": c.get("chunk_index", 0),
                "snippet": c.get("content", "")[:140] + "...",
            }
            for c in chunks
        ]

        return {
            "success": True,
            "query": query,
            "answer": full_answer,
            "doc_id": doc_id or (chunks[0].get("doc_id") if chunks else None),
            "filename": doc_name,
            "sources": sources,
            "chunks_retrieved": len(chunks),
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all local documents currently indexed in the RAG store."""
        self._init_schema()
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, filename, file_type, file_size, chunk_count, summary, created_at
                FROM local_documents
                ORDER BY created_at DESC;
                """
            ).fetchall()
            return [
                {
                    "id": r[0],
                    "filename": r[1],
                    "file_type": r[2],
                    "file_size": r[3],
                    "chunk_count": r[4],
                    "summary": r[5],
                    "created_at": r[6],
                }
                for r in rows
            ]

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document and its indexed chunks from SQLite FTS5."""
        self._init_schema()
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM local_documents WHERE id = ?;", (doc_id,))
            conn.execute("DELETE FROM document_chunks WHERE doc_id = ?;", (doc_id,))
            conn.execute("DELETE FROM document_fts WHERE doc_id = ?;", (doc_id,))
        return True

    def clear_all(self) -> bool:
        """Wipes all documents and chunks for clean state."""
        self._init_schema()
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM local_documents;")
            conn.execute("DELETE FROM document_chunks;")
            conn.execute("DELETE FROM document_fts;")
        return True


document_rag_engine = DocumentRAGEngine()
