import json
import re
from typing import Dict, Any, List, Optional
import httpx

VISION_SYSTEM_PROMPT = """You are an elite visual intelligence analyst for a professional comedy writers' room.
Your job is NOT to write jokes. Your job is to observe the uploaded photograph with surgical precision and extract roastable visual facts.

Identify:
- Facial presentation and expression
- Hairstyle, facial hair, and grooming choices
- Clothing, accessories, and styling
- Pose, posture, and body positioning
- Camera angle, framing, lighting, and photographic presentation
- Background objects and environmental details
- Unusual combinations of visible styling choices
- Overall first impression

RULES:
1. Only report what is ACTUALLY visible. Never invent features.
2. You MUST identify at least ONE prominent personal facial or physical feature of the individual themselves (e.g., facial expression, hairline, eyebrows, jawline, smile, eyes, nose, posture, or build — minus clothing/objects) and include it as one of the `top_two_targets`, even if it looks normal.
3. Score visual_prominence (0-10), confidence (0-10), and comedy_potential (0-10).
4. Select the TOP TWO strongest visual comedy targets: Target 1 should be the most prominent personal facial/physical feature of the individual, and Target 2 should be the strongest styling/pose/background detail.
4. Return ONLY valid JSON matching this exact schema, with no markdown fences or extra text:

{
  "visual_summary": "2-3 sentence objective summary of the image",
  "first_impression": "The immediate vibe/archetype this photo gives off",
  "observable_features": [
    {
      "feature": "short_feature_name",
      "observation": "specific visible detail",
      "visual_prominence": 8,
      "confidence": 9,
      "comedy_potential": 8,
      "comedy_angles": ["angle 1", "angle 2"]
    }
  ],
  "top_two_targets": [
    {
      "feature_reference": "short_feature_name",
      "reason_selected": "why this is prime comedy ammunition",
      "possible_comedy_angles": ["angle 1", "angle 2"]
    }
  ],
  "background_opportunities": ["detail 1"],
  "presentation_opportunities": ["lighting/angle/pose detail"],
  "uncertain_observations": []
}"""


def _extract_json(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    # Graceful fallback: wrap plain-text vision output into the VisualAnalysis schema
    lines = [ln.strip("-•* \t") for ln in raw.splitlines() if ln.strip()]
    summary = " ".join(lines[:3]) if lines else raw[:400]
    features = []
    for idx, ln in enumerate(lines[:5]):
        features.append({
            "feature": f"visual_detail_{idx+1}",
            "observation": ln[:220],
            "visual_prominence": 8 - idx,
            "confidence": 8,
            "comedy_potential": 8,
            "comedy_angles": ["exaggerate", "absurd comparison"],
        })
    return {
        "visual_summary": summary,
        "first_impression": lines[0][:160] if lines else "Distinctive visual presentation",
        "observable_features": features,
        "top_two_targets": [
            {
                "feature_reference": f["feature"],
                "reason_selected": f["observation"],
                "possible_comedy_angles": f["comedy_angles"],
            }
            for f in features[:2]
        ],
        "background_opportunities": [],
        "presentation_opportunities": [],
        "uncertain_observations": [],
    }


async def analyze_image(
    data_url: str,
    tier: str,
    openrouter_key: str,
    openai_key: str,
    openrouter_vision_model: str = "google/gemma-4-26b-a4b-it:free",
    openai_model: str = "gpt-4o",
) -> Dict[str, Any]:
    """
    Stage 2: Visual Intelligence
    """
    if tier == "premium" and openai_key.strip():
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_key.strip()}",
            "Content-Type": "application/json",
        }
        models_to_try = [openai_model]
    else:
        if not openrouter_key.strip():
            raise ValueError("OpenRouter API key is required for Free Tier. Please add it in Settings.")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openrouter_key.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://daroastbox.app",
            "X-Title": "Da RoastBox",
        }
        models_to_try = [
            openrouter_vision_model,
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3.5-super-vl:free",
        ]

    last_error = None
    async with httpx.AsyncClient(timeout=45.0) as client:
        for model in models_to_try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": VISION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image for our comedy writers' room. Return ONLY the JSON object.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url},
                            },
                        ],
                    },
                ],
                "temperature": 0.3,
                "max_tokens": 2500,
            }
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data["choices"][0].get("message", {})
                    content = msg.get("content") or msg.get("reasoning") or ""
                    usage = data.get("usage", {})
                    prompt_t = usage.get("prompt_tokens", 0)
                    comp_t = usage.get("completion_tokens", 0)
                    total_t = usage.get("total_tokens", prompt_t + comp_t)
                    # OpenRouter sometimes returns usage.cost; otherwise $0 for :free or estimate for paid
                    cost = usage.get("cost")
                    if cost is None:
                        if ":free" in model:
                            cost = 0.0
                        else:
                            cost = round((prompt_t * 2.5 + comp_t * 10.0) / 1_000_000, 6)
                    parsed = _extract_json(content)
                    parsed["_model_used"] = model
                    parsed["_usage"] = {
                        "model": model,
                        "prompt_tokens": prompt_t,
                        "completion_tokens": comp_t,
                        "total_tokens": total_t,
                        "cost_usd": round(float(cost), 6),
                    }
                    return parsed
                else:
                    last_error = f"{model} HTTP {resp.status_code}: {resp.text[:250]}"
            except Exception as e:
                last_error = f"{model} error: {str(e)}"

    raise RuntimeError(f"Vision analysis failed across models. Last error: {last_error}")
