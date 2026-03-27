"""Abstract base class for TTS engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Voice:
    """Voice metadata."""
    id: str
    name: str
    language: str
    gender: str
    style: str = "default"


class TTSEngine(ABC):
    """Base class for all TTS engines."""

    name: str = "base"
    supports_cloning: bool = False

    @abstractmethod
    async def generate(self, text: str, voice_id: str, output_path: Path, speed: float = 1.0) -> Path:
        """Generate speech from text with a preset voice."""
        ...

    async def clone(self, text: str, reference_audio: Path, output_path: Path,
                    speed: float = 1.0, ref_text: str | None = None) -> Path:
        """Clone a voice from reference audio and generate speech."""
        raise NotImplementedError(f"{self.name} does not support voice cloning")

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[Voice]:
        """Return available voices, optionally filtered by language."""
        ...
