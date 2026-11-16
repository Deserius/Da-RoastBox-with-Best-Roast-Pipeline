from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .settings_store import (
    AppSettings,
    load_settings,
    save_settings,
    mask_key,
    verify_openrouter_key,
    verify_openai_key,
    verify_elevenlabs_key,
)
from .roast_engine.pipeline_config import ROAST_INTENSITY, COMEDY_STYLES
from .roast_engine.personas import PERSONAS
from .roast_engine.orchestrator import run_roast_pipeline
from .tts_service import generate_edge_tts, generate_elevenlabs_tts

app = FastAPI(title="Da RoastBox! API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_FILE = Path(__file__).parent.parent / "frontend" / "index.html"
ASSETS_DIR = Path(__file__).parent.parent / "frontend" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if FRONTEND_FILE.exists():
        return HTMLResponse(content=FRONTEND_FILE.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Da RoastBox! Frontend not found</h1>", status_code=404)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "Da RoastBox!"}


@app.get("/api/config")
async def get_config():
    return {
        "intensities": ROAST_INTENSITY,
        "styles": COMEDY_STYLES,
    }


@app.get("/api/personas")
async def get_personas():
    return {"personas": PERSONAS}


@app.get("/api/settings")
async def get_settings():
    s = load_settings()
    return {
        "preferred_tier": s.preferred_tier,
        "preferred_tts": s.preferred_tts,
        "openrouter_vision_model": s.openrouter_vision_model,
        "openrouter_writer_model": s.openrouter_writer_model,
        "openrouter_fallback_model": s.openrouter_fallback_model,
        "openai_model": s.openai_model,
        "elevenlabs_voice_id": s.elevenlabs_voice_id,
        "edge_tts_voice": s.edge_tts_voice,
        "custom_api_base_url": s.custom_api_base_url,
        "has_openrouter_key": bool(s.openrouter_api_key.strip()),
        "has_openai_key": bool(s.openai_api_key.strip()),
        "has_elevenlabs_key": bool(s.elevenlabs_api_key.strip()),
        "has_custom_key": bool(s.custom_api_key.strip()),
        "masked_openrouter_key": mask_key(s.openrouter_api_key),
        "masked_openai_key": mask_key(s.openai_api_key),
        "masked_elevenlabs_key": mask_key(s.elevenlabs_api_key),
        "masked_custom_key": mask_key(s.custom_api_key),
    }


class SettingsUpdate(BaseModel):
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_api_base_url: Optional[str] = None
    preferred_tier: Optional[str] = None
    preferred_tts: Optional[str] = None
    openrouter_vision_model: Optional[str] = None
    openrouter_writer_model: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    edge_tts_voice: Optional[str] = None


@app.post("/api/settings")
async def update_settings(payload: SettingsUpdate):
    current = load_settings()
    data = current.model_dump()
    for field, val in payload.model_dump(exclude_none=True).items():
        # Only overwrite API key if user actually typed a new non-empty value or explicitly cleared it
        data[field] = val
    updated = save_settings(AppSettings(**data))

    # Run authenticity checks on saved keys
    checks = {
        "openrouter": await verify_openrouter_key(updated.openrouter_api_key),
        "openai": await verify_openai_key(updated.openai_api_key),
        "elevenlabs": await verify_elevenlabs_key(updated.elevenlabs_api_key),
    }
    return {"status": "saved", "checks": checks}


@app.post("/api/settings/verify")
async def verify_all_keys():
    s = load_settings()
    return {
        "openrouter": await verify_openrouter_key(s.openrouter_api_key),
        "openai": await verify_openai_key(s.openai_api_key),
        "elevenlabs": await verify_elevenlabs_key(s.elevenlabs_api_key),
    }


@app.post("/api/roast/generate")
async def generate_roast(
    image: UploadFile = File(...),
    user_ammo: str = Form(""),
    intensity: int = Form(4),
    style: str = Form("roast_battle"),
    personas: str = Form(""),
):
    settings = load_settings()
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file uploaded.")

    persona_ids = [p.strip() for p in personas.split(",") if p.strip()][:5]

    try:
        result = await run_roast_pipeline(
            image_bytes=image_bytes,
            user_ammo=user_ammo,
            intensity=intensity,
            style=style,
            settings=settings,
            persona_ids=persona_ids,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TTSRequest(BaseModel):
    text: str
    engine: Optional[str] = None  # "edge" or "elevenlabs"
    voice: Optional[str] = None


@app.post("/api/tts/speak")
async def speak_text(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is required for TTS.")

    settings = load_settings()
    engine = req.engine or settings.preferred_tts

    try:
        if engine == "elevenlabs":
            audio_bytes = await generate_elevenlabs_tts(
                text=req.text,
                api_key=settings.elevenlabs_api_key,
                voice_id=req.voice or settings.elevenlabs_voice_id,
            )
        else:
            audio_bytes = await generate_edge_tts(
                text=req.text,
                voice=req.voice or settings.edge_tts_voice,
            )
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
