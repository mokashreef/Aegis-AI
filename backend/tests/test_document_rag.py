"""
Unit and integration tests for Aegis AI Local Document RAG Engine (Drag & Drop).
"""

from unittest.mock import patch
from fastapi.testclient import TestClient

from aegis_core.main import app
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.system_tools import QueryDocumentTool
from aegis_core.memory.document_rag import DocumentRAGEngine

client = TestClient(app)


def test_document_intent_routing_arabic():
    """Verifies that Arabic document RAG queries correctly route to query_document tool."""
    prompts = [
        "لخص المستند المرفق",
        "ابحث في الملف عن الشروط",
        "ماذا يقول الملف بخصوص الميزانية؟",
        "اسأل المستند",
        "ما محتوى الملف",
    ]
    for p in prompts:
        routed = IntentRouter.classify_and_route(p)
        assert routed is not None, f"Failed to route: {p}"
        assert routed["intent"] == UserIntent.DOCUMENT_RAG
        assert routed["name"] == "query_document"


def test_document_intent_routing_english():
    """Verifies that English document queries route to query_document tool."""
    prompts = [
        "summarize document please",
        "query file about pricing",
        "search in document for deployment",
        "what does the file say",
    ]
    for p in prompts:
        routed = IntentRouter.classify_and_route(p)
        assert routed is not None, f"Failed to route: {p}"
        assert routed["intent"] == UserIntent.DOCUMENT_RAG
        assert routed["name"] == "query_document"


def test_chunking_and_fts5_indexing(tmp_path):
    """Verifies document extraction, chunking, and FTS5 BM25 search in Arabic and English."""
    sample_file = tmp_path / "sample_manual.txt"
    sample_text = (
        "مرحباً بك في دليل تشغيل نظام Aegis AI المساعد الذكي لنظام ويندوز.\n\n"
        "الفصل الأول: معمارية النظام والأمان المحلي بنسبة مائة بالمائة وبلا اشتراكات.\n\n"
        "Section Two: Performance benchmarks and offline AI models including Qwen and Llama.\n\n"
        "Section Three: Shortcuts and global summons using Alt+Space."
    )
    sample_file.write_text(sample_text, encoding="utf-8")

    engine = DocumentRAGEngine()
    indexed = engine.index_document(sample_file, "sample_manual.txt")

    assert indexed["doc_id"].startswith("doc_")
    assert indexed["chunk_count"] >= 1
    assert indexed["filename"] == "sample_manual.txt"

    # Query Arabic FTS5
    ar_chunks = engine.query_chunks("معمارية", doc_id=indexed["doc_id"])
    assert len(ar_chunks) > 0
    assert "الأمان المحلي" in ar_chunks[0]["content"]

    # Query English FTS5
    en_chunks = engine.query_chunks("benchmarks", doc_id=indexed["doc_id"])
    assert len(en_chunks) > 0
    assert "Performance" in en_chunks[0]["content"]

    # Clean up test doc
    engine.delete_document(indexed["doc_id"])


@patch("aegis_core.ai_runtime.router.ai_router.stream_chat")
async def test_ask_document_grounded_answer(mock_stream, tmp_path):
    """Verifies ask_document produces a grounded citation answer."""
    from aegis_core.ai_runtime.base import LLMChunk

    async def mock_generator(*args, **kwargs):
        yield LLMChunk(delta="النظام يعمل محلياً بنسبة 100% كما ورد في الصفحة 1.", provider="local", model="mock")

    mock_stream.side_effect = mock_generator

    sample_file = tmp_path / "policy.md"
    sample_file.write_text("# Policy\nAegis AI operates 100% locally.", encoding="utf-8")

    engine = DocumentRAGEngine()
    indexed = engine.index_document(sample_file, "policy.md")

    res = await engine.ask_document("هل يعمل محلياً؟", doc_id=indexed["doc_id"], language="ar")
    assert res["success"] is True
    assert "محلياً" in res["answer"]
    assert len(res["sources"]) > 0

    engine.delete_document(indexed["doc_id"])


def test_api_documents_endpoints(tmp_path):
    """Verifies REST endpoints for upload, list, query, and delete."""
    sample_file = tmp_path / "test_api_doc.txt"
    sample_file.write_text("Aegis AI Document API Test File Content.", encoding="utf-8")

    # 1. Upload via file_path query
    res = client.post(f"/api/documents/upload?file_path={str(sample_file)}")
    assert res.status_code == 200
    doc_data = res.json()
    doc_id = doc_data["doc_id"]
    assert doc_data["filename"] == "test_api_doc.txt"

    # 2. List documents
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["id"] == doc_id for d in docs)

    # 3. Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True


@patch("aegis_core.memory.document_rag.document_rag_engine.ask_document")
async def test_query_document_tool_execution(mock_ask):
    """Verifies QueryDocumentTool executes properly and returns structured ToolResult."""
    mock_ask.return_value = {
        "success": True,
        "doc_id": "test-doc-123",
        "filename": "guide.pdf",
        "chunks_retrieved": 2,
        "sources": [{"page": 1, "snippet": "Sample text"}],
        "answer": "This is a grounded answer from document.",
    }

    tool = QueryDocumentTool()
    res = await tool.execute(query="summary", doc_id="test-doc-123")
    assert res.success is True
    assert "grounded" in res.message
    assert res.data["doc_id"] == "test-doc-123"
