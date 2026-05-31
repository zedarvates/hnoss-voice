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


---

## 🤝 Support

If you find this project useful, consider supporting its development:

| Coin | Address |
|------|---------|
| ₿ **Bitcoin** | `bc1qcqhgfyay56dqexrrnvzguqdczxct0vykqz38dz` |
| Ξ **Ethereum** | `0x1CbE662f1d6C58bc2adEE57F0e17216882BAc36c` |

Your support helps keep the servers running ☕
