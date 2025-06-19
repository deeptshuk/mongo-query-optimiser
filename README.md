# MongoDB Query Optimizer

An intelligent MongoDB performance analysis tool that identifies slow queries and provides AI-powered optimization recommendations using Large Language Models.

## ✨ Features

- **Automated Query Analysis**: Extracts slow queries from MongoDB's `system.profile` collection
- **AI-Powered Recommendations**: Uses OpenRouter LLM APIs to generate intelligent optimization suggestions
- **Smart Query Grouping**: Automatically groups similar queries to avoid redundant API calls and reduce costs
- **Metadata Caching**: Efficient caching system to avoid redundant schema/index computations
- **Local & Remote Support**: Automatic Docker container management for local testing or connect to remote MongoDB
- **Enhanced Seed Data**: Realistic test data generator with multiple collections and slow query patterns
- **Configurable Analysis**: Customizable thresholds and query limits via environment variables

## 📋 Prerequisites

- **Python 3.8+**
- **OpenRouter API Key** - Get one from [openrouter.ai](https://openrouter.ai/)
- **Docker** (optional, for local mode)
- **MongoDB 3.6+** (for remote mode)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd mongo-query-optimiser

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required Configuration:**
- Set `OPENROUTER_API_KEY` to your API key from [openrouter.ai](https://openrouter.ai/)
- Choose `MONGO_MODE`: `local` (Docker) or `remote` (existing MongoDB)

### 3. Usage

#### Option A: Local Mode (Recommended for Testing)

```bash
# Set local mode in .env file
MONGO_MODE=local

# Generate test data and run analysis
python seed_data.py
python mongo-optimiser-agent.py
```

This automatically:
- Starts MongoDB 4.4 Docker container with profiling enabled
- Creates realistic test data (users, orders, products)
- Generates slow queries for analysis

#### Option B: Remote Mode (Production)

```bash
# Configure remote MongoDB in .env file
MONGO_MODE=remote
MONGO_URI=mongodb://your-host:27017/
MONGO_DB_NAME=your_database
MONGO_USERNAME=your_username  # optional
MONGO_PASSWORD=your_password  # optional

# Run analysis on existing data
python mongo-optimiser-agent.py
```

## ⚙️ Configuration Reference

### Environment Variables (.env file)

```bash
# MongoDB Configuration
MONGO_MODE=local                    # 'local' or 'remote'
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=testdb
MONGO_USERNAME=                     # Optional for remote auth
MONGO_PASSWORD=                     # Optional for remote auth
MONGO_AUTH_DB=admin                 # Optional for remote auth

# OpenRouter API Configuration
OPENROUTER_API_KEY=your_api_key_here
LLM_MODEL=mistralai/mistral-7b-instruct
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions

# Analysis Configuration
MIN_DURATION_MS=100                 # Minimum query duration to analyze
MAX_QUERIES_TO_ANALYZE=10           # Limit number of queries (0 = no limit)

# Local Mode Configuration
MONGO_CONTAINER_NAME=mongo-optimizer
MONGO_DOCKER_IMAGE=mongo:4.4
```

### Remote MongoDB Examples

```bash
# Standard remote connection
MONGO_MODE=remote
MONGO_URI=mongodb://192.168.1.100:27017/
MONGO_DB_NAME=production_db

# With authentication
MONGO_MODE=remote
MONGO_URI=mongodb://192.168.1.100:27017/
MONGO_DB_NAME=production_db
MONGO_USERNAME=admin
MONGO_PASSWORD=secret123
MONGO_AUTH_DB=admin

# MongoDB Atlas
MONGO_MODE=remote
MONGO_URI=mongodb+srv://cluster0.abcde.mongodb.net/
MONGO_DB_NAME=production_db
MONGO_USERNAME=your_username
MONGO_PASSWORD=your_password

# Replica Set
MONGO_MODE=remote
MONGO_URI=mongodb://host1:27017,host2:27017,host3:27017/database?replicaSet=myReplicaSet
MONGO_DB_NAME=production_db
```

## 📊 Example Output

```
🚀 MongoDB Query Optimizer
==================================================
✅ Loaded configuration from /path/to/.env
🐳 Local mode: Managing MongoDB Docker container...
✅ MongoDB container started successfully
📊 Profiling enabled: level 2, slowms 0
🔗 Connecting to MongoDB (local mode)...
✅ Successfully connected to MongoDB
🗄️  Targeting database: 'testdb'

🔍 Extracting slow queries (min duration: 100ms)...
🔗 Grouping similar queries to optimize API usage...
📊 Found 23 total queries, grouped into 18 unique patterns
   📋 Pattern 10922abc... has 4 similar queries (analyzing slowest: 5ms)
   📋 Pattern 08b12aac... has 3 similar queries (analyzing slowest: 2ms)
📊 Analyzing top 3 representative queries out of 18

🔄 Starting analysis...

=============== Query Pattern 1/3 ===============
🔗 Represents 4 similar queries (avg: 1.8ms, max: 5ms)
📋 Collection: users
⏱️  Duration: 245ms
🔧 Operation: query
📋 Schema cache MISS for users - computing...
🗂️  Indexes cache MISS for users - retrieving...
🤖 Generating AI recommendations...

💡 Optimization Recommendations:
==================================================
1. **Index Recommendations:**
   - Create compound index: db.users.createIndex({age: 1, status: 1})
   - This will optimize the age range filter and status matching

2. **Query Rewrites:**
   - Add projection to limit returned fields
   - Consider using aggregation pipeline for complex operations

3. **Performance Impact:**
   - Expected improvement: 85-95% faster execution
   - Estimated new duration: 12-37ms

4. **Data Model Advice:**
   - Consider denormalizing frequently accessed nested fields
==================================================

=============== Query 2/10 ===============
📋 Collection: orders
⏱️  Duration: 189ms
🔧 Operation: query
📋 Schema cache HIT for orders
🗂️  Indexes cache HIT for orders
🤖 Generating AI recommendations...
...

📊 Analysis Complete!
📊 Cache Stats: 6 entries, 3 collections cached
🔌 Disconnected from MongoDB
✅ MongoDB Query Optimizer finished
```

## 🔧 Understanding AI Recommendations

The optimizer provides four types of recommendations:

### 1. Index Recommendations
- **Single Field Indexes**: `db.collection.createIndex({field: 1})`
- **Compound Indexes**: `db.collection.createIndex({field1: 1, field2: -1})`
- **Text Indexes**: For text search optimization
- **Sparse Indexes**: For fields with many null values

### 2. Query Rewrites
- **Projection**: Limit returned fields to reduce network transfer
- **Aggregation Pipelines**: More efficient than multiple find operations
- **Limit/Skip Optimization**: Avoid large skip operations
- **Sort Optimization**: Ensure sorts can use indexes

### 3. Data Model Advice
- **Denormalization**: Embed frequently accessed data
- **Schema Design**: Optimize field types and structure
- **Array Optimization**: Efficient array query patterns
- **Nested Field Access**: Index nested fields when needed

### 4. Performance Tips
- **Connection Optimization**: Connection pooling and timeouts
- **Batch Operations**: Use bulk operations for multiple writes
- **Memory Management**: Working set size considerations
- **Monitoring**: Use explain() and profiling tools

## 🛠️ Production Setup

### Enable Profiling on Existing MongoDB

```javascript
// For development (captures all operations)
db.setProfilingLevel(2, { slowms: 100 })

// For production (captures only slow operations)
db.setProfilingLevel(1, { slowms: 1000, sampleRate: 0.1 })

// Check profiling status
db.getProfilingStatus()
```

### Automated Analysis with Cron

```bash
# Add to crontab for daily analysis
0 2 * * * cd /path/to/mongo-query-optimiser && source venv/bin/activate && python mongo-optimiser-agent.py >> /var/log/mongo-optimizer.log 2>&1
```

## 🔍 Troubleshooting

### Common Issues

#### Configuration Problems
```bash
# Check .env file exists and is readable
ls -la .env
cat .env

# Verify environment variables are loaded
python -c "from mongo_optimiser.config import *; print(f'Mode: {MONGO_MODE}, DB: {MONGO_DB_NAME}')"
```

#### MongoDB Connection Issues
```bash
# Local mode - check Docker
docker ps | grep mongo-optimizer
docker logs mongo-optimizer

# Remote mode - test connection
python -c "from pymongo import MongoClient; print(MongoClient('your_uri').admin.command('ping'))"
```

#### No Slow Queries Found
```bash
# Check profiling status
mongo your_database --eval "db.getProfilingStatus()"

# Enable profiling
mongo your_database --eval "db.setProfilingLevel(2, {slowms: 0})"

# Generate test data
python seed_data.py
```

#### OpenRouter API Issues
- Verify API key at [openrouter.ai](https://openrouter.ai/)
- Check account credits and rate limits
- Test with a simple request:
```python
import requests
headers = {"Authorization": "Bearer your_api_key"}
response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)
print(response.status_code)
```

#### Docker Issues
```bash
# Check Docker daemon
docker version

# Check container logs
docker logs mongo-optimizer

# Restart container
docker restart mongo-optimizer

# Clean up and recreate
docker rm -f mongo-optimizer
python seed_data.py  # Will recreate container
```

## 📁 Project Structure

```
mongo-query-optimiser/
├── mongo_optimiser/           # Main package
│   ├── __init__.py
│   ├── config.py             # Configuration management with .env support
│   ├── db_utils.py           # MongoDB utilities with caching
│   ├── docker_utils.py       # Docker container management
│   ├── llm_utils.py          # OpenRouter LLM integration
│   └── main.py               # Core optimization logic
├── .env.example              # Configuration template
├── mongo-optimiser-agent.py  # Main entry point
├── seed_data.py              # Enhanced database seeding
├── requirements.txt          # Python dependencies
└── README.md                 # This documentation
```

## 🚀 Performance Features

- **Smart Query Grouping**: Groups similar queries to reduce API calls by up to 90%
- **Metadata Caching**: Avoids redundant schema/index computations
- **Configurable Limits**: Control analysis scope with `MAX_QUERIES_TO_ANALYZE`
- **Efficient Profiling**: Smart query extraction with proper filtering
- **Batch Processing**: Optimized database operations
- **Progress Tracking**: Clear feedback during analysis

### Query Grouping Benefits

The tool automatically identifies and groups structurally similar queries:

- **Cost Reduction**: Significantly fewer API calls to LLM services
- **Faster Analysis**: Less time waiting for API responses
- **Better Insights**: Focus on unique query patterns rather than duplicates
- **Impact Awareness**: Clear indication of how many queries each optimization affects

For detailed information about query grouping, see [QUERY_GROUPING.md](QUERY_GROUPING.md).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Update documentation if needed
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: This README and inline code comments
- **API Documentation**: [OpenRouter API Docs](https://openrouter.ai/docs)
- **MongoDB Profiling**: [MongoDB Profiling Guide](https://docs.mongodb.com/manual/tutorial/manage-the-database-profiler/)

---

**Happy Optimizing! 🚀**
