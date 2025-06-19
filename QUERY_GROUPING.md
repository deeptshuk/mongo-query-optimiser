# Query Grouping Feature

## Overview

The MongoDB Query Optimizer now includes intelligent query grouping functionality that significantly reduces redundant API calls by identifying and grouping structurally similar queries together. This feature addresses the common scenario where the same query pattern appears multiple times in the slow query log with only different variable values.

## Problem Solved

**Before**: If you had 100 slow queries that were structurally identical (e.g., `{user_id: 123, status: "active"}`, `{user_id: 456, status: "active"}`, etc.), the tool would make 100 separate API calls to analyze each query individually.

**After**: The tool now groups these similar queries together and analyzes only one representative query per group, potentially reducing 100 API calls to just 1.

## How It Works

### 1. Query Normalization

The system normalizes queries by replacing specific values with type placeholders:

```javascript
// Original queries
{user_id: 123, status: "active"}
{user_id: 456, status: "active"} 
{user_id: 789, status: "active"}

// Normalized structure
{user_id: "<int>", status: "<str>"}
```

### 2. Signature Generation

Each normalized query structure gets a unique signature (MD5 hash) that identifies the pattern:

```
Query Pattern: testdb.users.find({user_id: <int>, status: <str>})
Signature: 7f05bfc7b5b5...
```

### 3. Grouping and Representative Selection

- Queries with identical signatures are grouped together
- The slowest query from each group is selected as the representative
- Group metadata is attached to track the impact

## Supported Query Types

The grouping works across all MongoDB operation types:

### Find Queries
```javascript
// These will be grouped together:
db.users.find({user_id: 123, status: "active"})
db.users.find({user_id: 456, status: "active"})
db.users.find({user_id: 789, status: "active"})
```

### Aggregation Pipelines
```javascript
// These will be grouped together:
db.orders.aggregate([
  {$match: {product: "laptop", status: {$in: ["shipped", "delivered"]}}},
  {$group: {_id: "$user_id", total: {$sum: "$price"}}}
])

db.orders.aggregate([
  {$match: {product: "phone", status: {$in: ["shipped", "delivered"]}}},
  {$group: {_id: "$user_id", total: {$sum: "$price"}}}
])
```

### Update Operations
```javascript
// These will be grouped together:
db.users.updateOne({email: "user1@example.com"}, {$set: {last_login: new Date()}})
db.users.updateOne({email: "user2@example.com"}, {$set: {last_login: new Date()}})
```

## Output Changes

### Console Output
The tool now shows grouping information:

```
🔗 Grouping similar queries to optimize API usage...
📊 Found 23 total queries, grouped into 18 unique patterns
   📋 Pattern 10922abc... has 4 similar queries (analyzing slowest: 5ms)
   📋 Pattern 08b12aac... has 3 similar queries (analyzing slowest: 2ms)
📊 Analyzing top 3 representative queries out of 18

=============== Query Pattern 1/3 ===============
🔗 Represents 4 similar queries (avg: 1.8ms, max: 5ms)
```

### LLM Prompts
When a query represents multiple similar queries, the LLM prompt includes additional context:

```
=== QUERY GROUP INFORMATION ===
This query represents 4 similar queries with the same structure.
Duration range: 0ms - 5ms
Average duration: 1.8ms
Note: Optimizing this query pattern will improve performance for all similar queries.
```

## Configuration

The grouping feature is enabled by default and works with existing configuration options:

- `MAX_QUERIES_TO_ANALYZE`: Now applies to representative queries, not total queries
- All other settings remain unchanged

## Benefits

### 1. Reduced API Costs
- Fewer API calls to the LLM service
- Significant cost savings for large query logs

### 2. Faster Analysis
- Less time waiting for API responses
- More efficient processing of large datasets

### 3. Better Insights
- Focus on unique query patterns rather than duplicates
- Clear indication of how many queries each optimization affects

### 4. Improved Recommendations
- LLM recommendations now include context about the number of affected queries
- Better prioritization of optimization efforts

## Example Scenarios

### Scenario 1: User Activity Queries
```
Input: 50 queries like db.users.find({user_id: X, status: "active"})
Output: 1 representative query analysis
Savings: 49 API calls avoided
```

### Scenario 2: Order Analytics
```
Input: 25 aggregation queries with different product filters
Output: 1 representative aggregation analysis  
Savings: 24 API calls avoided
```

### Scenario 3: Mixed Workload
```
Input: 100 queries across 15 different patterns
Output: 15 representative query analyses
Savings: 85 API calls avoided
```

## Testing

Run the test script to see the grouping in action:

```bash
python test_query_grouping.py
```

This demonstrates how 8 sample queries are grouped into 4 unique patterns, saving 4 API calls.

## Technical Implementation

### Key Functions

- `normalize_query_structure()`: Replaces values with type placeholders
- `get_query_signature()`: Generates unique signatures for query patterns
- `group_similar_queries()`: Groups queries by signature
- `select_representative_query()`: Chooses the slowest query as representative

### Normalization Rules

- **Comparison operators** (`$eq`, `$gt`, etc.): Values become `<type>`
- **Array operators** (`$in`, `$nin`): Arrays become `<type_array>`
- **Text operators** (`$regex`, `$text`): Become generic patterns
- **Structural operators** (`$exists`, `$type`): Preserved as-is
- **Field names**: Preserved, values normalized recursively

## Future Enhancements

Potential improvements for future versions:

1. **Configurable grouping sensitivity**: Allow users to control how similar queries need to be
2. **Time-based grouping**: Group queries that occurred within specific time windows
3. **Collection-aware grouping**: Enhanced grouping based on collection characteristics
4. **Custom representative selection**: Choose representatives based on criteria other than duration

## Migration

This feature is backward compatible. Existing configurations and workflows continue to work without changes. The only difference is improved efficiency and additional grouping information in the output.
