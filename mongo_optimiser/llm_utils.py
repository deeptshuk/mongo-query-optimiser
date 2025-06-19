import json
import sys
from typing import Any, Dict, List, Optional
import requests

from .config import OPENROUTER_API_KEY, LLM_MODEL, OPENROUTER_API_URL


def build_llm_prompt(
    slow_query: Dict[str, Any],
    schema: Dict[str, str],
    indexes: List[Dict[str, Any]],
    explain_plan: Optional[Dict[str, Any]]
) -> str:
    """
    Build a comprehensive prompt for the LLM with query context.

    Args:
        slow_query: Dictionary containing slow query information
        schema: Collection schema mapping field names to types
        indexes: List of index information dictionaries
        explain_plan: Optional query execution plan

    Returns:
        Formatted prompt string for the LLM
    """
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
    """
    Get optimization recommendations from OpenRouter LLM API.

    Args:
        prompt: The formatted prompt containing query context
        model: LLM model to use (defaults to configured model)

    Returns:
        String containing the LLM's optimization recommendations
    """
    if not OPENROUTER_API_KEY:
        error_msg = "❌ OPENROUTER_API_KEY environment variable is not set"
        print(error_msg, file=sys.stderr)
        return error_msg

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,  # Limit response length
        "temperature": 0.1   # Lower temperature for more focused responses
    }

    try:
        print(f"🔗 Calling OpenRouter API with model: {model}")
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        data = response.json()
        if data and 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content']
            print(f"✅ Received {len(content)} characters from LLM")
            return content
        else:
            error_msg = f"❌ Unexpected API response format: {json.dumps(data, indent=2)}"
            print(error_msg, file=sys.stderr)
            return error_msg

    except requests.exceptions.Timeout:
        error_msg = "❌ OpenRouter API request timed out (120s)"
        print(error_msg, file=sys.stderr)
        return error_msg
    except requests.exceptions.HTTPError as e:
        error_msg = f"❌ OpenRouter API HTTP error: {e.response.status_code} - {e.response.text}"
        print(error_msg, file=sys.stderr)
        return error_msg
    except requests.RequestException as e:
        error_msg = f"❌ OpenRouter API request error: {e}"
        print(error_msg, file=sys.stderr)
        return error_msg
    except json.JSONDecodeError as e:
        error_msg = f"❌ Failed to parse API response as JSON: {e}"
        print(error_msg, file=sys.stderr)
        return error_msg
    except Exception as e:
        error_msg = f"❌ Unexpected error calling LLM API: {e}"
        print(error_msg, file=sys.stderr)
        return error_msg
