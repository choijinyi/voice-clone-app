"""CosyVoice2 engine — full voice cloning with BiCodec architecture.

This engine matches the architecture in the reference diagram:
  - Voice Cloning:  Reference Audio → Global Tokenizer → LLM → BiCodec Decoder
  - Controlled Gen: Attribute Prompt → Attribute Tokenizer → LLM → BiCodec Decoder

Requires separate installation:
  1. git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
  2. cd CosyVoice && pip install -r requirements.txt
  3. Download model: CosyVoice2-0.5B from ModelScope/HuggingFace

Set env var COSYVOICE_MODEL_DIR to the model path.
"""

import os
import uuid
from pathlib import Path

from .base import TTSEngine, Voice

# Will raise ImportError if CosyVoice is not installed — caught by __init__.py
from cosyvoice.cli.cosyvoice import CosyVoice2  # type: ignore


_MODEL_DIR = os.environ.get("COSYVOICE_MODEL_DIR", "pretrained_models/CosyVoice2-0.5B")


class CosyVoiceEngine(TTSEngine):
    """CosyVoice2 — LLM-based voice cloning & controlled generation."""

    name = "cosyvoice"
    supports_cloning = True

    def __init__(self):
        self.model = CosyVoice2(_MODEL_DIR, load_jit=False, load_trt=False)

    async def generate(self, text: str, voice_id: str, output_path: Path, speed: float = 1.0) -> Path:
        """Generate with a built-in speaker (instruct mode)."""
        import torchaudio  # type: ignore

        for result in self.model.inference_instruct2(
            text,
            voice_id,
            stream=False,
            speed=speed,
        ):
            torchaudio.save(str(output_path), result["tts_speech"], 22050)
        return output_path

    async def clone(self, text: str, reference_audio: Path, output_path: Path,
                    speed: float = 1.0, ref_text: str | None = None) -> Path:
        """Zero-shot voice cloning from reference audio."""
        import torchaudio  # type: ignore

        prompt_speech_16k = self._load_audio(reference_audio)

        if ref_text:
            for result in self.model.inference_zero_shot(
                text, ref_text, prompt_speech_16k,
                stream=False, speed=speed,
            ):
                torchaudio.save(str(output_path), result["tts_speech"], 22050)
        else:
            for result in self.model.inference_cross_lingual(
                text, prompt_speech_16k,
                stream=False, speed=speed,
            ):
                torchaudio.save(str(output_path), result["tts_speech"], 22050)
        return output_path

    async def list_voices(self, language: str | None = None) -> list[Voice]:
        speakers = self.model.list_available_spks()
        return [Voice(id=s, name=s, language="multi", gender="unknown") for s in speakers]

    @staticmethod
    def _load_audio(path: Path):
        import torchaudio  # type: ignore

        speech, sr = torchaudio.load(str(path))
        if sr != 16000:
            speech = torchaudio.transforms.Resample(sr, 16000)(speech)
        return speech
