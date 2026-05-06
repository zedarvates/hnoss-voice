# 🎙️ Hnoss Voice

Assistant vocal always-on 100% local pour Hermes Agent.

## Architecture

```
Micro (GLYPH) → Wake Word → STT (Whisper) → LLM (Qwen MTP) → TTS (Piper FR) → Haut-parleurs
                                         ↓
                              Voice ID + Face ID (Hailo-8)
```

## Sécurité

- **Voice ID** : Reconnaissance vocale (Speaker embedding)
- **Face ID** : Reconnaissance faciale (Hailo-8 YOLO)
- **3 modes d'accès** : Complet (Sylvain) / Restreint (Invité) / Public (Inconnu)

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Wake Words

- "OK Hnoss"
- "OK Hermes"

## Services utilisés

| Service | Endpoint |
|---------|----------|
| STT (Whisper) | EUREKAI:8080 |
| LLM (Qwen MTP) | EUREKAI:8080 |
| TTS (Piper FR) | EUREKAI:8080 |
| Vision (Hailo-8) | EUREKAI:8767 |

## Créateur

Sylvain G. — Projet open-source MIT.
