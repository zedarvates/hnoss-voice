# Hnoss Voice 🎙️

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)]()

Assistant vocal always-on 100% local avec Voice ID + Face ID. Wake word, STT via Whisper, LLM via Qwen MTP, TTS via Piper FR.

## Architecture

```
Utilisateur → Micro
  ├─ Wake Word Detection → Écoute active
  ├─ Voice ID → Identification du locuteur
  └─ Face ID → Vérification visuelle (optionnel)
       ↓
  Whisper STT → Transcription locale
       ↓
  Qwen MTP LLM → Compréhension + réponse
       ↓
  Piper TTS → Synthèse vocale FR
       ↓
  Haut-parleur → Réponse audio
```

## Composants

- **Wake Word** — Détection locale, zero cloud
- **Whisper STT** — Transcription en temps réel
- **Qwen MTP** — LLM local multi-tâches
- **Piper TTS** — Synthèse vocale française
- **Voice ID** — Reconnaissance du locuteur
- **Face ID** — Vérification faciale (caméra)

## Intégration Hermes

Hnoss Voice s'intègre avec Hermes via :
- **MCP bridge** pour les outils Hermes
- **kitten-tts** pour la synthèse vocale
- **hermes-rust-backend** pour l'inférence

## Projets liés

- [kitten-tts](https://github.com/zedarvates/kitten-tts) — TTS local FR
- [hermes-rust-backend](https://github.com/zedarvates/hermes-rust-backend) — Backend Rust
- [hermes-brain](https://github.com/zedarvates/hermes-brain) — Architecture cognitive

## Licence MIT
