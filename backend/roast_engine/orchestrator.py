import time
from typing import Dict, Any
from .image_processor import process_image
from .visual_analyzer import analyze_image
from .ammo_engine import build_ammunition_brief
from .comedy_writer import generate_comedy_pool
from .editorial import assemble_final_roast
from ..settings_store import AppSettings


async def run_roast_pipeline(
    image_bytes: bytes,
    user_ammo: str,
    intensity: int,
    style: str,
    settings: AppSettings,
    persona_ids: list = None,
) -> Dict[str, Any]:
    """
    Master DaRoastEngine Orchestrator (Stages 1-8)
    """
    t0 = time.time()

    # Stage 1: Image Ingestion
    data_url, image_meta = process_image(image_bytes)

    # Stage 2: Visual Intelligence
    visual_report = await analyze_image(
        data_url=data_url,
        tier=settings.preferred_tier,
        openrouter_key=settings.openrouter_api_key,
        openai_key=settings.openai_api_key,
        openrouter_vision_model=settings.openrouter_vision_model,
        openai_model=settings.openai_model,
    )

    # Stage 3: Roast Ammunition Engine
    ammo_brief = build_ammunition_brief(visual_report, user_ammo)

    # Stage 4 & 5: Comedy Strategy & Multi-Style Generation
    comedy_pool = await generate_comedy_pool(
        ammo_brief=ammo_brief,
        intensity_level=intensity,
        style_key=style,
        tier=settings.preferred_tier,
        openrouter_key=settings.openrouter_api_key,
        openai_key=settings.openai_api_key,
        openrouter_writer_model=settings.openrouter_writer_model,
        openrouter_fallback_model=settings.openrouter_fallback_model,
        openai_model=settings.openai_model,
        persona_ids=persona_ids,
    )

    # Stage 6 & 7: Critic & Final Assembly
    final_roast = assemble_final_roast(comedy_pool)

    elapsed = round(time.time() - t0, 2)
    v_usage = visual_report.get("_usage", {"model": visual_report.get("_model_used", "unknown"), "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0})
    w_usage = comedy_pool.get("_usage", {"model": final_roast.get("writer_model", "unknown"), "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0})

    return {
        "status": "success",
        "elapsed_seconds": elapsed,
        "tier_used": settings.preferred_tier,
        "vision_model": visual_report.get("_model_used", "unknown"),
        "writer_model": final_roast.get("writer_model", "unknown"),
        "telemetry": {
            "vision": v_usage,
            "writer": w_usage,
            "total_tokens": v_usage.get("total_tokens", 0) + w_usage.get("total_tokens", 0),
            "total_cost_usd": round(v_usage.get("cost_usd", 0.0) + w_usage.get("cost_usd", 0.0), 6),
        },
        "image_meta": image_meta,
        "visual_analysis": {
            "visual_summary": visual_report.get("visual_summary", ""),
            "first_impression": visual_report.get("first_impression", ""),
            "top_two_targets": ammo_brief.get("top_two_targets", []),
            "user_ammunition": ammo_brief.get("user_ammunition", []),
            "contextual_combinations": ammo_brief.get("contextual_combinations", []),
        },
        "roast": final_roast,
    }
