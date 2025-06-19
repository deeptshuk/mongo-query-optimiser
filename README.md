# MongoDB Query Optimizer

An intelligent MongoDB performance analysis tool that identifies slow queries and provides AI-powered optimization recommendations. This tool analyzes queries from MongoDB's `system.profile` collection and uses Large Language Models (LLMs) to suggest actionable performance improvements.

## 🚀 Features

- **Automated Query Analysis**: Extracts and analyzes slow queries from MongoDB profiling data
- **AI-Powered Recommendations**: Uses OpenRouter LLM APIs to generate intelligent optimization suggestions
- **Collection Metadata Analysis**: Examines schemas, indexes, and execution plans
- **Flexible Deployment**: Supports both Docker and manual installation
- **Production Ready**: Compatible with MongoDB 3.x, 4.x, and 7.x
- **Mock Testing**: Includes local LLM stub for testing without API costs

## 📋 Prerequisites

- **Python**: 3.8+ (tested with 3.11 and 3.12)
- **MongoDB**: 3.6+ (tested with 3.x, 4.4, and 7.x)
- **Docker** (optional, for containerized setup)
- **OpenRouter API Key** (for production LLM analysis)

## 🐍 Virtual Environment Setup

**⚠️ Important**: Always use a virtual environment for Python development to avoid dependency conflicts and maintain project isolation.

### What is a Virtual Environment?

A virtual environment is an isolated Python environment that allows you to:
- Install packages specific to your project without affecting your system Python
- Avoid conflicts between different projects' dependencies
- Ensure consistent package versions across different machines
- Easily reproduce your development environment

### Creating and Managing Virtual Environments

#### Option 1: Using `venv` (Built-in, Recommended)

**Linux/macOS:**
```bash
# Navigate to your project directory
cd mongo-query-optimiser

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
which python
# Should output: /path/to/mongo-query-optimiser/venv/bin/python

# Install project dependencies
pip install -r requirements.txt

# When done working, deactivate the environment
deactivate
```

**Windows:**
```cmd
# Navigate to your project directory
cd mongo-query-optimiser

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
where python
# Should output: C:\path\to\mongo-query-optimiser\venv\Scripts\python.exe

# Install project dependencies
pip install -r requirements.txt

# When done working, deactivate the environment
deactivate
```

#### Option 2: Using `virtualenv` (Third-party)

If you prefer `virtualenv` or need Python 2.7 support:

```bash
# Install virtualenv (if not already installed)
pip install virtualenv

# Create virtual environment
virtualenv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Virtual Environment Best Practices

1. **Always activate before working**:
   ```bash
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Verify you're in the virtual environment**:
   - Your prompt should show `(venv)` prefix
   - `which python` should point to the venv directory

3. **Keep requirements.txt updated**:
   ```bash
   # After installing new packages
   pip freeze > requirements.txt
   ```

4. **Never commit the virtual environment**:
   - The `venv/` directory is already in `.gitignore`
   - Virtual environments contain system-specific paths and binaries

### Troubleshooting Virtual Environments

#### Issue: "Command not found" errors
**Solution**: Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

#### Issue: "Permission denied" on Windows
**Solution**: Enable script execution in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Issue: Python points to system Python
**Solution**:
1. Deactivate and reactivate the virtual environment
2. Verify with `which python` (Linux/macOS) or `where python` (Windows)

#### Issue: Packages not found after installation
**Solution**:
1. Ensure virtual environment is activated
2. Reinstall packages: `pip install -r requirements.txt`

#### Issue: Different Python version than expected
**Solution**: Create virtual environment with specific Python version:
```bash
# Use specific Python version
python3.11 -m venv venv
# or
virtualenv -p python3.11 venv
```

### Verification Steps

After setting up your virtual environment, verify everything is working:

#### Quick Manual Verification
```bash
# 1. Activate virtual environment
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 2. Check Python location
which python  # Should point to venv directory

# 3. Check installed packages
pip list

# 4. Verify required packages are installed
python -c "import pymongo, requests; print('Dependencies OK')"

# 5. Test MongoDB connection (if MongoDB is running)
python -c "from pymongo import MongoClient; print('MongoDB connection test:', MongoClient().admin.command('ping'))"
```

#### Automated Verification Script
For a comprehensive environment check, use the included verification script:

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Run the verification script
python verify_setup.py
```

This script will check:
- ✅ Virtual environment activation
- ✅ Python version compatibility
- ✅ Required package installation
- ✅ Project file structure
- ✅ Git repository status
- ✅ Environment variables

The script provides detailed feedback and suggestions for fixing any issues found.

## 🛠️ Installation & Setup

### Option 1: Quick Start with Docker Compose (Recommended for Testing)

This method sets up everything automatically with MongoDB 4.4, sample data, and a mock LLM service:

```bash
# Clone the repository
git clone <repository-url>
cd mongo-query-optimiser

# Start the complete environment
docker compose up --build
```

This will:
- Start MongoDB 4.4 with profiling enabled
- Seed the database with sample data and slow queries
- Launch a mock LLM service
- Run the optimizer and display results

### Option 2: Manual Installation (Recommended for Production)

#### Step 1: Set Up Virtual Environment and Install Dependencies

**⚠️ Critical**: Always create a virtual environment before installing dependencies!

```bash
# Navigate to project directory
cd mongo-query-optimiser

# Create virtual environment (choose one method)
python3 -m venv venv          # Linux/macOS
# python -m venv venv         # Windows

# Activate virtual environment
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Verify virtual environment is active
# You should see (venv) in your prompt
which python                  # Linux/macOS - should point to venv/bin/python
# where python                # Windows - should point to venv\Scripts\python.exe

# Upgrade pip to latest version
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pymongo, requests; print('✅ All dependencies installed successfully!')"
```

**Important Notes**:
- The virtual environment directory (`venv/`) is excluded from version control
- Each developer should create their own virtual environment locally
- Always activate the virtual environment before running any Python commands

#### Step 2: Set Up MongoDB

**Option A: Using Docker**
```bash
# MongoDB 4.4 (recommended for compatibility)
docker run -d --name mongodb-optimizer \
  -p 27017:27017 \
  mongo:4.4 \
  mongod --profile 2 --slowms 100

# MongoDB 7.x (if you prefer latest)
docker run -d --name mongodb-optimizer \
  -p 27017:27017 \
  mongo:7 \
  mongod --profile 2 --slowms 100
```

**Option B: Using Existing MongoDB Instance**
```javascript
// Connect to your MongoDB instance and enable profiling
use your_database_name
db.setProfilingLevel(2, { slowms: 100 })

// Verify profiling is enabled
db.getProfilingStatus()
```

#### Step 3: Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB_NAME="your_database_name"
export OPENROUTER_API_KEY="your_openrouter_api_key"

# Optional
export LLM_MODEL="mistralai/mistral-7b-instruct"  # Default model
export OPENROUTER_API_URL="https://openrouter.ai/api/v1/chat/completions"  # Default URL
```

#### Step 4: Get OpenRouter API Key

1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up for an account
3. Generate an API key
4. Set the `OPENROUTER_API_KEY` environment variable

## 🎯 Usage

### Basic Usage

Once your environment is set up, run the optimizer:

```bash
# ALWAYS activate virtual environment first (if using manual setup)
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Verify you're in the virtual environment (should see (venv) in prompt)
which python                  # Should point to venv directory

# Run the optimizer
python mongo-optimiser-agent.py
```

**💡 Pro Tip**: If you see import errors, make sure your virtual environment is activated!

### Using with Your Own Database

#### Step 1: Enable Profiling on Your Database

Connect to your MongoDB instance and enable profiling:

```javascript
// Connect to your database
use your_production_database

// Enable profiling for slow operations (>100ms)
db.setProfilingLevel(2, { slowms: 100 })

// For more selective profiling (recommended for production):
// Profile only operations slower than 1000ms
db.setProfilingLevel(1, { slowms: 1000 })

// Verify profiling status
db.getProfilingStatus()
```

#### Step 2: Let Your Application Generate Some Load

Allow your application to run for a while to generate profiling data. The optimizer needs existing slow queries in the `system.profile` collection to analyze.

#### Step 3: Run the Optimizer

```bash
# Set your database connection details
export MONGO_URI="mongodb://your-host:27017/"
export MONGO_DB_NAME="your_production_database"
export OPENROUTER_API_KEY="your_api_key"

# Run the optimizer
python mongo-optimiser-agent.py
```

### Advanced Usage

#### Custom Minimum Duration Threshold

To analyze queries with different duration thresholds, you can modify the `main.py` file or create a custom script:

```python
from mongo_optimiser.main import *
from mongo_optimiser.db_utils import get_slow_queries

# Analyze queries slower than 50ms instead of default 100ms
slow_queries = get_slow_queries(db, min_duration_ms=50)
```

#### Using with Authentication

For MongoDB instances with authentication:

```bash
export MONGO_URI="mongodb://username:password@host:27017/database?authSource=admin"
```

#### Using with MongoDB Atlas

```bash
export MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/database"
```

#### Using with Replica Sets

```bash
export MONGO_URI="mongodb://host1:27017,host2:27017,host3:27017/database?replicaSet=myReplicaSet"
```

## 🌱 Database Seeding for Testing

The project includes a seeding script to populate your database with sample data for testing purposes.

### Using the Seed Script

```bash
# ALWAYS activate virtual environment first
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Verify virtual environment is active
which python                  # Should point to venv directory

# Set environment variables
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB_NAME="testdb"

# Run the seed script
python seed_data.py
```

### What the Seed Script Does

The `seed_data.py` script:

1. **Creates Sample Data**: Inserts 1000 user documents with realistic data structure
2. **Generates Slow Queries**: Executes various query patterns to populate `system.profile`
3. **Creates Different Query Types**:
   - Find queries with different filter patterns
   - Aggregation pipelines
   - Update operations
   - Sort operations without proper indexes

### Sample Data Structure

The seeded data includes user documents with the following structure:

```javascript
{
  "_id": ObjectId("..."),
  "name": "John Doe",
  "email": "john.doe@example.com",
  "age": 25,
  "city": "New York",
  "country": "USA",
  "created_at": ISODate("2024-01-15T10:30:00Z"),
  "last_login": ISODate("2024-01-20T14:22:00Z"),
  "preferences": {
    "theme": "dark",
    "notifications": true
  },
  "tags": ["premium", "active"]
}
```

### Customizing Seed Data

You can modify `seed_data.py` to:
- Change the number of documents created
- Modify the data structure to match your use case
- Add different types of queries to generate specific slow query patterns
- Create additional collections for more complex scenarios

## 🧪 Testing with Mock LLM Service

For testing without using real API credits, the project includes a FastAPI-based mock LLM service.

### Starting the Mock LLM Service

```bash
# ALWAYS activate virtual environment first
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Verify virtual environment is active
which python                  # Should point to venv directory

# Start the mock service
cd llm_stub
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

### Using the Mock Service

```bash
# Set environment variables to use mock service
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB_NAME="testdb"
export OPENROUTER_API_KEY="dummy_key"
export OPENROUTER_API_URL="http://localhost:8080/api/v1/chat/completions"

# Run the optimizer
python mongo-optimiser-agent.py
```

The mock service returns realistic optimization suggestions without making real API calls.

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_URI` | Yes | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGO_DB_NAME` | Yes | - | Target database name |
| `OPENROUTER_API_KEY` | Yes* | - | OpenRouter API key (*not required for mock service) |
| `LLM_MODEL` | No | `mistralai/mistral-7b-instruct` | LLM model to use |
| `OPENROUTER_API_URL` | No | `https://openrouter.ai/api/v1/chat/completions` | LLM API endpoint |

### MongoDB Profiling Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `0` | Profiling disabled | Production (no performance impact) |
| `1` | Profile slow operations only | Production (recommended) |
| `2` | Profile all operations | Development/Testing only |

### Recommended Production Settings

```javascript
// For production databases, use level 1 with higher slowms threshold
db.setProfilingLevel(1, {
  slowms: 1000,  // Profile operations slower than 1 second
  sampleRate: 0.1  // Sample 10% of slow operations (MongoDB 4.4+)
})
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Virtual Environment Issues

**Issue**: `ModuleNotFoundError` or `ImportError` when running scripts
**Cause**: Virtual environment not activated or packages not installed in virtual environment.

**Solutions**:
```bash
# Check if virtual environment is activated
echo $VIRTUAL_ENV  # Should show path to venv directory

# If not activated, activate it
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Verify Python location
which python                  # Should point to venv/bin/python

# Reinstall dependencies if needed
pip install -r requirements.txt

# Test imports
python -c "import pymongo, requests; print('✅ Dependencies OK')"
```

**Issue**: `pip: command not found` or packages install to system Python
**Cause**: Virtual environment not properly activated.

**Solutions**:
```bash
# Deactivate current environment
deactivate

# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv

# Activate and install
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Issue**: Permission errors when creating virtual environment
**Cause**: Insufficient permissions or conflicting Python installations.

**Solutions**:
```bash
# Linux/macOS: Check Python installation
which python3
python3 --version

# Windows: Run as administrator or check execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Alternative: Use user directory
python3 -m venv ~/.virtualenvs/mongo-optimizer
source ~/.virtualenvs/mongo-optimizer/bin/activate
```

#### 2. "No slow queries found"

**Cause**: No queries in `system.profile` collection or threshold too high.

**Solutions**:
- Ensure profiling is enabled: `db.getProfilingStatus()`
- Lower the `slowms` threshold: `db.setProfilingLevel(2, { slowms: 0 })`
- Generate some database activity
- Check if `system.profile` collection exists: `db.system.profile.count()`

#### 3. "Connection refused" or MongoDB connection errors

**Cause**: MongoDB not running or incorrect connection string.

**Solutions**:
- Verify MongoDB is running: `docker ps` or `systemctl status mongod`
- Check connection string format
- Verify network connectivity and firewall settings
- For Docker: ensure port 27017 is exposed

#### 4. "OpenRouter API errors"

**Cause**: Invalid API key or network issues.

**Solutions**:
- Verify API key is correct
- Check OpenRouter account credits/limits
- Use mock service for testing: set `OPENROUTER_API_URL=http://localhost:8080/api/v1/chat/completions`
- Check network connectivity to OpenRouter

#### 5. "Permission denied" errors

**Cause**: Insufficient MongoDB permissions.

**Solutions**:
- Ensure user has read access to target database
- Ensure user has read access to `system.profile` collection
- For profiling setup, user needs `dbAdmin` role

### Debug Mode

To enable verbose logging, modify the script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Checking System Profile Collection

```javascript
// Check if profiling data exists
db.system.profile.count()

// View recent profile entries
db.system.profile.find().sort({ts: -1}).limit(5).pretty()

// Check profiling status
db.getProfilingStatus()
```

## 📁 Project Structure

```
mongo-query-optimiser/
├── mongo_optimiser/           # Main package
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   ├── db_utils.py           # MongoDB utilities
│   ├── llm_utils.py          # LLM integration
│   └── main.py               # Core optimization logic
├── llm_stub/                 # Mock LLM service
│   ├── Dockerfile
│   ├── main.py               # FastAPI mock service
│   └── requirements.txt
├── mongo-optimiser-agent.py  # Main entry point
├── seed_data.py              # Database seeding script
├── demo_optimizer.py         # Enhanced demo script
├── verify_setup.py           # Environment verification script
├── setup_production_db.py    # Production database setup wizard
├── docker-compose.yml        # Complete Docker setup
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore file (includes venv/)
└── README.md                 # This file
```

**Important**: The `venv/` directory (virtual environment) is **not** included in version control and should be created locally by each developer.

## 🎯 Example Output

When the optimizer finds slow queries, it provides detailed analysis:

```
🚀 Starting MongoDB Query Optimizer...
✅ Connected to database: 'production_db'

🔍 Extracting slow queries from 'production_db' (min duration: 100ms)
📊 Found 15 queries in profile collection

=== Analyzing Query 1 ===
📋 Collection: users
⏱️  Duration: 1247ms
🔧 Operation: find

📈 Gathering collection metadata...
📊 Schema sample: {'_id': 1, 'email': 1, 'created_at': 1, 'status': 1}
🗂️  Indexes: ['_id_', 'email_1']

💡 Optimization Recommendations:
=====================================
1. **Missing Index**: Create a compound index on {status: 1, created_at: 1}
   to optimize the query filter and sort operations.

   Command: db.users.createIndex({status: 1, created_at: 1})

2. **Query Optimization**: Consider adding a limit() clause if you don't
   need all matching documents.

3. **Schema Optimization**: The current query scans 45,000 documents.
   Consider adding selectivity to your query filters.

Expected Performance Improvement: 85-95% reduction in query time
=====================================
```

## 🚀 Production Deployment

### Best Practices

1. **Profiling Configuration**:
   ```javascript
   // Use level 1 in production with appropriate thresholds
   db.setProfilingLevel(1, { slowms: 1000, sampleRate: 0.1 })
   ```

2. **Resource Management**:
   - Monitor `system.profile` collection size
   - Set up log rotation for profile data
   - Consider running optimizer during off-peak hours

3. **Security**:
   - Use read-only MongoDB credentials
   - Secure OpenRouter API keys
   - Run in isolated network environment

4. **Automation**:
   ```bash
   # Example cron job (daily analysis)
   0 2 * * * /path/to/venv/bin/python /path/to/mongo-optimiser-agent.py >> /var/log/mongo-optimizer.log 2>&1
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check this README and inline code comments
- **Community**: Join discussions in GitHub Discussions

## 🔗 Related Resources

- [MongoDB Profiling Documentation](https://docs.mongodb.com/manual/tutorial/manage-the-database-profiler/)
- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [MongoDB Performance Best Practices](https://docs.mongodb.com/manual/administration/analyzing-mongodb-performance/)

---

**Happy Optimizing! 🚀**
