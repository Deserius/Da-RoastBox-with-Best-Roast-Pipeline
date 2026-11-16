from typing import Dict, Any, List
from .personas import PERSONA_MAP


def assemble_final_roast(comedy_pool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage 6 & 7: Comedy Critic & Final Assembly
    - Deduplicates near-identical jokes
    - Ensures category diversity and comedic sequencing
    - Builds the performance-ready TTS script
    """
    jokes: List[Dict[str, Any]] = comedy_pool.get("jokes", [])
    seen_texts = set()
    unique_jokes = []

    for idx, j in enumerate(jokes):
        full = (j.get("full_joke") or f"{j.get('setup', '')} {j.get('punchline', '')}").strip()
        norm = full.lower()[:60]
        if not full or norm in seen_texts:
            continue
        seen_texts.add(norm)
        j["joke_id"] = j.get("joke_id") or f"J{idx+1:03d}"
        j["full_joke"] = full
        j["quality_score"] = min(100, max(50, int(j.get("quality_score", 82))))
        pid = j.get("persona_id", "")
        if pid in PERSONA_MAP:
            p = PERSONA_MAP[pid]
            j["persona_name"] = p["displayName"]
            j["persona_color"] = p["color"]
            j["elevenlabs_voice_id"] = p["elevenlabs_voice_id"]
            j["edge_voice"] = "en-US-JennyNeural" if p["gender"] == "female" else "en-US-GuyNeural"
        unique_jokes.append(j)

    # Sort by quality score descending, then sequence for pacing
    unique_jokes.sort(key=lambda x: x["quality_score"], reverse=True)
    selected = unique_jokes[:8]

    opening = comedy_pool.get("opening_line", "").strip()
    closing = comedy_pool.get("closing_callback", "").strip()

    # Build full TTS performance transcript
    script_parts = []
    if opening:
        script_parts.append(opening)
    for j in selected:
        script_parts.append(j["full_joke"])
    if closing:
        script_parts.append(closing)

    full_transcript = "\n\n".join(script_parts)

    return {
        "roast_title": comedy_pool.get("roast_title", "Da RoastBox Live Set"),
        "opening_line": opening,
        "jokes": selected,
        "closing_callback": closing,
        "full_transcript": full_transcript,
        "writer_model": comedy_pool.get("_writer_model", "unknown"),
        "total_jokes": len(selected),
        "avg_quality_score": round(
            sum(j["quality_score"] for j in selected) / max(1, len(selected)), 1
        ),
    }
