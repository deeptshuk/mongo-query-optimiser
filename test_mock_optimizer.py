#!/usr/bin/env python3
"""
Test script for MongoDB Query Optimizer with Mock LLM Service
"""
import os
import sys

# Set environment variables for mock service
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGO_DB_NAME'] = 'testdb'
os.environ['OPENROUTER_API_KEY'] = 'dummy_key'
os.environ['OPENROUTER_API_URL'] = 'http://localhost:8080/api/v1/chat/completions'

from mongo_optimiser.config import MONGO_DB_NAME
from mongo_optimiser.db_utils import (
    get_mongo_client,
    get_slow_queries,
    get_collection_schema,
    get_collection_indexes,
    get_explain_plan,
)
from mongo_optimiser.llm_utils import build_llm_prompt, get_llm_recommendation


def run_mock_test():
    print("🚀 Starting MongoDB Query Optimizer Test with Mock LLM...\n")

    client = get_mongo_client()
    if not client:
        sys.exit(1)

    try:
        db = client.get_database(MONGO_DB_NAME)
        print(f"✅ Connected to database: '{MONGO_DB_NAME}'")

        print(f"\n🔍 Extracting slow queries from '{MONGO_DB_NAME}' (min duration: 0ms) ---")
        slow_queries = get_slow_queries(db, min_duration_ms=0)

        if not slow_queries:
            print("❌ No queries found in system.profile.")
            return

        print(f"📊 Found {len(slow_queries)} queries. Analyzing first 1 with mock LLM...\n")
        
        # Just test one query with mock service
        sq = slow_queries[0]
        print(f"\n{'='*15} Analyzing Query with Mock LLM {'='*15}")
        ns_parts = sq.get('ns', '').split('.', 1)
        if len(ns_parts) < 2:
            print(f"⚠️  Skipping query with invalid namespace: '{sq.get('ns')}'")
            return

        collection_name = ns_parts[1]
        print(f"📋 Collection: {collection_name}")
        print(f"⏱️  Duration: {sq.get('duration_ms')}ms")
        print(f"🔧 Operation: {sq.get('op_type')}")

        print(f"\n📈 Gathering collection metadata...")
        schema = get_collection_schema(db, collection_name)
        indexes = get_collection_indexes(db, collection_name)
        explain_plan = None if sq.get('op_type') == 'getmore' else get_explain_plan(db, collection_name, sq)

        print(f"📊 Schema sample: {dict(list(schema.items())[:5])}")  # Show first 5 fields
        print(f"🗂️  Indexes: {[idx.get('key', {}) for idx in indexes]}")

        print(f"\n🤖 Getting Mock AI recommendations...")
        prompt = build_llm_prompt(sq, schema, indexes, explain_plan)
        recommendation = get_llm_recommendation(prompt)

        print("\n💡 Mock Optimization Recommendations:")
        print("=" * 50)
        print(recommendation)
        print("=" * 50)
        print(f"\n{'='*15} End of Mock Analysis {'='*15}\n")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()
            print("🔌 Disconnected from MongoDB.")
        print("\n✅ MongoDB Query Optimizer Mock Test finished.")


if __name__ == "__main__":
    run_mock_test()
