"""
Aegis AI - Natural Language Intent Router & Fast Classifier.
Classifies user speech or typed queries into actionable desktop commands or conversational LLM reasoning
with zero latency, zero cloud APIs, and bilingual (English + Arabic) entity extraction.
"""

from enum import Enum
import re
from typing import Any, Dict, Optional


class UserIntent(str, Enum):
    APP_LAUNCH = "app_launch"
    APP_CLOSE = "app_close"
    OPEN_URL = "open_url"
    WINDOW_ACTION = "window_action"
    SYSTEM_QUERY = "system_query"
    CLIPBOARD = "clipboard"
    VOLUME = "volume"
    BRIGHTNESS = "brightness"
    SCREEN_CAPTURE = "screen_capture"
    NOTES = "notes"
    CONVERSATION = "conversation"


# Common Arabic friendly names for Windows apps and tools
ARABIC_APP_TRANSLATIONS = {
    "كروم": "chrome",
    "جوجل كروم": "chrome",
    "المفكرة": "notepad",
    "مفكرة": "notepad",
    "النوتة": "notepad",
    "المذكرة": "notepad",
    "الحاسبة": "calc",
    "حاسبة": "calc",
    "الة حاسبة": "calc",
    "الالة الحاسبة": "calc",
    "الآلة الحاسبة": "calc",
    "الرسام": "mspaint",
    "رسام": "mspaint",
    "كود": "code",
    "في اس كود": "code",
    "فيجوال ستوديو كود": "code",
    "كومت": "comet",
    "متصفح كومت": "comet",
    "المتصفح": "chrome",
    "متصفح": "chrome",
    "ايدج": "msedge",
    "إيدج": "msedge",
    "مايكروسوفت ايدج": "msedge",
    "بريف": "brave",
    "فايرفوكس": "firefox",
    "مدير المهام": "taskmgr",
    "التاسك مانجر": "taskmgr",
    "الاعدادات": "ms-settings:",
    "مستكشف الملفات": "explorer",
    "الملفات": "explorer",
    "الطرفية": "cmd",
    "تيرمينال": "wt",
}

# Arabic and shortcut website friendly names
ARABIC_URL_TRANSLATIONS = {
    "يوتيوب": "https://www.youtube.com",
    "youtube": "https://www.youtube.com",
    "جوجل": "https://www.google.com",
    "غوغل": "https://www.google.com",
    "google": "https://www.google.com",
    "غيتهاب": "https://www.github.com",
    "جيت هاب": "https://www.github.com",
    "جيت_هاب": "https://www.github.com",
    "github": "https://www.github.com",
    "تويتر": "https://x.com",
    "twitter": "https://x.com",
    "اكس": "https://x.com",
    "فيسبوك": "https://www.facebook.com",
    "فيس بوك": "https://www.facebook.com",
    "facebook": "https://www.facebook.com",
    "شات جي بي تي": "https://chatgpt.com",
    "شات_جي_بي_تي": "https://chatgpt.com",
    "chatgpt": "https://chatgpt.com",
    "جيميل": "https://mail.google.com",
    "gmail": "https://mail.google.com",
    "لينكد ان": "https://www.linkedin.com",
    "لينكد_ان": "https://www.linkedin.com",
    "linkedin": "https://www.linkedin.com",
    "واتساب": "https://web.whatsapp.com",
    "whatsapp": "https://web.whatsapp.com",
    "reddit": "https://www.reddit.com",
}


def normalize_spoken_arabic_text(text: str) -> str:
    """
    Normalizes spoken Arabic phonetics into internet standards:
    - Spoken domain suffixes: "دوت نت" -> ".net", "دوت كوم" -> ".com", "دوت اورج" -> ".org", etc.
    - Spoken "نقطة" -> "."
    """
    t = text.strip()
    domain_map = [
        (r"\s*(?:دوت|نقطة)\s*(?:نت|net)\b", ".net"),
        (r"\s*(?:دوت|نقطة)\s*(?:كوم|com)\b", ".com"),
        (r"\s*(?:دوت|نقطة)\s*(?:اورج|org)\b", ".org"),
        (r"\s*(?:دوت|نقطة)\s*(?:اي\s*او|io)\b", ".io"),
        (r"\s*(?:دوت|نقطة)\s*(?:ايه\s*اي|اي|ai)\b", ".ai"),
        (r"\s*(?:دوت|نقطة)\s*(?:كو|co)\b", ".co"),
        (r"\s*(?:دوت|نقطة)\s*(?:ديف|dev)\b", ".dev"),
        (r"\s*(?:دوت|نقطة)\s*(?:اب|app)\b", ".app"),
        (r"\s*(?:دوت|نقطة)\s*(?:مي|me)\b", ".me"),
    ]
    for pat, repl in domain_map:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)
    return t


class IntentRouter:
    """Fast, zero-latency natural language intent classifier supporting English & Arabic."""

    # Regex patterns for high-frequency Windows desktop operations
    APP_LAUNCH_PATTERNS = [
        (
            r"^(?:please\s+)?(?:can\s+you\s+)?(?:please\s+)?"
            r"(?:open|launch|start|run|fire\s+up)\s+(?:the\s+)?(?P<app>.+?)(?:\s+please)?$"
        ),
        r"^(?:start\s+up|open\s+up)\s+(?P<app>.+?)(?:\s+please)?$",
        (
            r"^(?:ممكن\s+)?(?:افتح|شغل|شغلي|افتحلي|ابدأ)(?:\s+لي)?\s+"
            r"(?:برنامج|تطبيق|متصفح)?\s*(?P<app>.+?)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$"
        ),
    ]

    APP_CLOSE_PATTERNS = [
        (
            r"^(?:please\s+)?(?:can\s+you\s+)?(?:please\s+)?"
            r"(?:close|kill|quit|terminate|exit)\s+(?:the\s+)?(?P<app>.+?)(?:\s+please)?$"
        ),
        r"^(?:force\s+close|shut\s+down)\s+(?P<app>.+?)(?:\s+please)?$",
        (
            r"^(?:ممكن\s+)?(?:اغلق|قفل|سكر|طفي|انهي|وقف)(?:\s+لي)?\s+"
            r"(?:برنامج|تطبيق|متصفح)?\s*(?P<app>.+?)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$"
        ),
    ]

    WINDOW_MINIMIZE_ALL_PATTERNS = [
        (
            r"^(?:please\s+)?"
            r"(?:minimize\s+all(?:\s+windows)?|show\s+desktop|hide\s+all\s+windows|clear\s+screen)"
            r"(?:\s+please)?$"
        ),
        (
            r"^(?:ممكن\s+)?(?:صغر\s+(?:كل\s+)?ال?نوافذ|اظهر\s+سطح\s+المكتب|سطح\s+المكتب|"
            r"نزل\s+كل\s+شي|اخفي\s+ال?نوافذ)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$"
        ),
    ]

    WINDOW_SNAP_PATTERNS = [
        (
            r"^(?:please\s+)?"
            r"(?:snap|tile|dock|move)(?:\s+window)?\s+(?:to\s+the\s+)?(?P<side>left|right)"
            r"(?:\s+please)?$"
        ),
        r"^(?:please\s+)?(?:maximize\s+window|maximize|unmaximize|restore\s+window)(?:\s+please)?$",
        r"^(?:ممكن\s+)?(?:كبر\s+ال?نافذة|ملء\s+الشاشة|ماكسيمايز)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
        r"^(?:ممكن\s+)?(?:قسم\s+ل?ليمين|حط\s+ال?نافذة\s+يمين|يمين\s+الشاشة|انقل\s+يمين)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
        r"^(?:ممكن\s+)?(?:قسم\s+ل?ليسار|حط\s+ال?نافذة\s+يسار|يسار\s+الشاشة|انقل\s+يسار)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
    ]

    WINDOW_FOCUS_PATTERNS = [
        (
            r"^(?:please\s+)?(?:bring|focus|switch\s+to)\s+(?:the\s+)?"
            r"(?P<app>.+?)(?:\s+to\s+front|\s+window)?(?:\s+please)?$"
        ),
    ]

    SYSTEM_QUERY_PATTERNS = [
        (
            r"^(?:what\s+is\s+my|show|get|check)?\s*"
            r"(?:system\s+telemetry|system\s+info|system\s+status|"
            r"cpu\s+usage|memory\s+usage|ram\s+usage|battery|specs)$"
        ),
        (
            r"^(?:ممكن\s+)?(?:معلومات\s+النظام|مواصفات\s+الجهاز|استهلاك\s+المعالج|الرام|حالة\s+الجهاز)"
            r"(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$"
        ),
    ]

    CLIPBOARD_PATTERNS = [
        r"^(?:what(?:'s|\s+is)\s+on\s+my\s+clipboard|get\s+clipboard|read\s+clipboard|show\s+clipboard)$",
        r"^(?:ممكن\s+)?(?:اقرأ\s+الحافظة|شو\s+بالحافظة|محتوى\s+الحافظة|الحافظة)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
    ]

    SCREEN_CAPTURE_PATTERNS = [
        (
            r"^(?:please\s+)?"
            r"(?:take\s+a\s+screenshot|capture\s+screen|take\s+screenshot|screenshot|capture\s+desktop)"
            r"(?:\s+please)?$"
        ),
        (
            r"^(?:ممكن\s+)?(?:صور\s+الشاشة|خد\s+لقطة\s+شاشة|لقطة\s+شاشة|سكرين\s*شوت|كبشر\s+الشاشة)"
            r"(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$"
        ),
    ]

    @classmethod
    def classify_and_route(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Classifies input text and returns a tool call dictionary if an actionable
        local intent is detected, or None for general conversation.
        """
        raw = text.strip()
        low = raw.lower()
        norm_raw = normalize_spoken_arabic_text(raw)

        # 0. First-Class Web / URL Opening (Arabic & English)
        # 0.1 Arabic Compound Browser-First (e.g. "كروم و افتح موقع كود التطور دوت نت", "افتح كروم وافتح موقع ...")
        m_ar_compound = re.match(
            r"^(?:ممكن\s+)?(?:افتح|شغل)?\s*(?:متصفح\s+)?(?P<browser>كروم|جوجل\s+كروم|كومت|ايدج|إيدج|بريف|فايرفوكس)\s+"
            r"(?:و\s*|ثم\s*)?(?:افتح|شغل|روّح|اذهب|تصفح)?(?:\s+لي)?\s+(?:موقع|صفحة)?\s*"
            r"(?P<target>.+?)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            norm_raw,
            re.IGNORECASE,
        )
        if m_ar_compound:
            tgt = m_ar_compound.group("target").strip()
            br = m_ar_compound.group("browser").strip()
            resolved_url = ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            resolved_browser = ARABIC_APP_TRANSLATIONS.get(br, br)
            return {
                "intent": UserIntent.OPEN_URL,
                "name": "open_url",
                "arguments": {"url": resolved_url, "browser": resolved_browser},
            }

        # 0.2 Arabic Target-First with Browser (e.g. "افتح موقع كود التطور بكروم", "افتح موقع كود التطور بمتصفح كروم")
        m_ar_target_br = re.match(
            r"^(?:ممكن\s+)?(?:افتح|شغل|روّح|اذهب|تصفح)?(?:\s+لي)?\s+(?:موقع|صفحة)?\s*"
            r"(?P<target>.+?)\s+(?:بمتصفح\s+|في\s+متصفح\s+|عبر\s+متصفح\s+|في\s+|عبر\s+|ب\s+|ب)"
            r"(?P<browser>كروم|جوجل\s+كروم|كومت|ايدج|إيدج|بريف|فايرفوكس)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            norm_raw,
            re.IGNORECASE,
        )
        if m_ar_target_br:
            tgt = m_ar_target_br.group("target").strip()
            br = m_ar_target_br.group("browser").strip()
            resolved_url = ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            resolved_browser = ARABIC_APP_TRANSLATIONS.get(br, br)
            return {
                "intent": UserIntent.OPEN_URL,
                "name": "open_url",
                "arguments": {"url": resolved_url, "browser": resolved_browser},
            }

        # 0.3 Arabic Site-only (e.g. "افتح موقع كود التطور دوت نت", "افتح موقع يوتيوب")
        m_ar_site = re.match(
            r"^(?:ممكن\s+)?(?:افتح|شغل|روّح|اذهب|تصفح)?(?:\s+لي)?\s+(?:موقع|صفحة)\s+"
            r"(?P<target>.+?)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            norm_raw,
            re.IGNORECASE,
        )
        if m_ar_site:
            tgt = m_ar_site.group("target").strip()
            resolved_url = ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            return {
                "intent": UserIntent.OPEN_URL,
                "name": "open_url",
                "arguments": {"url": resolved_url, "browser": ""},
            }

        # 0.4 Direct Known Web Domains or URLs
        m_ar_url = re.match(
            r"^(?:ممكن\s+)?(?:افتح|شغل|روّح|اذهب|تصفح)?(?:\s+لي)?\s*(?:موقع|صفحة)?\s*"
            r"(?P<target>https?://\S+|.+\.(?:net|com|org|io|ai|co|dev|app|me)|[a-zA-Z0-9_-]+|يوتيوب|جوجل|غوغل|غيتهاب|"
            r"جيت\s*هاب|تويتر|فيسبوك|شات\s*جي\s*بي\s*تي|جيميل|واتساب)"
            r"(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            norm_raw,
            re.IGNORECASE,
        )
        if m_ar_url:
            tgt = m_ar_url.group("target").strip()
            resolved_url = ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            return {
                "intent": UserIntent.OPEN_URL,
                "name": "open_url",
                "arguments": {"url": resolved_url, "browser": ""},
            }

        # English URL pattern: e.g. "open youtube in chrome", "open https://google.com in comet", "go to github.com"
        m_en_url = re.match(
            r"^(?:please\s+)?(?:open|launch|visit|go\s+to)\s+(?:the\s+)?(?:website|site|url|page)?\s*"
            r"(?P<target>https?://\S+|www\.\S+|\S+\.(?:com|org|net|io|edu|gov|co|ai|app|dev)|"
            r"youtube|google|github|twitter|facebook|reddit|chatgpt)"
            r"(?:\s+in\s+(?P<browser>chrome|edge|msedge|brave|firefox|comet))?(?:\s+please)?$",
            low,
        )
        if m_en_url:
            tgt = m_en_url.group("target").strip()
            br = (m_en_url.group("browser") or "").strip()
            resolved_url = ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            return {
                "intent": UserIntent.OPEN_URL,
                "name": "open_url",
                "arguments": {"url": resolved_url, "browser": br},
            }

        # 1. Volume Controls (Bilingual)
        if re.match(
            r"^(?:please\s+)?(?:mute|mute\s+audio|mute\s+sound|silence)(?:\s+please)?$", low
        ) or re.match(
            r"^(?:ممكن\s+)?(?:كتم\s+الصوت|اكتم\s+الصوت|صامت|اسكت|ميوت)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$", raw
        ):
            return {"intent": UserIntent.VOLUME, "name": "control_volume", "arguments": {"action": "mute"}}

        if re.match(
            r"^(?:please\s+)?(?:unmute|unmute\s+audio|unmute\s+sound)(?:\s+please)?$", low
        ) or re.match(
            r"^(?:ممكن\s+)?(?:شغل\s+الصوت|فك\s+الكتم|رجع\s+الصوت|صوت|"
            r"إلغاء\s+كتم\s+الصوت|الغاء\s+كتم\s+الصوت)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ):
            return {"intent": UserIntent.VOLUME, "name": "control_volume", "arguments": {"action": "unmute"}}

        m_vol_set = re.match(
            r"^(?:please\s+)?(?:set\s+)?volume\s+(?:to\s+)?(?P<lvl>\d+)\%?(?:\s+please)?$", low
        ) or re.match(
            r"^(?:ممكن\s+)?(?:اضبط\s+الصوت|خلي\s+الصوت|حط\s+الصوت)"
            r"(?:\s+على|\s+الى|\s+ل)?\s*(?P<lvl>\d+)\%?(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        )
        if m_vol_set:
            lvl = int(m_vol_set.group("lvl"))
            return {
                "intent": UserIntent.VOLUME,
                "name": "control_volume",
                "arguments": {"action": "set", "level": lvl},
            }

        if re.match(
            r"^(?:please\s+)?(?:turn\s+)?(?:volume\s+up|increase\s+volume|louder|raise\s+volume)(?:\s+please)?$",
            low,
        ) or re.match(
            r"^(?:ممكن\s+)?(?:ارفع\s+الصوت|علي\s+الصوت|زيد\s+الصوت|صوت\s+اعلى)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$", raw
        ):
            return {
                "intent": UserIntent.VOLUME,
                "name": "control_volume",
                "arguments": {"action": "increase", "level": 10},
            }

        if re.match(
            r"^(?:please\s+)?(?:turn\s+)?(?:volume\s+down|decrease\s+volume|quieter|lower\s+volume)(?:\s+please)?$",
            low,
        ) or re.match(
            r"^(?:ممكن\s+)?(?:اخفض\s+الصوت|وطي\s+الصوت|قصر\s+الصوت|نزل\s+الصوت|صوت\s+اوطى)"
            r"(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ):
            return {
                "intent": UserIntent.VOLUME,
                "name": "control_volume",
                "arguments": {"action": "decrease", "level": 10},
            }

        # 2. Brightness Controls (Bilingual)
        m_br_set = re.match(
            r"^(?:please\s+)?(?:set\s+)?brightness\s+(?:to\s+)?(?P<lvl>\d+)\%?(?:\s+please)?$", low
        ) or re.match(
            r"^(?:ممكن\s+)?(?:اضبط\s+السطوع|خلي\s+السطوع|حط\s+السطوع|خلي\s+الاضاءة)"
            r"(?:\s+على|\s+الى|\s+ل)?\s*(?P<lvl>\d+)\%?(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        )
        if m_br_set:
            lvl = int(m_br_set.group("lvl"))
            return {
                "intent": UserIntent.BRIGHTNESS,
                "name": "control_brightness",
                "arguments": {"action": "set", "level": lvl},
            }

        if re.match(
            r"^(?:please\s+)?(?:increase\s+brightness|brighter|raise\s+brightness|brightness\s+up)(?:\s+please)?$",
            low,
        ) or re.match(
            r"^(?:ممكن\s+)?(?:ارفع\s+السطوع|علي\s+الاضاءة|زيد\s+السطوع|شاشة\s+اوضح)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$", raw
        ):
            return {
                "intent": UserIntent.BRIGHTNESS,
                "name": "control_brightness",
                "arguments": {"action": "increase", "level": 10},
            }

        if re.match(
            r"^(?:please\s+)?(?:decrease\s+brightness|dimmer|dim\s+screen|dim\s+display|"
            r"dim|lower\s+brightness|brightness\s+down)(?:\s+please)?$",
            low,
        ) or re.match(
            r"^(?:ممكن\s+)?(?:اخفض\s+السطوع|وطي\s+الاضاءة|قصر\s+السطوع|قلل\s+الاضاءة)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ):
            return {
                "intent": UserIntent.BRIGHTNESS,
                "name": "control_brightness",
                "arguments": {"action": "decrease", "level": 10},
            }

        # 3. Screen Capture (Bilingual)
        for pat in cls.SCREEN_CAPTURE_PATTERNS:
            if re.match(pat, low) or re.match(pat, raw):
                return {
                    "intent": UserIntent.SCREEN_CAPTURE,
                    "name": "capture_screen",
                    "arguments": {"target": "full"},
                }

        # 4. Quick Notes (Bilingual)
        m_note_append = re.match(
            r"^(?:please\s+)?(?:note|add\s+note|quick\s+note|remember|take\s+note|write\s+down)\s*"
            r"[:\-]?\s*(?P<text>.+)$",
            raw,
            re.IGNORECASE,
        ) or re.match(
            r"^(?:ممكن\s+)?(?:سجل\s+ملاحظة|اكتب\s+ملاحظة|ملاحظة|دون)(?:\s+بتقول|\s+بانها|\s+:)?\s*(?P<text>.+)$",
            raw,
        )
        if m_note_append:
            note_txt = m_note_append.group("text").strip()
            return {
                "intent": UserIntent.NOTES,
                "name": "manage_notes",
                "arguments": {"action": "append", "text": note_txt},
            }

        if re.match(
            r"^(?:please\s+)?(?:show|read|view|get|list)?\s*(?:today'?s\s+)?notes(?:\s+please)?$",
            low,
        ) or re.match(
            r"^(?:ممكن\s+)?(?:اقرأ|عرض|شوف|افتح|شو)?\s*"
            r"(?:ملاحظات\s+اليوم|ملاحظاتي|الملاحظات)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ):
            return {
                "intent": UserIntent.NOTES,
                "name": "manage_notes",
                "arguments": {"action": "read_today"},
            }

        m_note_search = re.match(
            r"^(?:please\s+)?(?:search\s+notes\s+for|find\s+in\s+notes|search\s+notes)\s+(?P<query>.+)$",
            raw,
            re.IGNORECASE,
        ) or re.match(
            r"^(?:ممكن\s+)?(?:ابحث\s+في\s+الملاحظات\s+عن|دور\s+في\s+الملاحظات\s+على|ابحث\s+بالملاحظات\s+عن)\s+"
            r"(?P<query>.+)$",
            raw,
        )
        if m_note_search:
            q = m_note_search.group("query").strip()
            return {
                "intent": UserIntent.NOTES,
                "name": "manage_notes",
                "arguments": {"action": "search", "query": q},
            }

        # 5. Window Minimize All / Show Desktop (Bilingual)
        for pat in cls.WINDOW_MINIMIZE_ALL_PATTERNS:
            if re.match(pat, low) or re.match(pat, raw):
                return {
                    "intent": UserIntent.WINDOW_ACTION,
                    "name": "minimize_all_windows",
                    "arguments": {},
                }

        # 6. Window Snapping (left, right, maximize)
        for pat in cls.WINDOW_SNAP_PATTERNS:
            m = re.match(pat, low) or re.match(pat, raw)
            if m:
                text_matched = m.group(0)
                if "يمين" in text_matched or "right" in text_matched:
                    side = "right"
                elif "يسار" in text_matched or "left" in text_matched:
                    side = "left"
                elif any(k in text_matched for k in ["كبر", "ملء", "maximize"]):
                    side = "maximize"
                else:
                    side = "restore"

                return {
                    "intent": UserIntent.WINDOW_ACTION,
                    "name": "snap_window",
                    "arguments": {"side": side},
                }

        # 7. Window Focus / Bring to Front
        for pat in cls.WINDOW_FOCUS_PATTERNS:
            m = re.match(pat, low)
            if m:
                app = m.group("app").strip()
                if app not in ["it", "this", "that"]:
                    return {
                        "intent": UserIntent.WINDOW_ACTION,
                        "name": "focus_window_by_title",
                        "arguments": {"title_query": app},
                    }

        # 8. App Launching (Bilingual)
        for pat in cls.APP_LAUNCH_PATTERNS:
            m = re.match(pat, low) or re.match(pat, raw)
            if m:
                app = m.group("app").strip()
                # Translate Arabic app names to system executable tokens
                translated_app = ARABIC_APP_TRANSLATIONS.get(app, app)

                if "clipboard" in app or "الحافظة" in app:
                    return {
                        "intent": UserIntent.CLIPBOARD,
                        "name": "get_clipboard",
                        "arguments": {},
                    }
                if any(k in app for k in ["system", "telemetry", "specs", "cpu", "نظام", "مواصفات"]):
                    return {
                        "intent": UserIntent.SYSTEM_QUERY,
                        "name": "get_system_telemetry",
                        "arguments": {},
                    }
                return {
                    "intent": UserIntent.APP_LAUNCH,
                    "name": "launch_application",
                    "arguments": {"app_name": translated_app},
                }

        # 9. App Closing (Bilingual)
        for pat in cls.APP_CLOSE_PATTERNS:
            m = re.match(pat, low) or re.match(pat, raw)
            if m:
                app = m.group("app").strip()
                translated_app = ARABIC_APP_TRANSLATIONS.get(app, app)
                return {
                    "intent": UserIntent.APP_CLOSE,
                    "name": "close_application",
                    "arguments": {"process_name": translated_app},
                }

        # 10. System Queries (Bilingual)
        for pat in cls.SYSTEM_QUERY_PATTERNS:
            if re.match(pat, low) or re.match(pat, raw):
                return {
                    "intent": UserIntent.SYSTEM_QUERY,
                    "name": "get_system_telemetry",
                    "arguments": {},
                }

        # 11. Clipboard Queries (Bilingual)
        for pat in cls.CLIPBOARD_PATTERNS:
            if re.match(pat, low) or re.match(pat, raw):
                return {
                    "intent": UserIntent.CLIPBOARD,
                    "name": "get_clipboard",
                    "arguments": {},
                }

        # Default: Conversation / ReAct LLM Reasoning
        return None
