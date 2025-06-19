import json
import sys

from .config import MONGO_DB_NAME
from .db_utils import (
    get_mongo_client,
    get_slow_queries,
    get_collection_schema,
    get_collection_indexes,
    get_explain_plan,
)
from .llm_utils import build_llm_prompt, get_llm_recommendation


def run():
    print("Starting MongoDB Query Optimizer...\n")

    client = get_mongo_client()
    if not client:
        sys.exit(1)

    try:
        db = client.get_database(MONGO_DB_NAME)
        print(f"Targeting database: '{MONGO_DB_NAME}'")

        print(f"\n--- Extracting slow queries from '{MONGO_DB_NAME}' (min duration: 100ms) ---")
        slow_queries = get_slow_queries(db, min_duration_ms=100)

        if not slow_queries:
            print("No slow queries found in system.profile. Ensure profiling is enabled.")
            return

        print(f"Found {len(slow_queries)} slow queries. Analyzing each...\n")
        for i, sq in enumerate(slow_queries):
            print(f"\n{'='*10} Analyzing Slow Query {i+1}/{len(slow_queries)} {'='*10}")
            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) < 2:
                print(f"Skipping query with invalid namespace: '{sq.get('ns')}'", file=sys.stderr)
                continue

            collection_name = ns_parts[1]
            print(f"Collection: {collection_name}")

            schema = get_collection_schema(db, collection_name)
            indexes = get_collection_indexes(db, collection_name)
            explain_plan = None if sq.get('op_type') == 'getmore' else get_explain_plan(db, collection_name, sq)

            prompt = build_llm_prompt(sq, schema, indexes, explain_plan)
            recommendation = get_llm_recommendation(prompt)

            print("\n--- Optimization Recommendations ---")
            print(recommendation)
            print(f"\n{'='*10} End of Query {i+1} Analysis {'='*10}\n")
    finally:
        if client:
            client.close()
            print("Disconnected from MongoDB.")
        print("\nMongoDB Query Optimizer finished.")


if __name__ == "__main__":
    run()
