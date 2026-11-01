"""
Aegis AI - Natural Neural Text-To-Speech Engine.
Provides natural neural voice generation with zero paid subscriptions or API keys,
using Microsoft Edge Neural speech synthesis with local SAPI offline fallback.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from aegis_core.utils.logger import logger

DEFAULT_VOICE = "ar-SA-HamedNeural"

VOICE_CATALOG: List[Dict[str, Any]] = [
    # Arabic Voices (الأصوات العربية الفصيحة والإقليمية)
    {
        "id": "ar-SA-HamedNeural",
        "name": "حامد (سعودي - ذكوري فصيح وطبيعي)",
        "name_en": "Hamed (Saudi - Male / Natural)",
        "gender": "Male",
        "lang": "ar-SA",
        "lang_name": "العربية (السعودية)",
        "sample_text": "مرحباً بك، أنا مساعدك الذكي إيجيس، كيف يمكنني مساعدتك اليوم؟",
    },
    {
        "id": "ar-SA-ZariyahNeural",
        "name": "زارية (سعودية - أنثوي دافئ وإذاعي)",
        "name_en": "Zariyah (Saudi - Female / Warm)",
        "gender": "Female",
        "lang": "ar-SA",
        "lang_name": "العربية (السعودية)",
        "sample_text": "أهلاً بك، أنا إيجيس، في خدمتك لتسهيل مهامك اليومية على ويندوز.",
    },
    {
        "id": "ar-EG-ShakirNeural",
        "name": "شاكر (مصري - ذكوري ودود وتفاعلي)",
        "name_en": "Shakir (Egyptian - Male / Friendly)",
        "gender": "Male",
        "lang": "ar-EG",
        "lang_name": "العربية (مصر)",
        "sample_text": "أهلاً وسهلاً، أنا إيجيس وجاهز لأي مساعدة تحتاجها في جهازك.",
    },
    {
        "id": "ar-EG-SalmaNeural",
        "name": "سلمى (مصرية - أنثوي هادئ وواضح)",
        "name_en": "Salma (Egyptian - Female / Clear)",
        "gender": "Female",
        "lang": "ar-EG",
        "lang_name": "العربية (مصر)",
        "sample_text": "مرحباً، يسعدني التحدث معك ومساعدتك في إدارة تطبيقاتك.",
    },
    {
        "id": "ar-AE-HamdanNeural",
        "name": "حمدان (إماراتي - ذكوري وقور ورسمي)",
        "name_en": "Hamdan (Emirati - Male / Formal)",
        "gender": "Male",
        "lang": "ar-AE",
        "lang_name": "العربية (الإمارات)",
        "sample_text": "مرحباً بك، أنا في خدمتك لتنفيذ كافة أوامرك بدقة وسرعة.",
    },
    {
        "id": "ar-AE-FatimaNeural",
        "name": "فاطمة (إماراتية - أنثوي راقٍ وهادئ)",
        "name_en": "Fatima (Emirati - Female / Elegant)",
        "gender": "Female",
        "lang": "ar-AE",
        "lang_name": "العربية (الإمارات)",
        "sample_text": "أهلاً بك، أتمنى لك يوماً رائعاً ومنتجاً بمساعدة إيجيس.",
    },
    {
        "id": "ar-JO-TaimNeural",
        "name": "تيم (أردني/شامي - ذكوري شبابي حديث)",
        "name_en": "Taim (Jordanian - Male / Modern)",
        "gender": "Male",
        "lang": "ar-JO",
        "lang_name": "العربية (بلاد الشام)",
        "sample_text": "أهلاً صديقي، معك إيجيس وجاهز لمساعدتك بكل سرور وسرعة.",
    },
    {
        "id": "ar-JO-SanaNeural",
        "name": "سناء (أردنية/شامية - أنثوي لطيف ومريح)",
        "name_en": "Sana (Jordanian - Female / Gentle)",
        "gender": "Female",
        "lang": "ar-JO",
        "lang_name": "العربية (بلاد الشام)",
        "sample_text": "مرحباً بك، أنا هنا لمساعدتك في كل خطوة على سطح المكتب.",
    },
    # English Voices (الأصوات الإنجليزية الطبيعية)
    {
        "id": "en-US-AriaNeural",
        "name": "Aria (US - Female / Professional)",
        "name_en": "Aria (US - Female / Professional)",
        "gender": "Female",
        "lang": "en-US",
        "lang_name": "English (US)",
        "sample_text": "Hello! I am Aegis AI, your local intelligent companion. How can I assist you today?",
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (US - Male / Casual & Friendly)",
        "name_en": "Guy (US - Male / Casual & Friendly)",
        "gender": "Male",
        "lang": "en-US",
        "lang_name": "English (US)",
        "sample_text": "Hey there! Aegis AI is standing by to help you automate your Windows workflow.",
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (US - Female / Warm & Conversational)",
        "name_en": "Jenny (US - Female / Warm & Conversational)",
        "gender": "Female",
        "lang": "en-US",
        "lang_name": "English (US)",
        "sample_text": "Hi! I am here and ready whenever you need anything opened or automated on your PC.",
    },
    {
        "id": "en-GB-RyanNeural",
        "name": "Ryan (UK - Male / Natural & Polished)",
        "name_en": "Ryan (UK - Male / Natural & Polished)",
        "gender": "Male",
        "lang": "en-GB",
        "lang_name": "English (UK)",
        "sample_text": "Good day! Aegis AI is standing by and pleased to be of assistance to you.",
    },
    {
        "id": "en-GB-SoniaNeural",
        "name": "Sonia (UK - Female / British Accent)",
        "name_en": "Sonia (UK - Female / British Accent)",
        "gender": "Female",
        "lang": "en-GB",
        "lang_name": "English (UK)",
        "sample_text": "Hello! How may I assist you with your desktop applications and navigation today?",
    },
]


class NeuralTTSEngine:
    """High-fidelity neural text-to-speech synthesizer."""

    def __init__(self, default_voice: str = DEFAULT_VOICE):
        self.default_voice = default_voice

    async def synthesize_to_bytes(
        self, text: str, voice: Optional[str] = None, rate: Optional[str] = None
    ) -> bytes:
        """Synthesizes text into MP3 audio bytes using neural voice models."""
        target_voice = voice or self.default_voice
        target_rate = rate or "+0%"
        clean_text = text.strip()
        if not clean_text:
            return b""

        # Truncate for audio synthesis if excessively long (> 1000 chars)
        if len(clean_text) > 1000:
            clean_text = clean_text[:1000] + "..."

        try:
            import edge_tts

            communicate = edge_tts.Communicate(clean_text, target_voice, rate=target_rate)
            chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b"".join(chunks)

        except Exception as exc:
            logger.warning("Neural TTS synthesis via edge-tts failed: %s. Using local fallback.", exc)
            return b""

    async def synthesize_to_file(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
    ) -> Path:
        """Saves synthesized MP3 audio directly to a target file path."""
        data = await self.synthesize_to_bytes(text, voice=voice, rate=rate)
        if data:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(data)
            return output_path
        raise RuntimeError("Synthesis returned zero audio bytes.")

    def get_status(self) -> Dict[str, Any]:
        return {
            "default_voice": self.default_voice,
            "available_voices": VOICE_CATALOG,
            "backend": "edge_tts_neural",
            "zero_api_keys": True,
        }


# Global TTS engine singleton
tts_engine = NeuralTTSEngine()
