import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"


class AppSettings(BaseModel):
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""
    custom_api_key: str = ""
    custom_api_base_url: str = ""
    preferred_tier: str = "free"  # "free" (OpenRouter) or "premium" (OpenAI)
    preferred_tts: str = "edge"   # "edge" (Free Neural), "browser" (Web Speech), "elevenlabs" (Premium)
    openrouter_vision_model: str = "google/gemma-4-26b-a4b-it:free"
    openrouter_writer_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    openrouter_fallback_model: str = "nvidia/nemotron-3.5-lightning:free"
    openai_model: str = "gpt-4o"
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel default
    edge_tts_voice: str = "en-US-GuyNeural"


def load_settings() -> AppSettings:
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return AppSettings(**data)
        except Exception:
            pass
    return AppSettings()


def save_settings(settings: AppSettings) -> AppSettings:
    SETTINGS_FILE.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
    return settings


def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "" if not key else "****"
    return f"{key[:6]}...{key[-4:]}"


async def verify_openrouter_key(api_key: str) -> Dict[str, Any]:
    if not api_key.strip():
        return {"status": "not_set", "valid": False, "message": "No OpenRouter API key provided"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key.strip()}"},
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                label = data.get("label", "Active Key")
                is_free = data.get("is_free_tier", True)
                return {
                    "status": "valid",
                    "valid": True,
                    "message": f"Authenticated ({label} • {'Free Tier' if is_free else 'Paid Tier'})",
                }
            return {
                "status": "invalid",
                "valid": False,
                "message": f"OpenRouter rejected key (HTTP {resp.status_code})",
            }
    except Exception as e:
        return {"status": "error", "valid": False, "message": f"Connection error: {str(e)}"}


async def verify_openai_key(api_key: str) -> Dict[str, Any]:
    if not api_key.strip():
        return {"status": "not_set", "valid": False, "message": "No OpenAI API key provided"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key.strip()}"},
            )
            if resp.status_code == 200:
                return {"status": "valid", "valid": True, "message": "OpenAI key authenticated & ready"}
            return {
                "status": "invalid",
                "valid": False,
                "message": f"OpenAI rejected key (HTTP {resp.status_code})",
            }
    except Exception as e:
        return {"status": "error", "valid": False, "message": f"Connection error: {str(e)}"}


async def verify_elevenlabs_key(api_key: str) -> Dict[str, Any]:
    if not api_key.strip():
        return {"status": "not_set", "valid": False, "message": "No ElevenLabs API key provided"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": api_key.strip()},
            )
            if resp.status_code == 200:
                data = resp.json()
                sub = data.get("subscription", {})
                tier = sub.get("tier", "active")
                char_count = sub.get("character_count", 0)
                char_limit = sub.get("character_limit", 0)
                return {
                    "status": "valid",
                    "valid": True,
                    "message": f"ElevenLabs ({tier}) • {char_count:,}/{char_limit:,} chars used",
                }
            return {
                "status": "invalid",
                "valid": False,
                "message": f"ElevenLabs rejected key (HTTP {resp.status_code})",
            }
    except Exception as e:
        return {"status": "error", "valid": False, "message": f"Connection error: {str(e)}"}
