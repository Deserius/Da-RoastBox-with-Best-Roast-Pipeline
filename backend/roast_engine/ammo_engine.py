from typing import Dict, Any, List


def build_ammunition_brief(visual_report: Dict[str, Any], user_ammo_raw: str) -> Dict[str, Any]:
    """
    Stage 3: Roast Ammunition Engine
    - Extracts top two visual targets
    - Parses user-submitted ammunition
    - Scores and ranks visual features: A = 0.30V + 0.25R + 0.20C + 0.15U + 0.10O
    - Generates contextual combinations between visual targets and user ammunition
    """
    user_items = [
        item.strip()
        for item in user_ammo_raw.replace("\n", ",").split(",")
        if item.strip()
    ]

    features = visual_report.get("observable_features", [])
    ranked_visual: List[Dict[str, Any]] = []

    for idx, feat in enumerate(features):
        v = float(feat.get("visual_prominence", 5))
        c = float(feat.get("comedy_potential", 5))
        o = float(feat.get("confidence", 7))
        # Relevance to user-submitted material
        obs_lower = (feat.get("observation", "") + " " + feat.get("feature", "")).lower()
        r = 8.0 if any(u.lower() in obs_lower for u in user_items) else 4.0
        u = max(3.0, 9.0 - idx * 0.8)  # Uniqueness heuristic

        score = round(0.30 * v + 0.25 * r + 0.20 * c + 0.15 * u + 0.10 * o, 2)
        ranked_visual.append({
            "source": "visual",
            "feature": feat.get("feature", f"feature_{idx+1}"),
            "observation": feat.get("observation", ""),
            "angles": feat.get("comedy_angles", []),
            "score": score,
        })

    ranked_visual.sort(key=lambda x: x["score"], reverse=True)

    top_two = visual_report.get("top_two_targets", [])[:2]
    if not top_two and ranked_visual:
        top_two = [
            {
                "feature_reference": item["feature"],
                "reason_selected": item["observation"],
                "possible_comedy_angles": item["angles"],
            }
            for item in ranked_visual[:2]
        ]

    # Synthesize contextual combinations
    combinations: List[str] = []
    for target in top_two:
        t_name = target.get("feature_reference", "their look")
        for u_item in user_items[:3]:
            combinations.append(f"Combine [{t_name}] with user fact: '{u_item}'")

    return {
        "top_two_targets": top_two,
        "ranked_visual_ammo": ranked_visual[:6],
        "user_ammunition": user_items,
        "contextual_combinations": combinations,
        "first_impression": visual_report.get("first_impression", ""),
        "visual_summary": visual_report.get("visual_summary", ""),
    }
