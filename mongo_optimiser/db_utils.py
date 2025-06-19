import json
import sys
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from .config import MONGO_URI, MONGO_DB_NAME


def get_mongo_client(uri: str = MONGO_URI) -> Optional[MongoClient]:
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print(f"Successfully connected to MongoDB: {uri}")
        return client
    except ConnectionFailure as e:
        print(f"Error connecting to MongoDB at {uri}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error connecting to MongoDB: {e}", file=sys.stderr)
        return None


def get_slow_queries(db: MongoClient, min_duration_ms: int = 100) -> List[Dict[str, Any]]:
    profile_collection_name = "system.profile"
    if profile_collection_name not in db.list_collection_names():
        print(
            f"Warning: '{profile_collection_name}' not found in '{db.name}'. Ensure profiling is enabled.",
            file=sys.stderr,
        )
        return []

    profile_collection = db.get_collection(profile_collection_name)
    try:
        slow_queries = profile_collection.find(
            {"op": {"$in": ["query", "command", "update", "delete", "insert", "getmore"]}, "millis": {"$gte": min_duration_ms}},
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
    return schema


def get_collection_indexes(db: MongoClient, collection_name: str) -> List[Dict[str, Any]]:
    collection = db.get_collection(collection_name)
    if collection is None:
        print(f"Collection '{collection_name}' not found.", file=sys.stderr)
        return []
    try:
        return list(collection.index_information().values())
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
            return collection.aggregate(pipeline, explain=True).next()
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
