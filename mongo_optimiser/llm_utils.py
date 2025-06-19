import json
import sys
from typing import Any
import requests

from .config import OPENROUTER_API_KEY, LLM_MODEL, OPENROUTER_API_URL


def build_llm_prompt(slow_query: dict, schema: dict, indexes: list, explain_plan: dict | None) -> str:
    prompt_parts = [
        "You are an expert MongoDB performance optimization assistant. Analyze the following slow MongoDB query and its context and provide actionable recommendations.",
        "\n--- Slow Query Details ---",
        f"Namespace: {slow_query.get('ns', 'N/A')}",
        f"Operation Type: {slow_query.get('op_type', 'N/A')}",
        f"Duration (ms): {slow_query.get('duration_ms', 'N/A')}",
        f"Timestamp: {slow_query.get('ts', 'N/A')}",
        f"Number of Objects Scanned: {slow_query.get('nscannedObjects', 'N/A')}",
        f"Number of Index Entries Scanned: {slow_query.get('nscanned', 'N/A')}",
        "Original Query/Command Details:",
        json.dumps({k: v for k, v in slow_query.items() if k.startswith('original_query_') or k == 'command_details'}, indent=2, default=str),
        "\n--- Collection Schema Sample ---",
        json.dumps(schema, indent=2, default=str),
        "\n--- Existing Indexes ---",
        json.dumps(indexes, indent=2, default=str),
        "\n--- Explain Plan (executionStats) ---",
        json.dumps(explain_plan, indent=2, default=str) if explain_plan else 'N/A',
        "\n--- Recommendations ---",
        "1. Index Recommendations",
        "2. Query Rewrites",
        "3. Data Model Advice",
        "4. Other Performance Tips",
    ]
    return "\n".join(prompt_parts)


def get_llm_recommendation(prompt: str, model: str = LLM_MODEL) -> str:
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY environment variable is not set."

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        if data and 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        return f"Unexpected response from LLM: {json.dumps(data, indent=2)}"
    except requests.RequestException as e:
        print(f"OpenRouter API Request Error: {e}", file=sys.stderr)
        return "Failed to get LLM recommendations due to request error"
    except Exception as e:
        print(f"Unexpected error from LLM request: {e}", file=sys.stderr)
        return "Failed to get LLM recommendations"
