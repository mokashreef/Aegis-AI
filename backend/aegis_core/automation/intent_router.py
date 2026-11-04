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
    VISION_ANALYSIS = "vision_analysis"
    DOCUMENT_RAG = "document_rag"
    TIMER = "timer"
    REMINDER = "reminder"
    MEDIA = "media"
    NOTES = "notes"
    CONVERSATION = "conversation"


# Common Arabic friendly names for Windows apps and tools
ARABIC_APP_TRANSLATIONS: Dict[str, str] = {
    "كروم": "chrome",
    "جوجل كروم": "chrome",
    "قووقل كروم": "chrome",
    "المفكرة": "notepad",
    "مفكرة": "notepad",
    "نوتباد": "notepad",
    "النوتة": "notepad",
    "المذكرة": "notepad",
    "الحاسبة": "calc",
    "حاسبة": "calc",
    "الة حاسبة": "calc",
    "الالة الحاسبة": "calc",
    "الآلة الحاسبة": "calc",
    "كالكوليتر": "calc",
    "الرسام": "mspaint",
    "رسام": "mspaint",
    "بينت": "mspaint",
    "كود": "code",
    "في اس كود": "code",
    "فيجوال ستوديو كود": "code",
    "فيجوال استديو كود": "code",
    "فيجوال ستوديو": "code",
    "فيجوال استديو": "code",
    "فيجوال استوديو": "code",
    "فيجوال كود": "code",
    "كومت": "comet",
    "متصفح كومت": "comet",
    "المتصفح": "chrome",
    "متصفح": "chrome",
    "متصفح كروم": "chrome",
    "ايدج": "msedge",
    "إيدج": "msedge",
    "متصفح ايدج": "msedge",
    "مايكروسوفت ايدج": "msedge",
    "بريف": "brave",
    "متصفح بريف": "brave",
    "فايرفوكس": "firefox",
    "متصفح فايرفوكس": "firefox",
    "تيليجرام": "telegram",
    "تليجرام": "telegram",
    "واتساب": "whatsapp",
    "واتس اب": "whatsapp",
    "ديسكورد": "discord",
    "سبوتيفاي": "spotify",
    "ستيم": "steam",
    "وورد": "winword",
    "الوورد": "winword",
    "اكسل": "excel",
    "إكسل": "excel",
    "الاكسل": "excel",
    "باوربوينت": "powerpnt",
    "بوربوينت": "powerpnt",
    "الباوربوينت": "powerpnt",
    "فوتوشوب": "photoshop",
    "الفوتوشوب": "photoshop",
    "مدير المهام": "taskmgr",
    "التاسك مانجر": "taskmgr",
    "الاعدادات": "ms-settings:",
    "الإعدادات": "ms-settings:",
    "ضبط الجهاز": "ms-settings:",
    "لوحة التحكم": "control",
    "مستكشف الملفات": "explorer",
    "الملفات": "explorer",
    "المجلدات": "explorer",
    "الطرفية": "cmd",
    "تيرمينال": "wt",
    "موجه الاوامر": "cmd",
    "موجه الأوامر": "cmd",
    "باورشيل": "powershell",
    "باور شيل": "powershell",
    "تيمز": "teams",
    "زووم": "zoom",
}

# Arabic and shortcut website friendly names
ARABIC_URL_TRANSLATIONS: Dict[str, str] = {
    # Evolution Code / Core platforms
    "كود التطور": "https://codealtatawor.net",
    "كود_التطور": "https://codealtatawor.net",
    "موقع كود التطور": "https://codealtatawor.net",
    "codealtatawor": "https://codealtatawor.net",

    # AI & Developer Tools
    "شات جي بي تي": "https://chatgpt.com",
    "شات_جي_بي_تي": "https://chatgpt.com",
    "chatgpt": "https://chatgpt.com",
    "openai": "https://openai.com",
    "كلاود": "https://claude.ai",
    "كلود": "https://claude.ai",
    "claude": "https://claude.ai",
    "جيميني": "https://gemini.google.com",
    "gemini": "https://gemini.google.com",
    "غيتهاب": "https://www.github.com",
    "جيت هاب": "https://www.github.com",
    "جيت_هاب": "https://www.github.com",
    "github": "https://www.github.com",
    "جيت لاب": "https://gitlab.com",
    "gitlab": "https://gitlab.com",
    "ستاك اوفر فلو": "https://stackoverflow.com",
    "stackoverflow": "https://stackoverflow.com",
    "نوشن": "https://www.notion.so",
    "notion": "https://www.notion.so",
    "كانفا": "https://www.canva.com",
    "canva": "https://www.canva.com",
    "فيجما": "https://www.figma.com",
    "figma": "https://www.figma.com",

    # Search & Cloud & Mail
    "جوجل": "https://www.google.com",
    "غوغل": "https://www.google.com",
    "قووقل": "https://www.google.com",
    "google": "https://www.google.com",
    "بينج": "https://www.bing.com",
    "bing": "https://www.bing.com",
    "جيميل": "https://mail.google.com",
    "gmail": "https://mail.google.com",
    "درايف": "https://drive.google.com",
    "جوجل درايف": "https://drive.google.com",
    "ترجمة": "https://translate.google.com",
    "ترجمة جوجل": "https://translate.google.com",
    "مترجم جوجل": "https://translate.google.com",
    "خرائط جوجل": "https://maps.google.com",
    "خرائط": "https://maps.google.com",
    "جوجل ميت": "https://meet.google.com",
    "ويكيبيديا": "https://ar.wikipedia.org",
    "wikipedia": "https://ar.wikipedia.org",
    "ياهو": "https://www.yahoo.com",
    "اوتلوك": "https://outlook.live.com",

    # Social & Community
    "يوتيوب": "https://www.youtube.com",
    "youtube": "https://www.youtube.com",
    "تويتر": "https://x.com",
    "twitter": "https://x.com",
    "اكس": "https://x.com",
    "فيسبوك": "https://www.facebook.com",
    "فيس بوك": "https://www.facebook.com",
    "facebook": "https://www.facebook.com",
    "انستقرام": "https://www.instagram.com",
    "انستغرام": "https://www.instagram.com",
    "انستجرام": "https://www.instagram.com",
    "instagram": "https://www.instagram.com",
    "تيك توك": "https://www.tiktok.com",
    "تيكتوك": "https://www.tiktok.com",
    "tiktok": "https://www.tiktok.com",
    "لينكد ان": "https://www.linkedin.com",
    "لينكدان": "https://www.linkedin.com",
    "linkedin": "https://www.linkedin.com",
    "واتساب": "https://web.whatsapp.com",
    "واتس اب": "https://web.whatsapp.com",
    "whatsapp": "https://web.whatsapp.com",
    "تيليجرام": "https://web.telegram.org",
    "تليجرام": "https://web.telegram.org",
    "telegram": "https://web.telegram.org",
    "ريديت": "https://www.reddit.com",
    "reddit": "https://www.reddit.com",
    "ديسكورد": "https://discord.com",
    "discord": "https://discord.com",
    "تويتش": "https://www.twitch.tv",
    "twitch": "https://www.twitch.tv",
    "بينترست": "https://www.pinterest.com",
    "pinterest": "https://www.pinterest.com",
    "سناب شات": "https://web.snapchat.com",

    # Streaming & Entertainment
    "نتفلكس": "https://www.netflix.com",
    "نتفليكس": "https://www.netflix.com",
    "netflix": "https://www.netflix.com",
    "سبوتيفاي": "https://open.spotify.com",
    "spotify": "https://open.spotify.com",
    "ساوند كلاود": "https://soundcloud.com",
    "soundcloud": "https://soundcloud.com",
    "شاهد": "https://shahid.mbc.net",
    "انغامي": "https://www.anghami.com",
    "ستيم": "https://store.steampowered.com",

    # E-Commerce & Arab Portals
    "امازون": "https://www.amazon.com",
    "أمازون": "https://www.amazon.com",
    "amazon": "https://www.amazon.com",
    "علي اكسبريس": "https://www.aliexpress.com",
    "aliexpress": "https://www.aliexpress.com",
    "ايباي": "https://www.ebay.com",
    "ebay": "https://www.ebay.com",
    "نون": "https://www.noon.com",
    "noon": "https://www.noon.com",
    "حراج": "https://haraj.com.sa",
    "سلة": "https://salla.com",
    "زد": "https://zid.sa",
    "خمسات": "https://khamsat.com",
    "مستقل": "https://mostaql.com",
    "حاسوب": "https://academy.hsoub.com",
    "موضوع": "https://mawdoo3.com",
    "الجزيرة": "https://www.aljazeera.net",
    "العربية": "https://www.alarabiya.net",
}


def resolve_url_name(name: str) -> Optional[str]:
    """Resolves website name, brand or domain alias to an exact canonical URL."""
    k = name.strip().lower()
    for prefix in ["موقع ", "صفحة ", "the website ", "the site ", "website ", "site "]:
        if k.startswith(prefix):
            k = k[len(prefix):].strip()
    if k in ARABIC_URL_TRANSLATIONS:
        return ARABIC_URL_TRANSLATIONS[k]
    if k.startswith("ال") and k[2:] in ARABIC_URL_TRANSLATIONS:
        return ARABIC_URL_TRANSLATIONS[k[2:]]
    return None


def resolve_app_name(name: str) -> str:
    """Translates natural application names and removes polite prefixes."""
    k = name.strip().lower()
    for prefix in ["تطبيق ", "برنامج ", "متصفح ", "the app ", "the application ", "app ", "program "]:
        if k.startswith(prefix):
            k = k[len(prefix):].strip()
    if k in ARABIC_APP_TRANSLATIONS:
        return ARABIC_APP_TRANSLATIONS[k]
    if k.startswith("ال") and k[2:] in ARABIC_APP_TRANSLATIONS:
        return ARABIC_APP_TRANSLATIONS[k[2:]]
    return k


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

    VISION_ANALYSIS_PATTERNS = [
        (
            r"^(?:ممكن\s+)?(?:حلل\s+الشاشة|تحليل\s+الشاشة|حلل\s+ما\s+يظهر\s+على\s+الشاشة|حلل\s+ما\s+في\s+الشاشة|"
            r"افحص\s+الشاشة|اقرأ\s+الشاشة|شوف\s+الشاشة|ايش\s+على\s+الشاشة|شو\s+في\s+على\s+الشاشة|شو\s+في\s+بالشاشة|"
            r"شو\s+ظاهر\s+بالشاشة|شو\s+مكتوب\s+بالشاشة|ايش\s+مكتوب\s+بالشاشة|ايش\s+في\s+بالشاشة|"
            r"ماذا\s+ترى\s+على\s+الشاشة|ماذا\s+يوجد\s+على\s+الشاشة|ماذا\s+في\s+الشاشة|اشرح\s+الشاشة|"
            r"اشرح\s+ما\s+في\s+الشاشة|ترجم\s+الشاشة|ترجم\s+ما\s+يظهر\s+على\s+الشاشة|فحص\s+الشاشة|"
            r"تحليل\s+الشاشة\s+الذكي|اسأل\s+الشاشة|سؤال\s+عن\s+الشاشة)"
            r"(?:\s+(?:و\s+|عن\s+)?(?P<query>.+))?$"
        ),
        (
            r"^(?:please\s+)?(?:ask\s+my\s+screen|ask\s+screen|analyze\s+screen|analyze\s+my\s+screen|"
            r"what\s+is\s+on\s+my\s+screen|what\'s\s+on\s+my\s+screen|what\s+is\s+on\s+screen|"
            r"read\s+screen|explain\s+screen|check\s+screen|look\s+at\s+my\s+screen|screen\s+vision|"
            r"vision\s+ai|analyze\s+what\s+is\s+on\s+screen)"
            r"(?:\s+(?:and\s+)?(?P<query>.+))?$"
        ),
    ]

    DOCUMENT_RAG_PATTERNS = [
        (
            r"^(?:ممكن\s+)?(?:لخص\s+المستند|لخص\s+الملف|ابحث\s+في\s+المستند|ابحث\s+في\s+الملف|"
            r"ماذا\s+يقول\s+الملف|ماذا\s+يقول\s+المستند|اسأل\s+المستند|اسأل\s+الملف|"
            r"في\s+الملف(?:\s+المرفق)?|في\s+المستند(?:\s+المرفق)?|ما\s+محتوى\s+الملف|"
            r"ما\s+محتوى\s+المستند|اشرح\s+الملف|اشرح\s+المستند|ترجم\s+المستند|ترجم\s+الملف|"
            r"اقرأ\s+المستند|اقرأ\s+الملف)"
            r"(?:\s+(?:عن\s+|بخصوص\s+|و\s+)?(?P<query>.+))?$"
        ),
        (
            r"^(?:please\s+)?(?:summarize\s+document|summarize\s+the\s+document|summarize\s+file|"
            r"summarize\s+the\s+file|query\s+document|query\s+file|search\s+in\s+document|"
            r"search\s+document|search\s+file|ask\s+document|ask\s+the\s+document|"
            r"what\s+does\s+the\s+file\s+say|what\s+does\s+the\s+document\s+say|"
            r"explain\s+document|explain\s+the\s+file|read\s+document|read\s+file)"
            r"(?:\s+(?:about\s+|for\s+|and\s+)?(?P<query>.+))?$"
        ),
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
        # 0.1 Arabic Compound Browser-First (e.g. "افتح المتصفح و افتح كود التطور")
        m_ar_compound = re.match(
            r"^(?:ممكن\s+)?(?:افتح|شغل)?\s*(?:متصفح\s+)?"
            r"(?P<browser>كروم|جوجل\s+كروم|كومت|ايدج|إيدج|بريف|فايرفوكس|المتصفح|متصفح)\s+"
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
            r"(?P<browser>كروم|جوجل\s+كروم|كومت|ايدج|إيدج|بريف|فايرفوكس|المتصفح|متصفح)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            norm_raw,
            re.IGNORECASE,
        )
        if m_ar_target_br:
            tgt = m_ar_target_br.group("target").strip()
            br = m_ar_target_br.group("browser").strip()
            resolved_url = resolve_url_name(tgt) or ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            resolved_browser = resolve_app_name(br) or ARABIC_APP_TRANSLATIONS.get(br, br)
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
            resolved_url = resolve_url_name(tgt) or ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            return {
                "intent": UserIntent.OPEN_URL,
                "name": "open_url",
                "arguments": {"url": resolved_url, "browser": ""},
            }

        # 0.4 Direct Known Web Domains or URLs
        m_ar_url = re.match(
            r"^(?:ممكن\s+)?(?:افتح|شغل|روّح|اذهب|تصفح)?(?:\s+لي)?\s*(?:موقع|صفحة)?\s*"
            r"(?P<target>https?://\S+|.+\.(?:net|com|org|io|ai|co|dev|app|me)|يوتيوب|جوجل|غوغل|غيتهاب|"
            r"جيت\s*هاب|تويتر|فيسبوك|شات\s*جي\s*بي\s*تي|جيميل|واتساب|reddit|github|youtube|google|chatgpt|twitter)"
            r"(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            norm_raw,
            re.IGNORECASE,
        )
        if m_ar_url:
            tgt = m_ar_url.group("target").strip()
            resolved_url = resolve_url_name(tgt) or ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
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
            resolved_url = resolve_url_name(tgt) or ARABIC_URL_TRANSLATIONS.get(tgt, tgt)
            resolved_browser = resolve_app_name(br) or ARABIC_APP_TRANSLATIONS.get(br, br)
            return {
                "intent": UserIntent.OPEN_URL,
                "name": "open_url",
                "arguments": {"url": resolved_url, "browser": resolved_browser},
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

        # 2.5 Screen Vision Analysis (Ask My Screen / Bilingual)
        is_screen_query = False
        screen_query_arg = raw.strip()

        for pat in cls.VISION_ANALYSIS_PATTERNS:
            m = re.match(pat, low) or re.match(pat, raw)
            if m:
                is_screen_query = True
                query_arg = (m.groupdict().get("query") or "").strip()
                if query_arg and len(query_arg) > 3:
                    screen_query_arg = query_arg
                break

        if not is_screen_query:
            # Broad natural query detection for arbitrary questions about the screen
            # Handles: "شو في بالشاشة", "اقرأ المكتوب بالشاشة", "ما هذا الخطأ بالشاشة", "اشرح الكود المعروض", etc.
            screen_keys_ar = ["الشاشة", "بالشاشة", "على الشاشة", "شاشتي"]
            screen_keys_en = ["on screen", "on my screen", "this screen", "the screen", "in screen"]
            has_screen_ref = any(k in raw for k in screen_keys_ar) or any(k in low for k in screen_keys_en)

            actions_ar = [
                "شو", "ايش", "ما", "ماذا", "اشرح", "حلل", "اقرأ", "اقرا", "ترجم",
                "لخص", "شوف", "افحص", "هل", "كيف", "وين", "مين", "فحص", "تحليل", "خطأ", "كود", "صورة"
            ]
            actions_en = [
                "what", "explain", "analyze", "read", "translate", "summarize",
                "check", "see", "look", "how", "error", "code"
            ]
            has_intent_action = any(k in raw for k in actions_ar) or any(k in low for k in actions_en)
            if has_screen_ref and has_intent_action:
                is_screen_query = True

        if is_screen_query:
            return {
                "intent": UserIntent.VISION_ANALYSIS,
                "name": "analyze_screen",
                "arguments": {
                    "query": screen_query_arg,
                    "target": "full",
                },
            }

        # 2.7 Document RAG Routing (Bilingual)
        for pat in cls.DOCUMENT_RAG_PATTERNS:
            m = re.match(pat, low) or re.match(pat, raw)
            if m:
                query_arg = (m.groupdict().get("query") or "").strip()
                return {
                    "intent": UserIntent.DOCUMENT_RAG,
                    "name": "query_document",
                    "arguments": {
                        "query": query_arg if query_arg else raw,
                    },
                }

        # 2.8 Reminders, Timers & System Alerts (Bilingual)
        # 2.8.1 Cancel Timer / Alarm
        if re.match(
            r"^(?:ممكن\s+)?(?:الغ(?:اء|ي)|وقف|احذف|بطل|اطفئ|اطفي|سكّت|سكت)\s*"
            r"(?:المؤقت|المنبه|المؤقتات|المنبهات|التنبيه)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ) or re.match(
            r"^(?:please\s+)?(?:cancel|stop|delete|dismiss)\s*(?:the\s+)?(?:timer|alarm|reminder)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.TIMER,
                "name": "cancel_reminder",
                "arguments": {},
            }

        # 2.8.2 List Timers / Alarms
        if re.match(
            r"^(?:ممكن\s+)?(?:اعرض|وريني|شو\s+في|قائمة|استعرض|كم)\s*"
            r"(?:المؤقتات|المنبهات|التنبيهات|المؤقت|المنبه)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ) or re.match(
            r"^(?:please\s+)?(?:list|show|view|get)\s*(?:the\s+)?(?:reminders|timers|alarms)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.REMINDER,
                "name": "list_reminders",
                "arguments": {"status": "active"},
            }

        # 2.8.3 Set Relative Timer (e.g. "مؤقت 10 دقائق", "ذكرني بعد نص ساعة", "timer 5 mins")
        if any(w in raw for w in ["مؤقت", "timer"]) or re.search(r"\b(?:ذكرني|نبهني)\s+بعد\b", raw):
            from aegis_core.automation.reminder_manager import reminder_manager

            sec, title = reminder_manager.parse_relative_duration(raw)
            if sec > 0:
                return {
                    "intent": UserIntent.TIMER,
                    "name": "set_timer",
                    "arguments": {"duration_seconds": sec, "title": title},
                }

        # 2.8.4 Set Absolute Reminder (e.g. "منبه الساعة 7", "ذكرني الساعة 4:30", "remind me at 5 pm")
        if any(w in raw for w in ["منبه", "تنبيه", "alarm"]) or re.search(r"\b(?:الساعة|ساعة|at\s+\d)\b", raw):
            from aegis_core.automation.reminder_manager import reminder_manager

            dt, title = reminder_manager.parse_absolute_time(raw)
            if dt:
                return {
                    "intent": UserIntent.REMINDER,
                    "name": "set_reminder",
                    "arguments": {"target_time": raw, "title": title},
                }
            sec, title = reminder_manager.parse_relative_duration(raw)
            if sec > 0:
                return {
                    "intent": UserIntent.TIMER,
                    "name": "set_timer",
                    "arguments": {"duration_seconds": sec, "title": title},
                }

        # 2.9 Media Playback Controls (Bilingual)
        # 2.9.1 Next Track
        if re.match(
            r"^(?:ممكن\s+)?(?:المقطع\s+التالي|الأغنية\s+التالية|الاغنية\s+التالية|"
            r"التالي|اللي\s+بعده|قدم\s+المقطع|تخطي)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ) or re.match(
            r"^(?:please\s+)?(?:next\s+track|next\s+song|next|skip\s+song|skip\s+track|skip)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.MEDIA,
                "name": "control_media",
                "arguments": {"action": "next"},
            }

        # 2.9.2 Previous Track
        if re.match(
            r"^(?:ممكن\s+)?(?:المقطع\s+السابق|الأغنية\s+السابقة|الاغنية\s+السابقة|"
            r"السابق|اللي\s+قبله|رجع\s+المقطع|السابقة)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ) or re.match(
            r"^(?:please\s+)?(?:previous\s+track|previous\s+song|prev\s+track|prev\s+song|previous|prev|back)"
            r"(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.MEDIA,
                "name": "control_media",
                "arguments": {"action": "previous"},
            }

        # 2.9.3 Stop Media
        if re.match(
            r"^(?:ممكن\s+)?(?:إيقاف\s+الموسيقى|ايقاف\s+الموسيقى|إيقاف\s+المقطع|ايقاف\s+المقطع|"
            r"إيقاف\s+التشغيل|ايقاف\s+التشغيل|اطفئ\s+الموسيقى)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ) or re.match(
            r"^(?:please\s+)?(?:stop\s+music|stop\s+media|stop\s+playback)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.MEDIA,
                "name": "control_media",
                "arguments": {"action": "stop"},
            }

        # 2.9.4 Play / Pause Toggle
        if re.match(
            r"^(?:ممكن\s+)?(?:شغل\s+(?:الموسيقى|المقطع|الفيديو|الاغنية|الأغنية)|"
            r"وقف\s+(?:الموسيقى|المقطع|الفيديو|الاغنية|الأغنية)|"
            r"شغل\s+أو\s+وقف\s+الموسيقى|شغل\s+او\s+وقف\s+الموسيقى|"
            r"وقف\s+مؤقتاً|وقف\s+مؤقت|استئناف|كمل\s+المقطع|"
            r"شغل|وقف|تشغيل|ايقاف\s+مؤقت|إيقاف\s+مؤقت)(?:\s+لو\s+سمحت|\s+من\s+فضلك)?$",
            raw,
        ) or re.match(
            r"^(?:please\s+)?(?:play\s+music|pause\s+music|play\s+media|pause\s+media|"
            r"play|pause|resume|unpause|toggle\s+playback)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.MEDIA,
                "name": "control_media",
                "arguments": {"action": "play_pause"},
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
                # 1. Check if user asked to open a known website or web app (e.g. "افتح امازون", "افتح كانفا")
                known_url = resolve_url_name(app)
                if known_url:
                    return {
                        "intent": UserIntent.OPEN_URL,
                        "name": "open_url",
                        "arguments": {"url": known_url, "browser": ""},
                    }

                # 2. Translate Arabic app names and strip polite prefixes
                translated_app = resolve_app_name(app)

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
