import os
import json
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import requests # New import for OpenRouter API calls

# --- Configuration ---
# It's highly recommended to set these as environment variables.
# Example:
# export MONGO_URI="mongodb://localhost:27017/"
# export MONGO_DB_NAME="your_database_name"
# export OPENROUTER_API_KEY="sk-YOUR_OPENROUTER_API_KEY" # Get this from openrouter.ai
# export LLM_MODEL="mistralai/mistral-7b-instruct" # A good, memory-efficient model on OpenRouter

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "test") # IMPORTANT: Change this to your actual database name
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct") # Default to a good OpenRouter model

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# --- MongoDB Helper Functions ---

def get_mongo_client(uri: str) -> MongoClient | None:
    """
    Establishes a connection to MongoDB.
    Args:
        uri (str): The MongoDB connection URI.
    Returns:
        MongoClient: The connected MongoDB client instance, or None if connection fails.
    """
    try:
        # Set serverSelectionTimeoutMS to a short duration for quick connection check
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        print(f"Successfully connected to MongoDB: {uri}")
        return client
    except ConnectionFailure as e:
        print(f"Error connecting to MongoDB at {uri}: {e}", file=sys.stderr)
        print("Please ensure MongoDB is running and accessible.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during MongoDB connection: {e}", file=sys.stderr)
        return None

def get_slow_queries(db: MongoClient, min_duration_ms: int = 100) -> list[dict]:
    """
    Retrieves slow queries from the system.profile collection.
    Requires profiling level to be set to 2 (db.setProfilingLevel(2)) or 1 with a threshold.
    Args:
        db (MongoClient): The MongoDB database object.
        min_duration_ms (int): Minimum duration in milliseconds for a query to be considered slow.
    Returns:
        list[dict]: A list of dictionaries, each representing a slow query with relevant details.
    """
    profile_collection_name = "system.profile"
    if profile_collection_name not in db.list_collection_names():
        print(f"Warning: '{profile_collection_name}' collection not found in '{db.name}'. "
              "Ensure profiling is enabled (e.g., db.setProfilingLevel(2)).", file=sys.stderr)
        return []

    profile_collection = db.get_collection(profile_collection_name)

    # Query for queries slower than min_duration_ms, focusing on 'query' and 'command' operations.
    # Sorting by 'millis' in descending order to get the slowest queries first.
    try:
        slow_queries = profile_collection.find(
            {"op": {"$in": ["query", "command", "update", "delete", "insert", "getmore"]},
             "millis": {"$gte": min_duration_ms}},
            projection={
                "ns": 1, "op": 1, "query": 1, "command": 1, "millis": 1,
                "planSummary": 1, "ts": 1, "type": 1, "nscannedObjects": 1, "nscanned": 1
            }
        ).sort("millis", -1)
    except OperationFailure as e:
        print(f"Error querying system.profile: {e}", file=sys.stderr)
        print("Ensure the connected user has read access to system.profile.", file=sys.stderr)
        return []

    extracted_queries = []
    for q in slow_queries:
        query_info = {
            "ns": q.get('ns'),
            "duration_ms": q.get('millis'),
            "planSummary": q.get('planSummary'), # High-level plan summary from profiling
            "ts": q.get('ts'),
            "op_type": q.get('op'),
            "nscannedObjects": q.get('nscannedObjects'), # Number of objects scanned
            "nscanned": q.get('nscanned') # Number of index entries scanned
        }

        if 'command' in q:
            # Modern MongoDB uses 'command' for most operations (find, aggregate, update, delete).
            # We need to extract the specific command details.
            command_details = q['command']
            query_info['type'] = "command"
            query_info['command_details'] = command_details

            # Try to identify common command types
            if 'find' in command_details:
                query_info['original_query_filter'] = command_details.get('filter')
                query_info['original_query_sort'] = command_details.get('sort')
                query_info['original_query_projection'] = command_details.get('projection')
            elif 'aggregate' in command_details:
                query_info['original_query_pipeline'] = command_details.get('pipeline')
            elif 'update' in command_details:
                query_info['original_query_filter'] = command_details.get('q') # For update
                query_info['original_query_update'] = command_details.get('u') # For update
            elif 'delete' in command_details:
                query_info['original_query_filter'] = command_details.get('q') # For delete
            # Add more parsing logic for other command types if needed

        elif 'query' in q:
            # Legacy 'query' field, less common in modern MongoDB for complex ops.
            # Often contains the filter document for find operations.
            query_info['type'] = "legacy_query"
            query_info['original_query_filter'] = q.get('query')
            query_info['original_query_orderby'] = q.get('orderby')

        extracted_queries.append(query_info)
    return extracted_queries

def get_collection_schema(db: MongoClient, collection_name: str, sample_size: int = 100) -> dict:
    """
    Infers a basic schema by sampling documents from a collection.
    This is a simplified inference. For complex schemas, consider MongoDB Schema Validation
    or specialized schema inference tools.
    Args:
        db (MongoClient): The MongoDB database object.
        collection_name (str): The name of the collection.
        sample_size (int): Number of documents to sample for schema inference.
    Returns:
        dict: A dictionary where keys are field names and values are their inferred types.
              Returns an empty dict if the collection does not exist or sampling fails.
    """
    collection = db.get_collection(collection_name)
    if collection is None:
        print(f"Collection '{collection_name}' not found.", file=sys.stderr)
        return {}

    schema = {}
    try:
        # Use aggregation with $sample for random document sampling
        sampled_docs = list(collection.aggregate([
            {"$sample": {"size": min(sample_size, collection.estimated_document_count() or sample_size)}}
        ]))
    except OperationFailure as e:
        print(f"Error sampling documents from '{collection_name}': {e}", file=sys.stderr)
        print("Ensure the connected user has read access to the collection.", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"An unexpected error occurred during schema inference for '{collection_name}': {e}", file=sys.stderr)
        return {}

    def get_type_name(value):
        if isinstance(value, dict):
            return "object"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, bool):
            return "boolean"
        elif value is None:
            return "null"
        else:
            return str(type(value).__name__)

    for doc in sampled_docs:
        for key, value in doc.items():
            current_type = get_type_name(value)
            if key not in schema:
                schema[key] = current_type
            elif schema[key] != current_type and schema[key] != "mixed":
                schema[key] = "mixed" # Indicate inconsistent types if multiple types are found

    return schema

def get_collection_indexes(db: MongoClient, collection_name: str) -> list[dict]:
    """
    Retrieves indexes for a given collection.
    Args:
        db (MongoClient): The MongoDB database object.
        collection_name (str): The name of the collection.
    Returns:
        list[dict]: A list of dictionaries, each representing an index.
                    Returns an empty list if the collection does not exist or access fails.
    """
    collection = db.get_collection(collection_name)
    if collection is None:
        print(f"Collection '{collection_name}' not found.", file=sys.stderr)
        return []
    try:
        # index_information() returns a dictionary of index details
        return list(collection.index_information().values())
    except OperationFailure as e:
        print(f"Error retrieving indexes for '{collection_name}': {e}", file=sys.stderr)
        print("Ensure the connected user has read access to the collection.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"An unexpected error occurred during index retrieval for '{collection_name}': {e}", file=sys.stderr)
        return []

def get_explain_plan(db: MongoClient, collection_name: str, query_info: dict) -> dict | None:
    """
    Runs an explain plan for a given query type and details.
    Args:
        db (MongoClient): The MongoDB database object.
        collection_name (str): The name of the collection involved in the query.
        query_info (dict): A dictionary containing parsed query details (e.g., filter, sort, pipeline).
    Returns:
        dict | None: The explain plan document, or None if it cannot be generated.
    """
    collection = db.get_collection(collection_name)
    if collection is None:
        return None

    op_type = query_info.get('op_type')

    try:
        # Handle both 'find' (from command) and 'query' (legacy) operations similarly.
        # 'original_query_filter' is used for the query itself.
        # 'original_query_sort' (from command) or 'original_query_orderby' (from legacy query) for sorting.
        if op_type in ["find", "query"] and (query_info.get('original_query_filter') is not None or query_info.get('original_query_sort') is not None or query_info.get('original_query_orderby') is not None):
            filter_doc = query_info.get('original_query_filter', {})
            # Prefer 'original_query_sort' if available, otherwise 'original_query_orderby'
            sort_doc = query_info.get('original_query_sort') or query_info.get('original_query_orderby')
            projection_doc = query_info.get('original_query_projection')

            cursor = collection.find(filter_doc)
            if sort_doc:
                cursor = cursor.sort(sort_doc)
            if projection_doc:
                cursor = cursor.project(projection_doc)

            return cursor.explain()

        elif op_type == "command" and 'aggregate' in query_info.get('command_details', {}):
            # For 'aggregate' commands
            pipeline = query_info['command_details'].get('pipeline', [])
            # For explain on aggregate, need to pass explain=True to the aggregate call
            # and then get the first result from the cursor.
            return collection.aggregate(pipeline, explain=True).next()

        elif op_type == "update" or op_type == "delete":
            # For update/delete operations, construct a dummy command to explain.
            # Explain plans for writes primarily show the query selection part.
            filter_doc = query_info.get('original_query_filter', {})
            if op_type == "update":
                # For update, we need a dummy update operation for the explain command.
                update_doc = query_info.get('original_query_update', {"$set": {"__dummy_field__": True}})
                return db.command("update", collection_name, updates=[{"q": filter_doc, "u": update_doc}], explain=True)
            elif op_type == "delete":
                # For delete operation.
                return db.command("delete", collection_name, deletes=[{"q": filter_doc}], explain=True)

        else:
            print(f"Explain plan not supported for operation type: {op_type} with provided query info.", file=sys.stderr)
            return None

    except OperationFailure as e:
        print(f"Error getting explain plan for '{collection_name}' (Operation Failure): {e}", file=sys.stderr)
        print("Ensure the connected user has necessary permissions to run explain.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred getting explain plan for '{collection_name}': {e}", file=sys.stderr)
        return None

# --- LLM Helper Functions ---

def build_llm_prompt(slow_query: dict, schema: dict, indexes: list[dict], explain_plan: dict | None) -> str:
    """
    Constructs a detailed prompt for the LLM based on extracted MongoDB data.
    Args:
        slow_query (dict): Dictionary containing details of the slow query.
        schema (dict): Inferred schema of the collection.
        indexes (list[dict]): List of existing indexes on the collection.
        explain_plan (dict | None): The explain plan for the query.
    Returns:
        str: The fully constructed prompt string.
    """
    prompt_parts = [
        "You are an expert MongoDB performance optimization assistant. "
        "Analyze the following slow MongoDB query and its context. "
        "Provide actionable recommendations to improve its performance. "
        "Focus on index recommendations, query rewrites, and data model advice.",
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
        "Note: This is an inferred sample schema. The actual schema might be more complex.",
        json.dumps(schema, indent=2, default=str),

        "\n--- Existing Indexes ---",
        json.dumps(indexes, indent=2, default=str),

        "\n--- Explain Plan (executionStats) ---",
        "Analyze the 'executionStats' or 'winningPlan' if available to understand query execution.",
        json.dumps(explain_plan, indent=2, default=str) if explain_plan else 'N/A',

        "\n--- Recommendations ---",
        "Based on the above information, provide a concise list of optimization suggestions. "
        "Ensure recommendations are specific and actionable. If no improvements are obvious, state that.",
        "1. **Index Recommendations**: Suggest specific index fields and types (e.g., `{'field': 1}` for ascending, `{'field': -1}` for descending, `{'field': 'text'}` for text index). Explain *why* the index is needed and how it helps the given query.",
        "2. **Query Rewrites**: If the query can be written more efficiently, provide the optimized version. Explain the changes.",
        "3. **Data Model Advice**: If the data model itself is contributing to slow performance, suggest structural changes (e.g., embedding vs. referencing, normalization/denormalization, sharding key considerations).",
        "4. **Other Performance Tips**: Include any other relevant advice (e.g., using `projection` to return only necessary fields, using `batchSize`, query hints, or considering aggregation pipeline optimization)."
    ]
    return "\n".join(prompt_parts)

def get_llm_recommendation(prompt: str, model: str = LLM_MODEL) -> str:
    """
    Sends the prompt to the LLM via OpenRouter API and returns the generated response.
    Args:
        prompt (str): The prompt to send to the LLM.
        model (str): The name of the LLM model to use on OpenRouter (e.g., 'mistralai/mistral-7b-instruct').
    Returns:
        str: The LLM's generated recommendations, or an error message if the call fails.
    """
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY environment variable is not set. Cannot connect to OpenRouter."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=120) # Increased timeout
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        json_response = response.json()

        if json_response and 'choices' in json_response and len(json_response['choices']) > 0:
            return json_response['choices'][0]['message']['content']
        else:
            return f"Failed to get LLM recommendations: Unexpected response structure. Response: {json.dumps(json_response, indent=2)}"

    except requests.exceptions.RequestException as e:
        print(f"OpenRouter API Request Error: {e}", file=sys.stderr)
        print(f"Check your internet connection, API key, and the model name: '{model}'.", file=sys.stderr)
        return f"Failed to get LLM recommendations due to network or API request error: {e}"
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error from OpenRouter API: {e}", file=sys.stderr)
        print(f"Response content: {response.text}", file=sys.stderr)
        return "Failed to get LLM recommendations due to invalid JSON response from OpenRouter."
    except Exception as e:
        print(f"An unexpected error occurred during OpenRouter LLM call: {e}", file=sys.stderr)
        return f"Failed to get LLM recommendations due to an unexpected error: {e}"

# --- Main Application Logic ---

def main():
    """
    Main function to orchestrate the MongoDB query optimization process.
    """
    print("Starting MongoDB Query Optimizer...\n")

    # 1. Connect to MongoDB
    client = get_mongo_client(MONGO_URI)
    if not client:
        sys.exit(1) # Exit if connection fails

    try:
        db = client.get_database(MONGO_DB_NAME)
        print(f"Targeting database: '{MONGO_DB_NAME}'")

        # 2. Extract slow queries
        print(f"\n--- Extracting slow queries from '{MONGO_DB_NAME}' (min duration: 100ms) ---")
        slow_queries = get_slow_queries(db, min_duration_ms=100) # Adjust threshold as needed

        if not slow_queries:
            print("No slow queries found in system.profile. "
                  "Please ensure MongoDB profiling is enabled (e.g., db.setProfilingLevel(2)).")
            print("Example command in mongosh: 'use your_database_name; db.setProfilingLevel(2);'")
            print("You might need to run some queries to populate the profile collection.")
            return

        print(f"Found {len(slow_queries)} slow queries. Analyzing each...\n")

        # Analyze each slow query (iterate over all found queries)
        num_queries_to_analyze = len(slow_queries) # Process all slow queries
        for i, sq in enumerate(slow_queries[:num_queries_to_analyze]):
            print(f"\n{'='*10} Analyzing Slow Query {i+1}/{num_queries_to_analyze} {'='*10}")
            print(f"Query Namespace: {sq.get('ns', 'N/A')}")
            print(f"Duration: {sq.get('duration_ms', 'N/A')} ms")
            print(f"Operation Type: {sq.get('op_type', 'N/A')}")
            print(f"Original Query Info: {json.dumps({k: v for k, v in sq.items() if k.startswith('original_query_') or k == 'command_details'}, indent=2, default=str)}")


            ns_parts = sq.get('ns', '').split('.', 1)
            if len(ns_parts) < 2:
                print(f"Skipping query with invalid namespace: '{sq.get('ns')}'", file=sys.stderr)
                continue

            collection_name = ns_parts[1]
            print(f"Collection: {collection_name}")

            # 3. Extract schema, indexes, and explain plan for the specific query
            print("  - Getting collection schema...")
            schema = get_collection_schema(db, collection_name)
            print("    Schema:")
            print(json.dumps(schema, indent=2, default=str)) # Print schema

            print("  - Getting existing indexes...")
            indexes = get_collection_indexes(db, collection_name)
            print("    Indexes:")
            print(json.dumps(indexes, indent=2, default=str)) # Print indexes

            print("  - Generating explain plan...")
            # For 'getmore' operations, explain plan is not directly available or meaningful.
            # The LLM will proceed with the available context.
            if sq.get('op_type') == "getmore":
                print("    Note: Explain plan is not directly supported for 'getmore' operations.")
                explain_plan = None
            else:
                explain_plan = get_explain_plan(db, collection_name, sq)
            print("    Explain Plan:")
            print(json.dumps(explain_plan, indent=2, default=str) if explain_plan else 'N/A') # Print explain plan


            # 4. Build context for the LLM
            print("  - Building LLM prompt...")
            prompt = build_llm_prompt(sq, schema, indexes, explain_plan)

            # 5. Use LLM to analyze and generate suggestions
            print("  - Requesting recommendations from LLM (this may take a moment)...")
            recommendation = get_llm_recommendation(prompt)

            # 6. Output recommendations via CLI
            print("\n--- Optimization Recommendations ---")
            print(recommendation)
            print(f"\n{'='*10} End of Query {i+1} Analysis {'='*10}\n")

    except Exception as e:
        print(f"An unexpected error occurred in the main application flow: {e}", file=sys.stderr)
    finally:
        # Ensure MongoDB client is closed
        if client:
            client.close()
            print("Disconnected from MongoDB.")
        print("\nMongoDB Query Optimizer finished.")

if __name__ == "__main__":
    main()
