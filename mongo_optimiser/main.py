import json
import sys

from .config import MONGO_DB_NAME, MIN_DURATION_MS, MAX_QUERIES_TO_ANALYZE, EXCLUDE_OPERATIONS, ANALYSIS_TIME_WINDOW_MINUTES, validate_config
from .db_utils import (
    get_mongo_client,
    get_slow_queries,
    get_collection_schema,
    get_collection_indexes,
    get_explain_plan,
    clear_metadata_cache,
    print_cache_stats,
    group_similar_queries,
    select_representative_query,
)
from .llm_utils import build_llm_prompt, get_llm_recommendation


def run():
    """Main function to run the MongoDB Query Optimizer."""
    print("🚀 MongoDB Query Optimizer")
    print("=" * 50)

    # Validate configuration
    if not validate_config():
        print("\n❌ Configuration validation failed. Please check your .env file.")
        sys.exit(1)

    # Clear any existing cache
    clear_metadata_cache()

    # Get MongoDB client
    client = get_mongo_client()
    if not client:
        print("\n❌ Failed to connect to MongoDB")
        sys.exit(1)

    try:
        db = client.get_database(MONGO_DB_NAME)
        print(f"🗄️  Targeting database: '{MONGO_DB_NAME}'")

        print(f"\n🔍 Extracting slow queries (min duration: {MIN_DURATION_MS}ms)...")
        slow_queries = get_slow_queries(
            db,
            min_duration_ms=MIN_DURATION_MS,
            exclude_operations=EXCLUDE_OPERATIONS,
            time_window_minutes=ANALYSIS_TIME_WINDOW_MINUTES
        )

        if not slow_queries:
            print("❌ No slow queries found in system.profile.")
            print("💡 Ensure profiling is enabled: db.setProfilingLevel(2, {slowms: 0})")
            return

        # Group similar queries to avoid redundant API calls
        print(f"\n🔗 Grouping similar queries to optimize API usage...")
        grouped_queries = group_similar_queries(slow_queries)

        print(f"📊 Found {len(slow_queries)} total queries, grouped into {len(grouped_queries)} unique patterns")

        # Select representative queries from each group
        representative_queries = []
        for signature, similar_queries in grouped_queries.items():
            representative = select_representative_query(similar_queries)
            representative_queries.append(representative)
            if len(similar_queries) > 1:
                print(f"   📋 Pattern {signature[:8]}... has {len(similar_queries)} similar queries (analyzing slowest: {representative['duration_ms']}ms)")

        # Limit representative queries if configured
        total_representatives = len(representative_queries)
        if MAX_QUERIES_TO_ANALYZE > 0 and total_representatives > MAX_QUERIES_TO_ANALYZE:
            representative_queries = representative_queries[:MAX_QUERIES_TO_ANALYZE]
            print(f"📊 Analyzing top {MAX_QUERIES_TO_ANALYZE} representative queries out of {total_representatives}")
        else:
            print(f"📊 Analyzing all {total_representatives} representative queries")

        print(f"\n🔄 Starting analysis...")

        for i, sq in enumerate(representative_queries):
            group_info = sq.get('group_info', {})
            similar_count = group_info.get('total_similar_queries', 1)

            print(f"\n{'='*15} Query Pattern {i+1}/{len(representative_queries)} {'='*15}")
            if similar_count > 1:
                print(f"🔗 Represents {similar_count} similar queries (avg: {group_info.get('avg_duration_ms', 0):.1f}ms, max: {group_info.get('max_duration_ms', 0)}ms)")

            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) < 2:
                print(f"⚠️  Skipping query with invalid namespace: '{sq.get('ns')}'")
                continue

            collection_name = ns_parts[1]
            print(f"📋 Collection: {collection_name}")
            print(f"⏱️  Duration: {sq.get('duration_ms')}ms")
            print(f"🔧 Operation: {sq.get('op_type')}")

            # Get metadata (with caching)
            print(f"\n📊 COLLECTING METADATA FOR LLM:")
            print(f"   🔍 Getting schema for {collection_name}...")
            schema = get_collection_schema(db, collection_name)
            print(f"   ✅ Schema: {len(schema)} fields - {list(schema.keys())[:5]}{'...' if len(schema) > 5 else ''}")

            print(f"   🗂️  Getting indexes for {collection_name}...")
            indexes = get_collection_indexes(db, collection_name)
            print(f"   ✅ Indexes: {len(indexes)} indexes")
            for i, idx in enumerate(indexes):
                print(f"      Index {i+1}: {idx.get('key', 'N/A')}")

            print(f"   📋 Getting explain plan...")
            explain_plan = None if sq.get('op_type') == 'getmore' else get_explain_plan(db, collection_name, sq)
            if explain_plan:
                print(f"   ✅ Explain plan: Available ({len(str(explain_plan))} chars)")
                # Show key execution stats if available
                if 'executionStats' in explain_plan:
                    stats = explain_plan['executionStats']
                    print(f"      Execution time: {stats.get('executionTimeMillis', 'N/A')}ms")
                    print(f"      Documents examined: {stats.get('totalDocsExamined', 'N/A')}")
                    print(f"      Documents returned: {stats.get('totalDocsReturned', 'N/A')}")
                    print(f"      Index hits: {stats.get('totalKeysExamined', 'N/A')}")
            else:
                print(f"   ⚠️  Explain plan: Not available for {sq.get('op_type')} operation")

            # Show complete query details being sent to LLM
            print(f"\n📝 QUERY DETAILS BEING ANALYZED:")
            print(f"   Namespace: {sq.get('ns')}")
            print(f"   Operation: {sq.get('op_type')}")
            print(f"   Duration: {sq.get('duration_ms')}ms")
            print(f"   Plan Summary: {sq.get('planSummary', 'N/A')}")

            # Show original query/command if available
            query_details = {k: v for k, v in sq.items() if k.startswith('original_query_') or k == 'command_details'}
            if query_details:
                print(f"   Query/Command Details:")
                for key, value in query_details.items():
                    print(f"      {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")

            # Generate recommendations
            print(f"\n🤖 Generating AI recommendations...")
            prompt = build_llm_prompt(sq, schema, indexes, explain_plan)
            recommendation = get_llm_recommendation(prompt)

            print(f"\n💡 Optimization Recommendations:")
            print("=" * 50)
            print(recommendation)
            print("=" * 50)

        # Show cache efficiency
        print(f"\n📊 Analysis Complete!")
        print_cache_stats()

    except KeyboardInterrupt:
        print(f"\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client:
            client.close()
            print(f"\n🔌 Disconnected from MongoDB")
        print(f"✅ MongoDB Query Optimizer finished")


if __name__ == "__main__":
    run()
