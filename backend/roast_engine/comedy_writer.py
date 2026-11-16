import json
import re
from typing import Dict, Any, List
import httpx
from .pipeline_config import ROAST_INTENSITY, COMEDY_STYLES
from .personas import PERSONA_MAP


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
    # Graceful fallback: if JSON was truncated, extract "full_joke" values via regex first
    joke_matches = re.findall(r'"full_joke"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if joke_matches:
        jokes = []
        for idx, jm in enumerate(joke_matches[:10]):
            clean_j = jm.replace('\\"', '"').replace("\\n", " ").strip()
            jokes.append({
                "joke_id": f"J{idx+1:03d}",
                "category": "roast",
                "source_ammunition": ["visual"],
                "comedic_technique": "roast_battle",
                "setup": "",
                "punchline": clean_j,
                "full_joke": clean_j,
                "quality_score": max(78, 94 - idx * 2),
            })
        title_m = re.search(r'"roast_title"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
        open_m = re.search(r'"opening_line"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
        close_m = re.search(r'"closing_callback"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
        return {
            "roast_title": title_m.group(1) if title_m else "Da RoastBox Live Set",
            "opening_line": open_m.group(1) if open_m else "",
            "jokes": jokes,
            "closing_callback": close_m.group(1) if close_m else (jokes[-1]["full_joke"] if jokes else ""),
        }
    # Secondary fallback: parse plain-text jokes into structured schema
    lines = [ln.strip("-•*0123456789.) \t") for ln in raw.splitlines() if len(ln.strip()) > 20 and not ln.strip().startswith('"')]
    if not lines:
        raise ValueError("Comedy writer returned empty response")
    jokes = []
    for idx, ln in enumerate(lines[:8]):
        jokes.append({
            "joke_id": f"J{idx+1:03d}",
            "category": "roast",
            "source_ammunition": ["visual"],
            "comedic_technique": "roast_battle",
            "setup": "",
            "punchline": ln,
            "full_joke": ln,
            "quality_score": max(75, 92 - idx * 2),
        })
    return {
        "roast_title": "Da RoastBox Live Set",
        "opening_line": jokes[0]["full_joke"] if jokes else "",
        "jokes": jokes,
        "closing_callback": jokes[-1]["full_joke"] if len(jokes) > 1 else "",
    }


async def generate_comedy_pool(
    ammo_brief: Dict[str, Any],
    intensity_level: int,
    style_key: str,
    tier: str,
    openrouter_key: str,
    openai_key: str,
    openrouter_writer_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free",
    openrouter_fallback_model: str = "nvidia/nemotron-3.5-lightning:free",
    openai_model: str = "gpt-4o",
    persona_ids: List[str] = None,
) -> Dict[str, Any]:
    """
    Stage 4 & 5: Comedy Strategy & Multi-Style Joke Generation
    """
    intensity = ROAST_INTENSITY.get(intensity_level, ROAST_INTENSITY[4])
    style = COMEDY_STYLES.get(style_key, COMEDY_STYLES["roast_battle"])

    selected_personas = [PERSONA_MAP[pid] for pid in (persona_ids or []) if pid in PERSONA_MAP][:5]
    persona_block = ""
    if selected_personas:
        lines = ["ACTIVE ROASTERS ON STAGE (distribute the 10 jokes across these roasters and tag each joke with persona_id and persona_name):"]
        for p in selected_personas:
            lines.append(f"- {p['id']} ({p['displayName']} — {p['role']}, inspired by {p['comic_inspiration']}): {p['quirks_prompt']} Lingo: {', '.join(p['lingo'])}")
        persona_block = "\n".join(lines) + "\n\n"

    system_prompt = f"""You are the head writer of Da RoastBox, an uncensored 21+ adult comedy writers' room.
You write like a ruthless, sharp, professional insult comic — NEVER like a generic chatbot.

COMEDY STYLE: {style['name']}
{style['directive']}

{persona_block}INTENSITY LEVEL: {intensity_level}/5 ({intensity['name']})
- Aggression: {intensity['aggression']}/10
- Profanity: {intensity['profanity']}/10
- Exaggeration: {intensity['exaggeration']}/10
- Sarcasm: {intensity['sarcasm']}/10
- Punchline Impact: {intensity['punchline_impact']}/10
Directive: {intensity['tone_directive']}

CRITICAL WRITING RULES:
1. PUNCHLINE-FIRST: Find the sharpest, most unexpected ending first, then build a tight setup with misdirection.
2. NO GENERIC INSULTS: Every joke MUST reference specific visual details from the brief or user-submitted ammunition. Never invent visual details that aren't in the brief.
3. VARIETY: Use different comedic techniques across jokes (unexpected_comparison, misdirection, rule_of_three, escalation, callback, double_entendre, hyperbole, absurd_analogy, narrative_punchline).
4. NO FILLER: Cut unnecessary words. Make every punchline land hard.

Return ONLY valid JSON matching this exact schema (no markdown fences):
{{
  "roast_title": "Catchy, hilarious title for this roast set",
  "opening_line": "A killer 1-sentence stage entrance line",
  "jokes": [
    {{
      "joke_id": "J001",
      "category": "visual_roast | user_ammo | combo_roast | comparison | extended_setup",
      "source_ammunition": ["item1"],
      "comedic_technique": "unexpected_comparison",
      "setup": "The setup...",
      "punchline": "The punchline...",
      "full_joke": "The complete, natural-sounding joke ready to be spoken aloud",
      "quality_score": 88
    }}
  ],
  "closing_callback": "A devastating final callback line tying the top visual target and user ammo together"
}}

Generate 10 high-impact, distinct jokes."""

    user_prompt = f"""AMMUNITION BRIEF:
Visual Summary: {ammo_brief.get('visual_summary', '')}
First Impression: {ammo_brief.get('first_impression', '')}

TOP TWO VISUAL TARGETS:
{json.dumps(ammo_brief.get('top_two_targets', []), indent=2)}

RANKED VISUAL OBSERVATIONS:
{json.dumps(ammo_brief.get('ranked_visual_ammo', []), indent=2)}

USER-SUBMITTED AMMUNITION:
{json.dumps(ammo_brief.get('user_ammunition', []), indent=2)}

CONTEXTUAL COMBINATIONS TO EXPLOIT:
{json.dumps(ammo_brief.get('contextual_combinations', []), indent=2)}

Write 10 uncensored, razor-sharp, personalized roasts now. Return ONLY JSON."""

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
            openrouter_writer_model,
            openrouter_fallback_model,
            "baidu/ernie-5.5-flash-preview:free",
        ]

    last_error = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in models_to_try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.85,
                "max_tokens": 4096,
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
                    cost = usage.get("cost")
                    if cost is None:
                        if ":free" in model:
                            cost = 0.0
                        else:
                            cost = round((prompt_t * 2.5 + comp_t * 10.0) / 1_000_000, 6)
                    parsed = _extract_json(content)
                    parsed["_writer_model"] = model
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

    raise RuntimeError(f"Comedy generation failed across models. Last error: {last_error}")
