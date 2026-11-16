"""
Aegis AI - Unit Tests for Native Windows Screen OCR Engine & Text Extraction Tool.
Verifies offline pixel text recognition, bilingual intent routing, and vision analyzer augmentation.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image
import pytest
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.screen_ocr import ScreenOCREngine, screen_ocr_engine
from aegis_core.automation.system_tools import ExtractScreenTextTool


@pytest.mark.asyncio
async def test_ocr_engine_available_languages():
    engine = ScreenOCREngine()
    langs = engine.get_available_languages()
    assert isinstance(langs, list)
    assert len(langs) > 0


@pytest.mark.asyncio
async def test_ocr_engine_language_resolution():
    engine = ScreenOCREngine(default_lang="ar-SA")
    with patch.object(engine, "get_available_languages", return_value=["ar-SA", "en-US", "fr-FR"]):
        assert engine.resolve_language("ar") == "ar-SA"
        assert engine.resolve_language("en") == "en-US"
        assert engine.resolve_language("fr") == "fr-FR"
        assert engine.resolve_language("nonexistent") == "ar-SA"


@pytest.mark.asyncio
async def test_ocr_engine_extract_text_mocked():
    engine = ScreenOCREngine()
    test_img = Image.new("RGB", (200, 100), color=(255, 255, 255))

    mock_line_1 = MagicMock()
    mock_line_1.text = "مرحباً بكم في نظام Aegis AI"
    mock_line_2 = MagicMock()
    mock_line_2.text = "Native Windows OCR Engine"

    mock_res = MagicMock()
    mock_res.text = "مرحباً بكم في نظام Aegis AI\nNative Windows OCR Engine"
    mock_res.lines = [mock_line_1, mock_line_2]

    with patch("winocr.recognize_pil", new_callable=AsyncMock) as mock_recognize:
        mock_recognize.return_value = mock_res
        res = await engine.extract_text(image_or_path=test_img, lang="ar-SA")

        assert res["success"] is True
        assert "Aegis AI" in res["text"]
        assert len(res["lines"]) == 2
        assert res["line_count"] == 2
        assert res["word_count"] > 0
        assert res["language"] == "ar-SA"
        assert res["latency_ms"] >= 0.0


@pytest.mark.asyncio
async def test_ocr_engine_error_handling():
    engine = ScreenOCREngine()
    test_img = Image.new("RGB", (100, 50), color=(0, 0, 0))

    with patch("winocr.recognize_pil", side_effect=RuntimeError("OCR engine crashed")):
        res = await engine.extract_text(image_or_path=test_img)
        assert res["success"] is False
        assert "OCR engine crashed" in res["error"]
        assert res["text"] == ""
        assert res["lines"] == []


@pytest.mark.asyncio
async def test_extract_screen_text_tool():
    tool = ExtractScreenTextTool()
    assert tool.name == "extract_screen_text"

    mock_ocr = {
        "success": True,
        "text": "Code Evolution - كود التطور",
        "lines": ["Code Evolution - كود التطور"],
        "line_count": 1,
        "word_count": 4,
        "language": "ar-SA",
        "latency_ms": 42.0,
    }

    with patch.object(screen_ocr_engine, "extract_text", new_callable=AsyncMock) as mock_extract:
        with patch("aegis_core.automation.clipboard_manager.ClipboardManager.set_text") as mock_set_clip:
            mock_extract.return_value = mock_ocr
            res = await tool.execute(lang="ar-SA", copy_to_clipboard=True)

            assert res.success is True
            assert res.data["line_count"] == 1
            assert "Code Evolution" in res.data["text"]
            assert res.data["copied_to_clipboard"] is True
            mock_set_clip.assert_called_once_with("Code Evolution - كود التطور")


def test_intent_router_screen_ocr_arabic():
    # Extraction only
    r1 = IntentRouter.classify_and_route("استخرج النص من الشاشة")
    assert r1 is not None
    assert r1["intent"] == UserIntent.SCREEN_OCR
    assert r1["name"] == "extract_screen_text"
    assert r1["arguments"]["copy_to_clipboard"] is False

    # Extraction with clipboard copy
    r2 = IntentRouter.classify_and_route("انسخ النص من الشاشة وحطه بالحافظة")
    assert r2 is not None
    assert r2["intent"] == UserIntent.SCREEN_OCR
    assert r2["name"] == "extract_screen_text"
    assert r2["arguments"]["copy_to_clipboard"] is True
    assert r2["arguments"]["lang"] == "ar-SA"

    # Alternate phrasing
    r3 = IntentRouter.classify_and_route("اقرأ نص الشاشة")
    assert r3 is not None
    assert r3["intent"] == UserIntent.SCREEN_OCR


def test_intent_router_screen_ocr_english():
    r1 = IntentRouter.classify_and_route("extract screen text")
    assert r1 is not None
    assert r1["intent"] == UserIntent.SCREEN_OCR
    assert r1["name"] == "extract_screen_text"
    assert r1["arguments"]["copy_to_clipboard"] is False

    r2 = IntentRouter.classify_and_route("copy text from screen to clipboard")
    assert r2 is not None
    assert r2["intent"] == UserIntent.SCREEN_OCR
    assert r2["name"] == "extract_screen_text"
    assert r2["arguments"]["copy_to_clipboard"] is True
    assert r2["arguments"]["lang"] == "en-US"


@pytest.mark.asyncio
async def test_vision_analyzer_integrates_ocr():
    from aegis_core.ai_runtime.vision_analyzer import screen_vision_analyzer

    mock_cap = {
        "success": True,
        "path": "test_screen.jpg",
        "base64": "dummy_b64",
        "width": 1920,
        "height": 1080,
        "latency_ms": 15.0,
    }

    mock_ocr = {
        "success": True,
        "text": "Exception: NullReference in module main.py",
        "lines": ["Exception: NullReference in module main.py"],
    }

    with patch("aegis_core.automation.screen_capture.ScreenCaptureEngine.capture", return_value=mock_cap):
        with patch.object(screen_ocr_engine, "extract_text", new_callable=AsyncMock) as mock_ext:
            with patch.object(screen_vision_analyzer, "find_available_vision_model", new_callable=AsyncMock) as m_vlm:
                m_vlm.return_value = None
                mock_ext.return_value = mock_ocr

                res = await screen_vision_analyzer.analyze_screen(query="ما هو الخطأ في الشاشة؟")
                assert res["success"] is True
                assert res["ocr_line_count"] == 1
                assert "NullReference" in res["ocr_text_preview"]
