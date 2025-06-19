import json
import sys
import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from .config import MONGO_MODE, MONGO_DB_NAME, build_mongo_uri, EXCLUDE_OPERATIONS, ANALYSIS_TIME_WINDOW_MINUTES
from .docker_utils import start_mongodb_container, is_docker_available

# Global cache for collection metadata
_metadata_cache: Dict[str, Dict[str, Any]] = {}


def clear_metadata_cache() -> None:
    """Clear the metadata cache."""
    global _metadata_cache
    _metadata_cache.clear()
    print("🗑️  Metadata cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    schema_entries = sum(1 for key in _metadata_cache.keys() if key.endswith('.schema'))
    index_entries = sum(1 for key in _metadata_cache.keys() if key.endswith('.indexes'))

    return {
        "total_entries": len(_metadata_cache),
        "schema_entries": schema_entries,
        "index_entries": index_entries,
        "collections_cached": schema_entries  # Assuming schema and indexes are cached together
    }


def print_cache_stats() -> None:
    """Print cache statistics."""
    stats = get_cache_stats()
    print(f"📊 Cache Stats: {stats['total_entries']} entries, {stats['collections_cached']} collections cached")


def normalize_query_structure(query_obj: Any) -> Any:
    """
    Normalize a query object by replacing specific values with placeholders.
    This helps group similar queries that differ only in variable values.

    Args:
        query_obj: The query object to normalize (can be dict, list, or primitive)

    Returns:
        Normalized query object with values replaced by type placeholders
    """
    if isinstance(query_obj, dict):
        normalized = {}
        for key, value in query_obj.items():
            if key in ['$eq', '$ne', '$gt', '$gte', '$lt', '$lte', '$in', '$nin']:
                # For comparison operators, replace values with type placeholders
                if isinstance(value, (list, tuple)):
                    # For $in/$nin arrays, use a placeholder based on first element type
                    if value and len(value) > 0:
                        first_type = type(value[0]).__name__
                        normalized[key] = f"<{first_type}_array>"
                    else:
                        normalized[key] = "<empty_array>"
                else:
                    normalized[key] = f"<{type(value).__name__}>"
            elif key in ['$regex', '$text', '$where']:
                # For text-based operators, use generic placeholders
                normalized[key] = f"<{key[1:]}_pattern>"
            elif key in ['$exists', '$type', '$size']:
                # Keep structural operators as-is since they define query structure
                normalized[key] = value
            elif key.startswith('$'):
                # For other operators, recursively normalize
                normalized[key] = normalize_query_structure(value)
            else:
                # For field names, recursively normalize the value
                normalized[key] = normalize_query_structure(value)
        return normalized
    elif isinstance(query_obj, (list, tuple)):
        return [normalize_query_structure(item) for item in query_obj]
    else:
        # For primitive values, replace with type placeholder
        return f"<{type(query_obj).__name__}>"


def get_query_signature(query_info: Dict[str, Any]) -> str:
    """
    Generate a unique signature for a query based on its structure.
    Queries with the same signature are considered similar and can be grouped.

    Args:
        query_info: Dictionary containing query information

    Returns:
        String signature representing the query structure
    """
    # Extract the key components that define query structure
    signature_components = {
        'ns': query_info.get('ns'),
        'op_type': query_info.get('op_type'),
        'type': query_info.get('type')
    }

    # Normalize query components
    if query_info.get('original_query_filter'):
        signature_components['filter'] = normalize_query_structure(query_info['original_query_filter'])

    if query_info.get('original_query_sort') or query_info.get('original_query_orderby'):
        sort_obj = query_info.get('original_query_sort') or query_info.get('original_query_orderby')
        signature_components['sort'] = normalize_query_structure(sort_obj)

    if query_info.get('original_query_projection'):
        signature_components['projection'] = normalize_query_structure(query_info['original_query_projection'])

    if query_info.get('original_query_pipeline'):
        signature_components['pipeline'] = normalize_query_structure(query_info['original_query_pipeline'])

    if query_info.get('original_query_update'):
        signature_components['update'] = normalize_query_structure(query_info['original_query_update'])

    # Create a stable hash of the normalized structure
    signature_json = json.dumps(signature_components, sort_keys=True, default=str)
    return hashlib.md5(signature_json.encode()).hexdigest()


def group_similar_queries(queries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group queries by their structural similarity.

    Args:
        queries: List of query information dictionaries

    Returns:
        Dictionary mapping query signatures to lists of similar queries
    """
    grouped_queries: Dict[str, List[Dict[str, Any]]] = {}

    for query in queries:
        signature = get_query_signature(query)
        if signature not in grouped_queries:
            grouped_queries[signature] = []
        grouped_queries[signature].append(query)

    return grouped_queries


def select_representative_query(similar_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Select the most representative query from a group of similar queries.
    Currently selects the slowest query, but could be enhanced with other criteria.

    Args:
        similar_queries: List of similar queries

    Returns:
        The representative query from the group
    """
    if not similar_queries:
        raise ValueError("Cannot select representative from empty query list")

    # Select the query with the highest duration as the representative
    representative = max(similar_queries, key=lambda q: q.get('duration_ms', 0))

    # Add metadata about the group
    representative['group_info'] = {
        'total_similar_queries': len(similar_queries),
        'min_duration_ms': min(q.get('duration_ms', 0) for q in similar_queries),
        'max_duration_ms': max(q.get('duration_ms', 0) for q in similar_queries),
        'avg_duration_ms': sum(q.get('duration_ms', 0) for q in similar_queries) / len(similar_queries),
        'query_signatures': [get_query_signature(q) for q in similar_queries[:3]]  # Sample of signatures
    }

    return representative


def get_mongo_client() -> Optional[MongoClient]:
    """
    Get MongoDB client with automatic local container management.

    Returns:
        MongoClient instance if successful, None otherwise
    """
    # Handle local mode - start Docker container if needed
    if MONGO_MODE == "local":
        print(f"🐳 Local mode: Managing MongoDB Docker container...")

        if not is_docker_available():
            print("❌ Docker is not available for local mode")
            return None

        if not start_mongodb_container():
            print("❌ Failed to start MongoDB container")
            return None

    # Build connection URI
    uri = build_mongo_uri()

    try:
        print(f"🔗 Connecting to MongoDB ({MONGO_MODE} mode)...")
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        print(f"✅ Successfully connected to MongoDB")
        return client
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}", file=sys.stderr)
        if MONGO_MODE == "local":
            print("💡 Try running: docker ps to check container status")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None


def get_slow_queries(
    db: MongoClient,
    min_duration_ms: int = 100,
    exclude_operations: Optional[List[str]] = None,
    time_window_minutes: int = 0
) -> List[Dict[str, Any]]:
    profile_collection_name = "system.profile"
    if profile_collection_name not in db.list_collection_names():
        print(
            f"Warning: '{profile_collection_name}' not found in '{db.name}'. Ensure profiling is enabled.",
            file=sys.stderr,
        )
        return []

    profile_collection = db.get_collection(profile_collection_name)
    try:
        # Build query filter
        query_filter = {"millis": {"$gte": min_duration_ms}}

        # Include operations filter (exclude specified operations)
        if exclude_operations is None:
            exclude_operations = EXCLUDE_OPERATIONS

        all_operations = ["query", "command", "update", "delete", "insert", "getmore"]
        included_operations = [op for op in all_operations if op not in exclude_operations]

        if included_operations:
            query_filter["op"] = {"$in": included_operations}

        # Add time window filter
        if time_window_minutes > 0:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            query_filter["ts"] = {"$gte": cutoff_time}

        print(f"🔍 Query filter: {query_filter}")
        print(f"📊 Excluded operations: {exclude_operations}")
        if time_window_minutes > 0:
            print(f"⏰ Time window: last {time_window_minutes} minutes")

        slow_queries = profile_collection.find(
            query_filter,
            projection={
                "ns": 1,
                "op": 1,
                "query": 1,
                "command": 1,
                "millis": 1,
                "planSummary": 1,
                "ts": 1,
                "type": 1,
                "nscannedObjects": 1,
                "nscanned": 1,
            },
        ).sort("millis", -1)
    except OperationFailure as e:
        print(f"Error querying system.profile: {e}", file=sys.stderr)
        return []

    extracted_queries: List[Dict[str, Any]] = []
    for q in slow_queries:
        query_info: Dict[str, Any] = {
            "ns": q.get("ns"),
            "duration_ms": q.get("millis"),
            "planSummary": q.get("planSummary"),
            "ts": q.get("ts"),
            "op_type": q.get("op"),
            "nscannedObjects": q.get("nscannedObjects"),
            "nscanned": q.get("nscanned"),
        }

        if "command" in q:
            cmd = q["command"]
            query_info["type"] = "command"
            query_info["command_details"] = cmd
            if "find" in cmd:
                query_info["original_query_filter"] = cmd.get("filter")
                query_info["original_query_sort"] = cmd.get("sort")
                query_info["original_query_projection"] = cmd.get("projection")
            elif "aggregate" in cmd:
                query_info["original_query_pipeline"] = cmd.get("pipeline")
            elif "update" in cmd:
                query_info["original_query_filter"] = cmd.get("q")
                query_info["original_query_update"] = cmd.get("u")
            elif "delete" in cmd:
                query_info["original_query_filter"] = cmd.get("q")
        elif "query" in q:
            query_info["type"] = "legacy_query"
            query_info["original_query_filter"] = q.get("query")
            query_info["original_query_orderby"] = q.get("orderby")

        extracted_queries.append(query_info)
    return extracted_queries


def get_collection_schema(db: MongoClient, collection_name: str, sample_size: int = 100) -> Dict[str, str]:
    """
    Get collection schema with caching support.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection
        sample_size: Number of documents to sample for schema analysis

    Returns:
        Dictionary mapping field names to their types
    """
    cache_key = f"{db.name}.{collection_name}.schema"

    # Check cache first
    if cache_key in _metadata_cache:
        print(f"📋 Schema cache HIT for {collection_name}")
        return _metadata_cache[cache_key]["data"]

    print(f"📋 Schema cache MISS for {collection_name} - computing...")

    collection = db.get_collection(collection_name)
    if collection is None:
        print(f"Collection '{collection_name}' not found.", file=sys.stderr)
        return {}

    try:
        sampled_docs = list(
            collection.aggregate(
                [{"$sample": {"size": min(sample_size, collection.estimated_document_count() or sample_size)}}]
            )
        )
    except OperationFailure as e:
        print(f"Error sampling documents from '{collection_name}': {e}", file=sys.stderr)
        return {}

    def get_type(value: Any) -> str:
        if isinstance(value, dict):
            return "object"
        if isinstance(value, list):
            return "array"
        if isinstance(value, str):
            return "string"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, bool):
            return "boolean"
        if value is None:
            return "null"
        return type(value).__name__

    schema: Dict[str, str] = {}
    for doc in sampled_docs:
        for k, v in doc.items():
            t = get_type(v)
            if k not in schema:
                schema[k] = t
            elif schema[k] != t and schema[k] != "mixed":
                schema[k] = "mixed"

    # Cache the result
    _metadata_cache[cache_key] = {
        "data": schema,
        "timestamp": time.time()
    }

    return schema


def get_collection_indexes(db: MongoClient, collection_name: str) -> List[Dict[str, Any]]:
    """
    Get collection indexes with caching support.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection

    Returns:
        List of index information dictionaries
    """
    cache_key = f"{db.name}.{collection_name}.indexes"

    # Check cache first
    if cache_key in _metadata_cache:
        print(f"🗂️  Indexes cache HIT for {collection_name}")
        return _metadata_cache[cache_key]["data"]

    print(f"🗂️  Indexes cache MISS for {collection_name} - retrieving...")

    collection = db.get_collection(collection_name)
    if collection is None:
        print(f"Collection '{collection_name}' not found.", file=sys.stderr)
        return []

    try:
        indexes = list(collection.index_information().values())

        # Cache the result
        _metadata_cache[cache_key] = {
            "data": indexes,
            "timestamp": time.time()
        }

        return indexes
    except OperationFailure as e:
        print(f"Error retrieving indexes for '{collection_name}': {e}", file=sys.stderr)
        return []


def get_explain_plan(db: MongoClient, collection_name: str, query_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    collection = db.get_collection(collection_name)
    if collection is None:
        return None

    op_type = query_info.get("op_type")
    try:
        if op_type in ["find", "query"] and (
            query_info.get("original_query_filter") is not None
            or query_info.get("original_query_sort") is not None
            or query_info.get("original_query_orderby") is not None
        ):
            filter_doc = query_info.get("original_query_filter", {})
            sort_doc = query_info.get("original_query_sort") or query_info.get("original_query_orderby")
            projection_doc = query_info.get("original_query_projection")
            cursor = collection.find(filter_doc)
            if sort_doc:
                cursor = cursor.sort(sort_doc)
            if projection_doc:
                cursor = cursor.project(projection_doc)
            return cursor.explain()
        if op_type == "command" and "aggregate" in query_info.get("command_details", {}):
            pipeline = query_info["command_details"].get("pipeline", [])
            # Use database.command for explain with aggregation
            explain_cmd = {
                "explain": {
                    "aggregate": collection_name,
                    "pipeline": pipeline,
                    "cursor": {}
                }
            }
            return db.command(explain_cmd)
        if op_type in {"update", "delete"}:
            filter_doc = query_info.get("original_query_filter", {})
            if op_type == "update":
                update_doc = query_info.get("original_query_update", {"$set": {"__dummy_field__": True}})
                return db.command("update", collection_name, updates=[{"q": filter_doc, "u": update_doc}], explain=True)
            return db.command("delete", collection_name, deletes=[{"q": filter_doc}], explain=True)
    except OperationFailure as e:
        print(f"Error getting explain plan for '{collection_name}': {e}", file=sys.stderr)
        return None
    return None
