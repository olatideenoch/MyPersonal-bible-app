"""Text-to-speech via the Voice RSS API (with chunking)."""
import re

import requests

from app.config import Config


def _fetch_voice_rss_chunk(text: str, voice: str = "en-us") -> bytes:
    """Fetch a single chunk from Voice RSS API"""
    data = {
        "key": Config.VOICE_RSS_API_KEY,
        "src": text,
        "hl": voice,
        "r": "0",
        "c": "mp3",
        "f": "44khz_16bit_stereo",
        "ssml": "false",
        "b64": "false"
    }
    
    try:
        response = requests.post(Config.VOICE_RSS_URL, data=data, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'audio' in content_type or response.content[:3] in [b'ID3', b'\xff\xfb']:
                return response.content
        return None
    except Exception as e:
        print(f"Voice RSS error: {e}")
        return None

def text_to_speech_voicerss(text: str, voice: str = "en-us") -> bytes:
    """Convert text to speech with chunking"""
    MAX_CHARS = 4500
    
    def chunk_text(text: str, max_length: int = 4500) -> list:
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_length]]

    chunks = chunk_text(text, MAX_CHARS)
    
    if len(chunks) == 1:
        return _fetch_voice_rss_chunk(chunks[0], voice)
    
    audio_chunks = []
    for chunk in chunks:
        chunk_audio = _fetch_voice_rss_chunk(chunk, voice)
        if chunk_audio is None:
            return None
        audio_chunks.append(chunk_audio)
    
    return b''.join(audio_chunks)
