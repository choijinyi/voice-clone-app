# VoiceForge — AI Voice Cloning & Generation Studio

Reference Audio를 업로드하여 목소리를 복제하거나, 다양한 프리셋 음성으로 텍스트를 생성하는 웹 앱입니다.

## Quick Start

```bash
cd voice-clone-app
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://localhost:7860` 접속.

## Features

| Tab | 기능 | 필요 엔진 |
|-----|------|-----------|
| Voice Cloning | 참조 음성 → 목소리 복제 | CosyVoice2 (미설치 시 기본 음성 대체) |
| Voice Generation | 프리셋 음성 선택 → TTS | Edge TTS (기본 포함) |

## Architecture

```
Voice Cloning:
  Reference Audio → Global Tokenizer ─┐
                                       ├→ LLM → BiCodec Decoder → Audio
  Text → BPE Tokenizer ───────────────┘

Controlled Generation:
  Attribute Prompt → Attribute Tokenizer ─┐
                                          ├→ LLM → BiCodec Decoder → Audio
  Text → BPE Tokenizer ──────────────────┘
```

## CosyVoice2 Setup (Optional — enables real voice cloning)

```bash
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice && pip install -r requirements.txt

# Download model
modelscope download --model iic/CosyVoice2-0.5B --local_dir pretrained_models/CosyVoice2-0.5B

# Set path & run
export COSYVOICE_MODEL_DIR=path/to/CosyVoice2-0.5B
python app.py
```
