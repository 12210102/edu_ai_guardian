# EduAI Guardian v8 — Expressive AI Teacher

## What's New in v8
- **Animated SVG face** — mouth moves while speaking, eyebrows change per emotion
- **Sarvam TTS** — teacher speaks every reply (Meera, Indian English voice)
- **Two-way voice** — speak questions via browser mic, teacher speaks answers
- **Text + Voice simultaneously** — both modes work at the same time
- **8 interactive suggestion cards** across 6 categories
- **Gemini AI primary** + Groq fallback
- **Dashboard & Risk Detector** — unchanged from v7

## Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

## API Keys (in sidebar)
| Key | Source | Used for |
|-----|--------|---------|
| Gemini | aistudio.google.com | Primary AI teacher |
| Groq | console.groq.com | Fallback AI + fast responses |
| Sarvam | dashboard.sarvam.ai | Voice TTS (Meera voice) |
| YouTube | console.cloud.google.com | Live video suggestions |

## Voice Usage
1. Add Sarvam key → teacher speaks in Indian English (Meera voice)
2. Click 🎤 mic button → speak your question (Chrome recommended)
3. Tap "Send to Prof. Aura" → reply is spoken aloud automatically
4. Toggle "Auto-speak" off in Voice Settings to stop auto-TTS
