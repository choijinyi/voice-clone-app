"""VoiceForge — AI Voice Cloning & Generation Studio.

Architecture (from reference diagram):
  1. Voice Cloning:      Reference Audio → Global Tokenizer → LLM → BiCodec Decoder → Audio
  2. Controlled Generation: Attribute Prompt → Attribute Tokenizer → LLM → BiCodec Decoder → Audio

Run:  python app.py
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

import gradio as gr

from engines import available_engines, get_engine
from engines.edge_engine import LANG_MAP

# ── Paths ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
.header { text-align: center; margin-bottom: 8px; }
.header h1 { font-size: 2rem; margin-bottom: 0; }
.header p  { color: #666; font-size: 0.95rem; }
.status-ok  { color: #16a34a; font-weight: 600; }
.status-off { color: #dc2626; font-weight: 600; }
.tip { background: #f0f9ff; border-left: 4px solid #3b82f6;
       padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }
footer { display: none !important; }
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def _out_path(prefix: str = "voice") -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUT_DIR / f"{prefix}_{ts}_{uuid.uuid4().hex[:6]}.mp3"


def _engine_status_md() -> str:
    engines = available_engines()
    lines = ["| Engine | Status | Voice Cloning |", "| --- | --- | --- |"]
    for name, eng in engines.items():
        clone = "Yes" if eng.supports_cloning else "No"
        lines.append(f"| {name} | Active | {clone} |")

    has_clone = any(e.supports_cloning for e in engines.values())
    if not has_clone:
        lines.append("")
        lines.append(
            "> Voice Cloning requires **CosyVoice2**. "
            "See the **Setup** tab for installation instructions."
        )
    return "\n".join(lines)


async def _get_voice_choices(language: str) -> list[tuple[str, str]]:
    engine = get_engine("edge-tts")
    voices = await engine.list_voices(language)
    return [(f"{v.name}  ({v.gender})", v.id) for v in voices]


# ── Core functions ────────────────────────────────────────────────────────────

async def do_generate(text: str, voice_id: str, language: str, speed: float):
    """Controlled generation — edge-tts."""
    if not text.strip():
        gr.Warning("Text is empty.")
        return None

    engine = get_engine("edge-tts")
    out = _out_path("gen")
    try:
        await engine.generate(text, voice_id, out, speed)
        return str(out)
    except Exception as e:
        gr.Warning(f"Generation failed: {e}")
        return None


async def do_clone(text: str, ref_audio: str | None, ref_text: str, speed: float):
    """Voice cloning — CosyVoice2 or fallback."""
    if not text.strip():
        gr.Warning("Text is empty.")
        return None, ""
    if not ref_audio:
        gr.Warning("Reference audio is required for voice cloning.")
        return None, ""

    engines = available_engines()
    clone_engine = None
    for eng in engines.values():
        if eng.supports_cloning:
            clone_engine = eng
            break

    if clone_engine is None:
        msg = (
            "**Voice Cloning engine is not installed.**\n\n"
            "Currently using Edge-TTS (preset voices only).\n"
            "Install CosyVoice2 for real voice cloning — see Settings tab."
        )
        # Fallback: generate with edge-tts default voice
        engine = get_engine("edge-tts")
        out = _out_path("clone_fallback")
        try:
            await engine.generate(text, "ko-KR-SunHiNeural", out, speed)
            return str(out), msg
        except Exception as e:
            gr.Warning(str(e))
            return None, msg

    out = _out_path("clone")
    ref_path = Path(ref_audio)
    try:
        await clone_engine.clone(text, ref_path, out, speed, ref_text or None)
        return str(out), "Voice cloning complete."
    except Exception as e:
        gr.Warning(f"Cloning failed: {e}")
        return None, f"Error: {e}"


def _get_voice_choices_sync(language: str) -> list[tuple[str, str]]:
    """Synchronous version for initial load."""
    from engines.edge_engine import _VOICES, LANG_MAP
    lang_code = LANG_MAP.get(language, language)
    voices = [v for v in _VOICES if v.language == lang_code] if lang_code else _VOICES
    return [(f"{v.name}  ({v.gender})", v.id) for v in voices]


async def update_voices(language: str):
    """Update voice dropdown when language changes."""
    choices = await _get_voice_choices(language)
    default = choices[0][1] if choices else None
    return gr.update(choices=choices, value=default)


async def preview_voice(voice_id: str, language: str):
    """Generate a short preview of the selected voice."""
    previews = {
        "ko": "안녕하세요, VoiceForge에 오신 것을 환영합니다.",
        "en": "Hello, welcome to VoiceForge.",
        "ja": "こんにちは、VoiceForgeへようこそ。",
        "zh": "你好，欢迎来到VoiceForge。",
        "es": "Hola, bienvenido a VoiceForge.",
        "fr": "Bonjour, bienvenue sur VoiceForge.",
        "de": "Hallo, willkommen bei VoiceForge.",
    }
    lang_code = LANG_MAP.get(language, "en")
    text = previews.get(lang_code, previews["en"])

    engine = get_engine("edge-tts")
    out = _out_path("preview")
    try:
        await engine.generate(text, voice_id, out)
        return str(out)
    except Exception:
        return None


# ── UI ────────────────────────────────────────────────────────────────────────

def build_app() -> gr.Blocks:
    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Noto Sans KR"), "sans-serif"],
    )

    with gr.Blocks(theme=theme, css=CSS, title="VoiceForge") as app:

        # ── Header ────────────────────────────────────────────────────────
        gr.HTML("""
        <div class="header">
            <h1>VoiceForge</h1>
            <p>AI Voice Cloning & Generation Studio</p>
        </div>
        """)

        with gr.Tabs():

            # ━━ Tab 1: Voice Cloning ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            with gr.TabItem("Voice Cloning"):
                gr.Markdown("""
                <div class="tip">
                Reference Audio를 업로드하고, 해당 목소리로 새로운 텍스트를 생성합니다.<br>
                <strong>CosyVoice2</strong> 설치 시 실제 음성 복제가 동작합니다.
                미설치 시 기본 음성으로 대체 생성됩니다.
                </div>
                """)

                with gr.Row(equal_height=True):
                    with gr.Column(scale=1):
                        clone_ref = gr.Audio(
                            label="Reference Audio (3~10s recommended)",
                            type="filepath",
                            sources=["upload", "microphone"],
                        )
                        clone_ref_text = gr.Textbox(
                            label="Reference Text (optional)",
                            placeholder="What the reference audio says — improves accuracy",
                            lines=2,
                        )

                    with gr.Column(scale=1):
                        clone_text = gr.Textbox(
                            label="Text to Generate",
                            placeholder="Enter text to speak in the cloned voice...",
                            lines=5,
                        )
                        clone_speed = gr.Slider(
                            0.5, 2.0, value=1.0, step=0.1, label="Speed"
                        )

                clone_btn = gr.Button("Clone & Generate", variant="primary", size="lg")
                clone_output = gr.Audio(label="Generated Audio", type="filepath")
                clone_status = gr.Markdown("")

                clone_btn.click(
                    fn=do_clone,
                    inputs=[clone_text, clone_ref, clone_ref_text, clone_speed],
                    outputs=[clone_output, clone_status],
                )

            # ━━ Tab 2: Controlled Generation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            with gr.TabItem("Voice Generation"):
                gr.Markdown("""
                <div class="tip">
                Language, Gender, Voice Style 을 선택하여 원하는 음성으로 텍스트를 생성합니다.
                </div>
                """)

                with gr.Row(equal_height=True):
                    with gr.Column(scale=1):
                        gen_lang = gr.Dropdown(
                            choices=list(LANG_MAP.keys()),
                            value="한국어",
                            label="Language",
                        )
                        _init_voices = _get_voice_choices_sync("한국어")
                        gen_voice = gr.Dropdown(
                            choices=_init_voices,
                            value=_init_voices[0][1] if _init_voices else None,
                            label="Voice",
                            interactive=True,
                        )
                        preview_btn = gr.Button("Preview Voice", size="sm")
                        preview_audio = gr.Audio(label="Preview", type="filepath", visible=True)

                        gen_speed = gr.Slider(
                            0.5, 2.0, value=1.0, step=0.1, label="Speed"
                        )

                    with gr.Column(scale=1):
                        gen_text = gr.Textbox(
                            label="Text to Generate",
                            placeholder="Enter text...",
                            lines=8,
                        )

                gen_btn = gr.Button("Generate", variant="primary", size="lg")
                gen_output = gr.Audio(label="Generated Audio", type="filepath")

                # Dynamic voice list
                gen_lang.change(fn=update_voices, inputs=[gen_lang], outputs=[gen_voice])
                # Preview
                preview_btn.click(
                    fn=preview_voice, inputs=[gen_voice, gen_lang], outputs=[preview_audio]
                )
                # Generate
                gen_btn.click(
                    fn=do_generate,
                    inputs=[gen_text, gen_voice, gen_lang, gen_speed],
                    outputs=[gen_output],
                )

            # ━━ Tab 3: Settings ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            with gr.TabItem("Settings"):
                gr.Markdown("### Engine Status")
                gr.Markdown(_engine_status_md())

                gr.Markdown("---")
                gr.Markdown("""
### CosyVoice2 Installation Guide

This app's voice cloning feature uses **CosyVoice2**, which matches the
BiCodec architecture from the reference diagram.

**Step 1 — Clone the repository**
```bash
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
pip install -r requirements.txt
```

**Step 2 — Download model weights**
```bash
# From ModelScope (recommended for Asia):
modelscope download --model iic/CosyVoice2-0.5B --local_dir pretrained_models/CosyVoice2-0.5B

# Or from HuggingFace:
huggingface-cli download FunAudioLLM/CosyVoice2-0.5B --local-dir pretrained_models/CosyVoice2-0.5B
```

**Step 3 — Set environment variable & run**
```bash
export COSYVOICE_MODEL_DIR=path/to/CosyVoice2-0.5B
python app.py
```

> After installation, the **Voice Cloning** tab will use real zero-shot
> voice cloning instead of the fallback TTS.
                """)

                gr.Markdown("---")
                gr.Markdown("""
### Architecture Reference

```
Voice Cloning Pipeline:
  Reference Audio → Global Tokenizer ─┐
                                       ├→ LLM → BiCodec Decoder → Audio
  Text → BPE Tokenizer ───────────────┘

Controlled Generation Pipeline:
  Attribute Prompt → Attribute Tokenizer ─┐
                                          ├→ LLM → BiCodec Decoder → Audio
  Text → BPE Tokenizer ──────────────────┘
```
                """)

    return app


# ── App instance (required by Vercel / hosting platforms) ─────────────────────

demo = build_app()
app = demo.app  # ASGI app for Vercel

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
    )
