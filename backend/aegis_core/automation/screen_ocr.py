"""
Aegis AI - Native Windows Screen OCR Engine.
Extracts pixel-level text from active desktop windows and screenshots
using Windows Media OCR APIs with sub-150ms latency and 100% offline privacy.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from PIL import Image
from aegis_core.automation.screen_capture import screen_capture
from aegis_core.utils.logger import logger


class ScreenOCREngine:
    """Provides high-performance native Windows OCR screen text recognition."""

    def __init__(self, default_lang: str = "ar-SA"):
        self.default_lang = default_lang
        self._available_languages: Optional[List[str]] = None

    def get_available_languages(self) -> List[str]:
        """Returns list of installed Windows OCR language tags."""
        if self._available_languages is not None:
            return self._available_languages

        try:
            import winocr
            langs = [lang_obj.language_tag for lang_obj in winocr.OcrEngine.available_recognizer_languages]
            self._available_languages = langs
            return langs
        except Exception as exc:
            logger.debug("Failed checking Windows OCR languages: %s", exc)
            return ["ar-SA", "en-US"]

    def resolve_language(self, preferred_lang: Optional[str] = None) -> str:
        """Resolves preferred language against installed Windows OCR engines."""
        installed = self.get_available_languages()
        if not installed:
            return "en-US"

        if preferred_lang:
            # Direct match
            for tag in installed:
                if tag.lower() == preferred_lang.lower() or tag.lower().startswith(preferred_lang.lower()):
                    return tag

        # Check default
        for tag in installed:
            if tag.lower().startswith("ar") and self.default_lang.startswith("ar"):
                return tag

        return installed[0]

    async def extract_text(
        self,
        image_or_path: Optional[Union[str, Path, Image.Image]] = None,
        lang: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extracts text from given image or captures the active desktop screen live.
        Returns detailed structured text, lines count, and performance latency.
        """
        start_time = time.perf_counter()
        target_lang = self.resolve_language(lang)

        # 1. Acquire Image
        img: Optional[Image.Image] = None
        capture_meta: Dict[str, Any] = {}

        if image_or_path is None:
            # Capture live desktop
            cap_res = screen_capture.capture()
            if not cap_res.get("success") or not cap_res.get("path"):
                return {
                    "success": False,
                    "text": "",
                    "lines": [],
                    "error": cap_res.get("message", "Screen capture failed."),
                    "latency_ms": 0.0,
                }
            capture_meta = cap_res
            img = Image.open(cap_res["path"])
        elif isinstance(image_or_path, (str, Path)):
            img = Image.open(image_or_path)
        elif isinstance(image_or_path, Image.Image):
            img = image_or_path

        if img is None:
            return {
                "success": False,
                "text": "",
                "lines": [],
                "error": "No valid image provided for OCR.",
                "latency_ms": 0.0,
            }

        # 2. Run Native Windows OCR
        try:
            import winocr

            ocr_res = await winocr.recognize_pil(img, target_lang)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            raw_text = (ocr_res.text or "").strip()
            lines = [line.text for line in getattr(ocr_res, "lines", []) if line.text.strip()]

            logger.info(
                "Windows OCR extracted %d lines (%d chars) using %s in %.1f ms.",
                len(lines),
                len(raw_text),
                target_lang,
                latency_ms,
            )

            return {
                "success": True,
                "text": raw_text,
                "lines": lines,
                "line_count": len(lines),
                "word_count": len(raw_text.split()),
                "language": target_lang,
                "latency_ms": latency_ms,
                "capture_meta": capture_meta,
            }

        except Exception as exc:
            logger.error("Native Windows OCR execution failed: %s", exc)
            return {
                "success": False,
                "text": "",
                "lines": [],
                "error": str(exc),
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
            }


# Singleton instance
screen_ocr_engine = ScreenOCREngine()
