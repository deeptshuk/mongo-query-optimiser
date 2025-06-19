#!/usr/bin/env python3
"""
Analysis of metadata computation efficiency
"""
import os
import sys
import time
from collections import defaultdict

# Set environment variables
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/'
os.environ['MONGO_DB_NAME'] = 'testdb'

from mongo_optimiser.db_utils import (
    get_mongo_client,
    get_slow_queries,
    get_collection_schema,
    get_collection_indexes,
)


def analyze_metadata_computation():
    print("🔍 METADATA COMPUTATION ANALYSIS")
    print("=" * 60)
    
    client = get_mongo_client()
    if not client:
        sys.exit(1)

    try:
        db = client.get_database('testdb')
        
        # Get all slow queries
        slow_queries = get_slow_queries(db, min_duration_ms=0)
        print(f"📊 Found {len(slow_queries)} queries")
        
        # Analyze collection distribution
        collection_counts = defaultdict(int)
        for sq in slow_queries:
            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) >= 2:
                collection_counts[ns_parts[1]] += 1
        
        print(f"\n📋 Collection distribution:")
        for collection, count in collection_counts.items():
            print(f"   {collection}: {count} queries")
        
        print(f"\n⚠️  CURRENT INEFFICIENCY:")
        print(f"   - Schema is computed {sum(collection_counts.values())} times")
        print(f"   - Indexes are retrieved {sum(collection_counts.values())} times")
        print(f"   - But we only have {len(collection_counts)} unique collections!")
        
        # Demonstrate the inefficiency
        print(f"\n🧪 DEMONSTRATING REDUNDANT COMPUTATION:")
        total_schema_time = 0
        total_index_time = 0
        
        for i, sq in enumerate(slow_queries[:5]):  # Test first 5
            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) < 2:
                continue
                
            collection_name = ns_parts[1]
            print(f"\nQuery {i+1} - Collection: {collection_name}")
            
            # Time schema computation
            start = time.time()
            schema = get_collection_schema(db, collection_name)
            schema_time = time.time() - start
            total_schema_time += schema_time
            
            # Time index retrieval
            start = time.time()
            indexes = get_collection_indexes(db, collection_name)
            index_time = time.time() - start
            total_index_time += index_time
            
            print(f"   Schema: {schema_time:.3f}s ({len(schema)} fields)")
            print(f"   Indexes: {index_time:.3f}s ({len(indexes)} indexes)")
        
        print(f"\n📊 EFFICIENCY ANALYSIS:")
        print(f"   Total schema computation time: {total_schema_time:.3f}s")
        print(f"   Total index retrieval time: {total_index_time:.3f}s")
        print(f"   Wasted time due to recomputation: ~{(total_schema_time + total_index_time) * 0.8:.3f}s")
        
        # Show what optimal caching would look like
        print(f"\n💡 OPTIMAL APPROACH WITH CACHING:")
        unique_collections = set()
        for sq in slow_queries:
            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) >= 2:
                unique_collections.add(ns_parts[1])
        
        print(f"   Collections to cache: {len(unique_collections)}")
        print(f"   Cache once, reuse {sum(collection_counts.values())} times")
        print(f"   Estimated time savings: ~{(total_schema_time + total_index_time) * 0.8:.3f}s per run")
        
        # Show the actual schema sampling process
        print(f"\n🔬 SCHEMA SAMPLING DETAILS:")
        for collection in unique_collections:
            coll = db.get_collection(collection)
            doc_count = coll.estimated_document_count()
            print(f"   {collection}: {doc_count} documents")
            
            # Show what the schema function actually does
            start = time.time()
            sample_docs = list(coll.aggregate([{"$sample": {"size": min(100, doc_count or 100)}}]))
            sample_time = time.time() - start
            print(f"     Sampling {len(sample_docs)} docs took {sample_time:.3f}s")
            
            # Show field analysis
            all_fields = set()
            for doc in sample_docs:
                all_fields.update(doc.keys())
            print(f"     Found {len(all_fields)} unique fields: {list(all_fields)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    analyze_metadata_computation()
