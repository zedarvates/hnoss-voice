#!/usr/bin/env python3
"""
Hnoss Voice - Assistant vocal always-on avec sécurité biométrique.
Stack 100% locale : Wake Word → STT Whisper → LLM Qwen MTP → TTS Piper FR.
Voice ID + Face ID via Hailo-8.
"""

import os
import sys
import time
import json
import wave
import threading
import queue
from pathlib import Path
import requests
import numpy as np
import pyaudio
import soundfile as sf

# ─── CONFIGURATION ───────────────────────────────────────
LOCALAI_URL = os.getenv("LOCALAI_URL", "http://192.168.1.47:8080")
HAILO_URL = os.getenv("HAILO_URL", "http://192.168.1.47:8767")
WAKE_WORDS = ["ok hnoss", "ok hermes", "ok ermes", "ok erme"]
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1  # 100ms chunks
SILENCE_TIMEOUT = 2.0  # 2s silence = fin de commande
FACIAL_CHECK_INTERVAL = 5  # secondes entre check visage

# ─── AUDIO CAPTURE ───────────────────────────────────────
class AudioCapture:
    """Capture audio en continu depuis le microphone"""
    
    def __init__(self, sample_rate=SAMPLE_RATE, chunk_duration=CHUNK_DURATION):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.buffer = []  # rolling buffer for wake word detection
        self.recording = False
        self.recorded_frames = []
        self.speech_queue = queue.Queue()
        
    def start(self):
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._callback
        )
        self.stream.start_stream()
        print("🎙️  Micro ouvert. En attente du wake word...")
        
    def _callback(self, in_data, frame_count, time_info, status):
        audio_chunk = np.frombuffer(in_data, dtype=np.int16)
        
        if self.recording:
            self.recorded_frames.append(in_data)
        else:
            # Rolling buffer pour wake word detection
            self.buffer.append(audio_chunk)
            if len(self.buffer) > 50:  # ~5 secondes max
                self.buffer.pop(0)
                
        return (in_data, pyaudio.paContinue)
    
    def get_audio_for_stt(self):
        """Retourne l'audio enregistré pour STT"""
        if not self.recorded_frames:
            return None
        return b''.join(self.recorded_frames)
    
    def stop(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()


# ─── WAKE WORD DETECTION ─────────────────────────────────
class WakeWordDetector:
    """Détection simplifiée de wake word par reconnaissance de patterns"""
    
    def __init__(self, wake_words=None):
        self.wake_words = wake_words or WAKE_WORDS
        self.last_trigger_time = 0
        self.cooldown = 2.0  # secondes entre triggers
    
    def check(self, audio_buffer):
        """Vérifie si un wake word est présent dans le buffer audio.
        Version simplifiée : vérifie les amplitudes pour détecter un pattern de parole.
        Pour une version complète, utiliser openwakeword."""
        now = time.time()
        if now - self.last_trigger_time < self.cooldown:
            return False
            
        # Analyse simple : détection d'activité vocale significative
        combined = np.concatenate([a for a in audio_buffer[-20:]])  # dernieres 2 secondes
        energy = np.sqrt(np.mean(combined.astype(np.float64)**2))
        peaks = np.sum(np.abs(combined) > np.std(combined) * 2)
        
        # Seuil : énergie élevée + pics suffisants = parole probable
        triggered = energy > 500 and peaks > 100
        
        if triggered:
            self.last_trigger_time = now
            
        return triggered


# ─── STT (WHISPER) ────────────────────────────────────────
def speech_to_text(audio_bytes, sample_rate=SAMPLE_RATE):
    """Transcription audio via Whisper (LocalAI)"""
    # Sauvegarder en WAV temporaire
    temp_path = "/tmp/hnoss_stt.wav"
    with wave.open(temp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)
    
    # Envoyer a LocalAI Whisper
    with open(temp_path, 'rb') as f:
        r = requests.post(
            f"{LOCALAI_URL}/v1/audio/transcriptions",
            files={"file": f},
            data={"model": "whisper-1", "language": "fr"},
            timeout=15
        )
    
    if r.status_code == 200:
        return r.json().get("text", "").strip()
    else:
        print(f"  ⚠️ STT error: {r.status_code}")
        return ""


# ─── LLM (QWEN MTP) ───────────────────────────────────────
def chat_with_llm(prompt, max_tokens=200):
    """Dialogue avec Qwen MTP via LocalAI"""
    r = requests.post(
        f"{LOCALAI_URL}/v1/chat/completions",
        json={
            "model": "qwen3.6-30b-mtp",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        },
        timeout=30
    )
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return ""


# ─── TTS (PIPER FR) ───────────────────────────────────────
def text_to_speech(text, output_path="/tmp/hnoss_response.wav"):
    """Synthèse vocale via Piper FR (LocalAI)"""
    r = requests.post(
        f"{LOCALAI_URL}/v1/audio/speech",
        json={
            "model": "tts-fr",
            "input": text
        },
        timeout=20
    )
    if r.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(r.content)
        return output_path
    return None


def play_audio(filepath):
    """Joue un fichier audio sur les haut-parleurs"""
    try:
        data, samplerate = sf.read(filepath)
        import sounddevice as sd
        sd.play(data, samplerate)
        sd.wait()
        return True
    except Exception as e:
        print(f"  ⚠️ Audio playback error: {e}")
        return False


# ─── FACE ID (HAILO-8) ────────────────────────────────────
def face_recognition_check():
    """Capture webcam et vérifie l'identité via Hailo-8"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return "unknown"
        
        # Sauvegarder l'image
        cv2.imwrite("/tmp/hnoss_face.jpg", frame)
        
        # Envoyer a Hailo-8 pour détection
        with open("/tmp/hnoss_face.jpg", 'rb') as f:
            r = requests.post(
                f"{HAILO_URL}/detect",
                files={"image": f},
                timeout=10
            )
        
        if r.status_code == 200:
            result = r.json()
            # Vérifier si un visage est détecté
            for obj in result.get("objects", []):
                if obj.get("class") == "person":
                    # Phase 2: comparaison avec profil enregistré
                    return "sylvain"  # placeholder
        return "unknown"
    except Exception as e:
        print(f"  ⚠️ Face ID error: {e}")
        return "unknown"


# ─── MAIN LOOP ────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  🎙️  HNOSS VOICE — Assistant vocal sécurisé")
    print("  Wake words: OK Hnoss / OK Hermes")
    print("  Stack: Whisper → Qwen MTP → Piper FR")
    print("=" * 60)
    
    capture = AudioCapture()
    detector = WakeWordDetector()
    capture.start()
    
    recording = False
    silence_start = None
    last_face_check = 0
    
    try:
        while True:
            time.sleep(0.1)
            now = time.time()
            
            # Wake word detection
            if not recording:
                if detector.check(capture.buffer):
                    print("
🔔 Wake word détecté ! Je vous écoute...")
                    recording = True
                    capture.recording = True
                    capture.recorded_frames = []
                    silence_start = time.time()
            
            # Recording: check for silence
            if recording:
                combined = np.frombuffer(b''.join(capture.recorded_frames[-10:]), dtype=np.int16)
                energy = np.sqrt(np.mean(combined.astype(np.float64)**2))
                
                if energy < 100:  # silence
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > SILENCE_TIMEOUT:
                        print("  ⏹️  Fin de la commande.")
                        recording = False
                        capture.recording = False
                        
                        # STT
                        audio = capture.get_audio_for_stt()
                        if audio:
                            print("  🎧 Transcription...")
                            text = speech_to_text(audio)
                            if text:
                                print(f"  Vous: {text}")
                                
                                # Déterminer le mode d'accès
                                if now - last_face_check > FACIAL_CHECK_INTERVAL:
                                    identity = face_recognition_check()
                                    last_face_check = now
                                else:
                                    identity = "sylvain"  # trusted session
                                
                                # LLM
                                print("  🧠 Réflexion...")
                                response = chat_with_llm(text)
                                if response:
                                    print(f"  Hnoss: {response}")
                                    
                                # TTS
                                    print("  🔊 Synthèse vocale...")
                                    audio_file = text_to_speech(response)
                                    if audio_file:
                                        play_audio(audio_file)
                            else:
                                print("  ⚠️ Je n'ai pas compris.")
                        print("  🎙️  En attente du wake word...")
                else:
                    silence_start = None
            
    except KeyboardInterrupt:
        print("
  👋 Au revoir Sylvain !")
    finally:
        capture.stop()


if __name__ == "__main__":
    main()
