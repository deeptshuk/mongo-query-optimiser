#!/usr/bin/env python3
"""
Test script for MongoDB Query Optimizer with lower threshold
"""
import os
import sys

# Set environment variables
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGO_DB_NAME'] = 'testdb'
os.environ['OPENROUTER_API_KEY'] = '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'

from mongo_optimiser.config import MONGO_DB_NAME
from mongo_optimiser.db_utils import (
    get_mongo_client,
    get_slow_queries,
    get_collection_schema,
    get_collection_indexes,
    get_explain_plan,
)
from mongo_optimiser.llm_utils import build_llm_prompt, get_llm_recommendation


def run_test():
    print("🚀 Starting MongoDB Query Optimizer Test...\n")

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

        print(f"📊 Found {len(slow_queries)} queries. Analyzing first 2...\n")
        
        for i, sq in enumerate(slow_queries[:2]):  # Limit to first 2 for testing
            print(f"\n{'='*15} Analyzing Query {i+1}/2 {'='*15}")
            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) < 2:
                print(f"⚠️  Skipping query with invalid namespace: '{sq.get('ns')}'")
                continue

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

            print(f"\n🤖 Getting AI recommendations...")
            prompt = build_llm_prompt(sq, schema, indexes, explain_plan)
            recommendation = get_llm_recommendation(prompt)

            print("\n💡 Optimization Recommendations:")
            print("=" * 50)
            print(recommendation)
            print("=" * 50)
            print(f"\n{'='*15} End of Query {i+1} Analysis {'='*15}\n")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    finally:
        if client:
            client.close()
            print("🔌 Disconnected from MongoDB.")
        print("\n✅ MongoDB Query Optimizer Test finished.")


if __name__ == "__main__":
    run_test()
