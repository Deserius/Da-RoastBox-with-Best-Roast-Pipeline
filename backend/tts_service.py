import io
import edge_tts
import httpx


async def generate_edge_tts(text: str, voice: str = "en-US-GuyNeural") -> bytes:
    """Free high-quality neural TTS using Microsoft Edge TTS."""
    communicate = edge_tts.Communicate(text, voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


async def generate_elevenlabs_tts(
    text: str,
    api_key: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
) -> bytes:
    """Premium TTS using ElevenLabs API."""
    if not api_key.strip():
        raise ValueError("ElevenLabs API key is required for Premium TTS. Add it in Settings.")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.80,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }
    async with httpx.AsyncClient(timeout=45.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"ElevenLabs error (HTTP {resp.status_code}): {resp.text[:200]}")
        return resp.content
