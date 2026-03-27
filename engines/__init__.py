"""Engine registry — auto-detects available backends."""

from .base import TTSEngine, Voice
from .edge_engine import EdgeTTSEngine

_engines: dict[str, TTSEngine] = {}


def _register_defaults():
    global _engines
    # Edge TTS — always available (requires only edge-tts pip package)
    _engines["edge-tts"] = EdgeTTSEngine()

    # CosyVoice2 — available only when installed
    try:
        from .cosyvoice_engine import CosyVoiceEngine
        _engines["cosyvoice"] = CosyVoiceEngine()
    except ImportError:
        pass


def get_engine(name: str | None = None) -> TTSEngine:
    """Get engine by name. Returns best available if name is None."""
    if not _engines:
        _register_defaults()
    if name:
        return _engines[name]
    # Prefer cosyvoice > edge-tts
    for key in ("cosyvoice", "edge-tts"):
        if key in _engines:
            return _engines[key]
    raise RuntimeError("No TTS engine available")


def available_engines() -> dict[str, TTSEngine]:
    if not _engines:
        _register_defaults()
    return dict(_engines)


__all__ = ["TTSEngine", "Voice", "get_engine", "available_engines"]
