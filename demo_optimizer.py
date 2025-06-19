#!/usr/bin/env python3
"""
Demo script to show the MongoDB Query Optimizer in action
"""
import os
import sys
from mongo_optimiser.main import *
from mongo_optimiser.config import MONGO_DB_NAME
from mongo_optimiser.db_utils import (
    get_mongo_client, 
    get_slow_queries,
    get_collection_schema,
    get_collection_indexes,
    get_explain_plan
)
from mongo_optimiser.llm_utils import build_llm_prompt, get_llm_recommendation

def demo_optimizer():
    print("🚀 Starting MongoDB Query Optimizer Demo...")
    print("=" * 60)
    
    client = get_mongo_client()
    if not client:
        print("❌ Failed to connect to MongoDB")
        return
    
    try:
        db = client.get_database(MONGO_DB_NAME)
        print(f"✅ Connected to database: '{MONGO_DB_NAME}'")
        
        # Get slow queries with a very low threshold to capture our test queries
        print(f"\n🔍 Extracting slow queries from '{MONGO_DB_NAME}' (min duration: 0ms)")
        slow_queries = get_slow_queries(db, min_duration_ms=0)
        
        if not slow_queries:
            print("❌ No slow queries found in system.profile.")
            return
        
        print(f"📊 Found {len(slow_queries)} queries in profile collection")
        
        # Filter for find queries (more interesting for optimization)
        find_queries = [sq for sq in slow_queries if sq.get('op_type') == 'query' or 
                       (sq.get('type') == 'command' and 'find' in str(sq.get('command_details', {})))]
        
        if not find_queries:
            print("⚠️  No find queries found. Showing first query from profile:")
            queries_to_analyze = slow_queries[:1]
        else:
            print(f"🎯 Found {len(find_queries)} find queries. Analyzing the first one:")
            queries_to_analyze = find_queries[:1]
        
        for i, sq in enumerate(queries_to_analyze):
            print(f"\n{'='*20} Analyzing Query {i+1} {'='*20}")
            
            # Extract collection name
            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) < 2:
                print(f"⚠️  Skipping query with invalid namespace: '{sq.get('ns')}'")
                continue
            
            collection_name = ns_parts[1]
            print(f"📋 Collection: {collection_name}")
            print(f"⏱️  Duration: {sq.get('duration_ms', 'unknown')}ms")
            print(f"🔧 Operation: {sq.get('op_type', 'unknown')}")
            
            # Get collection metadata
            print(f"\n📈 Gathering collection metadata...")
            schema = get_collection_schema(db, collection_name)
            indexes = get_collection_indexes(db, collection_name)
            
            print(f"📊 Schema sample: {schema}")
            print(f"🗂️  Indexes: {[idx.get('name', str(idx)) for idx in indexes]}")
            
            # Get explain plan if it's not a getmore operation
            explain_plan = None
            if sq.get('op_type') != 'getmore':
                try:
                    explain_plan = get_explain_plan(db, collection_name, sq)
                    if explain_plan:
                        print(f"📋 Execution plan available")
                except Exception as e:
                    print(f"⚠️  Could not get explain plan: {e}")
            
            # Build prompt and get LLM recommendation
            print(f"\n🤖 Building LLM prompt...")
            prompt = build_llm_prompt(sq, schema, indexes, explain_plan)
            
            print(f"📝 Prompt preview: {prompt[:200]}...")
            
            print(f"\n🧠 Getting LLM recommendation...")
            recommendation = get_llm_recommendation(prompt)
            
            print(f"\n{'='*20} 💡 Optimization Recommendations {'='*20}")
            print(recommendation)
            print(f"{'='*60}")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()
            print("\n✅ Disconnected from MongoDB")
        print("\n🏁 MongoDB Query Optimizer Demo finished!")

if __name__ == "__main__":
    demo_optimizer()
