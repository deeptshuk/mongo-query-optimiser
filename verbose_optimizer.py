#!/usr/bin/env python3
"""
Verbose MongoDB Query Optimizer - Shows detailed workflow
"""
import os
import sys
import json
import time

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


def verbose_run():
    print("🚀 VERBOSE MongoDB Query Optimizer Analysis")
    print("=" * 80)
    print(f"📅 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 MongoDB URI: {os.environ['MONGO_URI']}")
    print(f"🗄️  Database: {os.environ['MONGO_DB_NAME']}")
    print(f"🔑 API Key: {os.environ['OPENROUTER_API_KEY'][:20]}...")
    print("=" * 80)

    # STEP 1: Connect to MongoDB
    print("\n📡 STEP 1: Connecting to MongoDB...")
    start_time = time.time()
    client = get_mongo_client()
    if not client:
        print("❌ Connection failed!")
        sys.exit(1)
    connect_time = time.time() - start_time
    print(f"✅ Connected in {connect_time:.2f}s")

    try:
        db = client.get_database(MONGO_DB_NAME)
        
        # STEP 2: Extract slow queries (BATCH OPERATION)
        print(f"\n🔍 STEP 2: Extracting slow queries from system.profile...")
        print(f"   📊 Query: {{\"op\": {{\"$in\": [\"query\", \"command\", \"update\", \"delete\", \"insert\", \"getmore\"]}}, \"millis\": {{\"$gte\": 0}}}}")
        start_time = time.time()
        slow_queries = get_slow_queries(db, min_duration_ms=0)  # Using 0ms to capture test queries
        extract_time = time.time() - start_time
        
        print(f"✅ Extracted {len(slow_queries)} queries in {extract_time:.2f}s")
        print(f"   📋 Query types found: {set(sq.get('op_type') for sq in slow_queries)}")
        print(f"   ⏱️  Duration range: {min(sq.get('duration_ms', 0) for sq in slow_queries)}-{max(sq.get('duration_ms', 0) for sq in slow_queries)}ms")

        if not slow_queries:
            print("❌ No queries found!")
            return

        # STEP 3: Process each query individually (ONE-BY-ONE)
        print(f"\n🔄 STEP 3: Processing queries ONE-BY-ONE...")
        print(f"   ⚠️  NOTE: Schema/Index metadata is computed FRESH for each query!")
        
        for i, sq in enumerate(slow_queries[:2]):  # Limit to 2 for demo
            print(f"\n{'='*20} PROCESSING QUERY {i+1}/{min(len(slow_queries), 2)} {'='*20}")
            
            # Parse namespace
            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) < 2:
                print(f"⚠️  Skipping invalid namespace: {sq.get('ns')}")
                continue

            collection_name = ns_parts[1]
            print(f"📋 Collection: {collection_name}")
            print(f"⏱️  Duration: {sq.get('duration_ms')}ms")
            print(f"🔧 Operation: {sq.get('op_type')}")
            print(f"📅 Timestamp: {sq.get('ts')}")
            
            # Show raw query details
            print(f"\n📝 Raw Query Details:")
            for key, value in sq.items():
                if key.startswith('original_query_') or key == 'command_details':
                    print(f"   {key}: {json.dumps(value, default=str, indent=6)}")

            # STEP 3a: Get collection schema (FRESH COMPUTATION)
            print(f"\n📊 STEP 3a: Computing collection schema...")
            start_time = time.time()
            schema = get_collection_schema(db, collection_name)
            schema_time = time.time() - start_time
            print(f"✅ Schema computed in {schema_time:.3f}s")
            print(f"   📈 Fields found: {len(schema)}")
            print(f"   🏷️  Sample fields: {dict(list(schema.items())[:5])}")

            # STEP 3b: Get collection indexes (FRESH COMPUTATION)
            print(f"\n🗂️  STEP 3b: Retrieving collection indexes...")
            start_time = time.time()
            indexes = get_collection_indexes(db, collection_name)
            index_time = time.time() - start_time
            print(f"✅ Indexes retrieved in {index_time:.3f}s")
            print(f"   📊 Index count: {len(indexes)}")
            for idx_num, idx in enumerate(indexes):
                print(f"   Index {idx_num + 1}: {idx.get('key', {})}")

            # STEP 3c: Get explain plan (FRESH COMPUTATION)
            print(f"\n📋 STEP 3c: Getting explain plan...")
            start_time = time.time()
            explain_plan = None if sq.get('op_type') == 'getmore' else get_explain_plan(db, collection_name, sq)
            explain_time = time.time() - start_time
            if explain_plan:
                print(f"✅ Explain plan generated in {explain_time:.3f}s")
                print(f"   📊 Execution stats available: {bool(explain_plan.get('executionStats'))}")
            else:
                print(f"⚠️  No explain plan available ({explain_time:.3f}s)")

            # STEP 3d: Build LLM prompt
            print(f"\n🤖 STEP 3d: Building LLM prompt...")
            start_time = time.time()
            prompt = build_llm_prompt(sq, schema, indexes, explain_plan)
            prompt_time = time.time() - start_time
            print(f"✅ Prompt built in {prompt_time:.3f}s")
            print(f"   📏 Prompt length: {len(prompt)} characters")
            print(f"   📝 Prompt preview:")
            print("   " + "\n   ".join(prompt.split('\n')[:10]))
            print("   ...")

            # STEP 3e: Call LLM API (INDIVIDUAL API CALL)
            print(f"\n🧠 STEP 3e: Calling OpenRouter API...")
            start_time = time.time()
            recommendation = get_llm_recommendation(prompt)
            api_time = time.time() - start_time
            print(f"✅ API response received in {api_time:.2f}s")
            print(f"   📏 Response length: {len(recommendation)} characters")

            # Show recommendations
            print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
            print("=" * 60)
            print(recommendation)
            print("=" * 60)
            
            total_query_time = schema_time + index_time + explain_time + prompt_time + api_time
            print(f"\n⏱️  Total time for this query: {total_query_time:.2f}s")
            print(f"   - Schema: {schema_time:.3f}s")
            print(f"   - Indexes: {index_time:.3f}s") 
            print(f"   - Explain: {explain_time:.3f}s")
            print(f"   - Prompt: {prompt_time:.3f}s")
            print(f"   - API: {api_time:.2f}s")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()
            print(f"\n🔌 Disconnected from MongoDB")
        print(f"\n✅ Analysis completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    verbose_run()
