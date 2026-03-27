"""Edge TTS engine — free, high-quality, no GPU required."""

import asyncio
from pathlib import Path

import edge_tts

from .base import TTSEngine, Voice

# ── Voice catalogue (curated subset) ──────────────────────────────────────────
# Full list: `edge-tts --list-voices`
_VOICES = [
    # Korean
    Voice("ko-KR-SunHiNeural",   "선히 (SunHi)",    "ko", "female", "default"),
    Voice("ko-KR-InJoonNeural",  "인준 (InJoon)",   "ko", "male",   "default"),
    Voice("ko-KR-HyunsuNeural",  "현수 (Hyunsu)",   "ko", "male",   "default"),
    # English — US
    Voice("en-US-JennyNeural",   "Jenny",           "en", "female", "default"),
    Voice("en-US-AriaNeural",    "Aria",            "en", "female", "chat"),
    Voice("en-US-GuyNeural",     "Guy",             "en", "male",   "default"),
    Voice("en-US-DavisNeural",   "Davis",           "en", "male",   "default"),
    # English — GB
    Voice("en-GB-SoniaNeural",   "Sonia (British)", "en", "female", "default"),
    Voice("en-GB-RyanNeural",    "Ryan (British)",  "en", "male",   "default"),
    # Japanese
    Voice("ja-JP-NanamiNeural",  "Nanami",          "ja", "female", "default"),
    Voice("ja-JP-KeitaNeural",   "Keita",           "ja", "male",   "default"),
    # Chinese
    Voice("zh-CN-XiaoxiaoNeural","Xiaoxiao",        "zh", "female", "default"),
    Voice("zh-CN-YunxiNeural",   "Yunxi",           "zh", "male",   "default"),
    # Spanish
    Voice("es-ES-ElviraNeural",  "Elvira",          "es", "female", "default"),
    Voice("es-ES-AlvaroNeural",  "Alvaro",          "es", "male",   "default"),
    # French
    Voice("fr-FR-DeniseNeural",  "Denise",          "fr", "female", "default"),
    Voice("fr-FR-HenriNeural",   "Henri",           "fr", "male",   "default"),
    # German
    Voice("de-DE-KatjaNeural",   "Katja",           "de", "female", "default"),
    Voice("de-DE-ConradNeural",  "Conrad",          "de", "male",   "default"),
]

# Language display names → filter keys
LANG_MAP = {
    "한국어": "ko",
    "English": "en",
    "日本語": "ja",
    "中文":   "zh",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
}


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS — free, high-quality, works everywhere."""

    name = "edge-tts"
    supports_cloning = False

    async def generate(self, text: str, voice_id: str, output_path: Path, speed: float = 1.0) -> Path:
        rate = _speed_to_rate(speed)
        comm = edge_tts.Communicate(text, voice_id, rate=rate)
        await comm.save(str(output_path))
        return output_path

    async def list_voices(self, language: str | None = None) -> list[Voice]:
        if language and language in LANG_MAP:
            lang_code = LANG_MAP[language]
        else:
            lang_code = language
        if lang_code:
            return [v for v in _VOICES if v.language == lang_code]
        return list(_VOICES)


def _speed_to_rate(speed: float) -> str:
    """Convert numeric speed (0.5–2.0) to Edge TTS rate string."""
    pct = int((speed - 1.0) * 100)
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"
