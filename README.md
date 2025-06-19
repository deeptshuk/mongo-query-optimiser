# MongoDB Query Optimizer

An intelligent MongoDB performance analysis tool that identifies slow queries and provides AI-powered optimization recommendations.

## Features

- Analyzes slow queries from MongoDB's `system.profile` collection
- Uses OpenRouter LLM APIs to generate optimization suggestions
- Examines collection schemas, indexes, and execution plans
- Supports Docker and manual installation
- Compatible with MongoDB 3.x, 4.x, and 7.x
- Includes mock LLM service for testing

## Prerequisites

- Python 3.8+
- MongoDB 3.6+
- OpenRouter API Key (for production use)

## Quick Start

### Option 1: Docker (Recommended for Testing)

```bash
git clone <repository-url>
cd mongo-query-optimiser
docker compose up --build
```

This starts MongoDB 4.4, seeds test data, and runs the optimizer with a mock LLM service.

### Option 2: Manual Setup

#### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 2. Start MongoDB with Profiling

```bash
# Using Docker
docker run -d --name mongodb-optimizer \
  -p 27017:27017 \
  mongo:4.4 \
  mongod --profile 2 --slowms 100
```

Or enable profiling on existing MongoDB:
```javascript
use your_database_name
db.setProfilingLevel(2, { slowms: 100 })
```

#### 3. Configure Environment

```bash
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB_NAME="testdb"
export OPENROUTER_API_KEY="your_api_key"
```

Get your OpenRouter API key from [openrouter.ai](https://openrouter.ai/)

## Usage

### Basic Usage

```bash
# Activate virtual environment (if using manual setup)
source venv/bin/activate

# Run the optimizer
python mongo-optimiser-agent.py
```

### Generate Test Data

```bash
# Seed database with sample data and slow queries
python seed_data.py
```

### Using Mock LLM Service (No API Costs)

```bash
# Start mock service
cd llm_stub
python -m uvicorn main:app --host 0.0.0.0 --port 8080

# In another terminal, set environment to use mock service
export OPENROUTER_API_URL="http://localhost:8080/api/v1/chat/completions"
export OPENROUTER_API_KEY="dummy_key"
python mongo-optimiser-agent.py
```

## Example Output

```
Starting MongoDB Query Optimizer...

Targeting database: 'testdb'

--- Extracting slow queries from 'testdb' (min duration: 100ms) ---
Found 3 slow queries. Analyzing each...

========== Analyzing Slow Query 1/3 ==========
Collection: users

--- Optimization Recommendations ---
Based on the slow query analysis, here are the recommended optimizations:

1. **Create Index**: Add an index on the 'age' field to improve query performance
   Command: db.users.createIndex({age: 1})

2. **Query Optimization**: Consider using projection to limit returned fields

3. **Collection Stats**: 1000 documents scanned, 45 returned

Expected improvement: 80-90% faster query execution
========== End of Query 1 Analysis ==========
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_URI` | Yes | `mongodb://localhost:27017/` | MongoDB connection string |
| `MONGO_DB_NAME` | Yes | `test` | Target database name |
| `OPENROUTER_API_KEY` | Yes* | - | OpenRouter API key (*not required for mock service) |
| `LLM_MODEL` | No | `mistralai/mistral-7b-instruct` | LLM model to use |
| `OPENROUTER_API_URL` | No | `https://openrouter.ai/api/v1/chat/completions` | LLM API endpoint |

### MongoDB Profiling

```javascript
// Enable profiling for all operations (development)
db.setProfilingLevel(2, { slowms: 100 })

// Enable profiling for slow operations only (production)
db.setProfilingLevel(1, { slowms: 1000 })
```

## Troubleshooting

### Common Issues

**"No slow queries found"**
- Enable profiling: `db.setProfilingLevel(2, { slowms: 100 })`
- Generate database activity or run `python seed_data.py`

**"Connection refused"**
- Ensure MongoDB is running: `docker ps`
- Check connection string in `MONGO_URI`

**"Import errors"**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**"OpenRouter API errors"**
- Verify API key is correct
- Use mock service for testing (see Usage section)

## Project Structure

```
mongo-query-optimiser/
├── mongo_optimiser/           # Main package
│   ├── config.py             # Configuration
│   ├── db_utils.py           # MongoDB utilities
│   ├── llm_utils.py          # LLM integration
│   └── main.py               # Core logic
├── llm_stub/                 # Mock LLM service
│   └── main.py               # FastAPI mock service
├── mongo-optimiser-agent.py  # Main entry point
├── seed_data.py              # Database seeding
├── requirements.txt          # Dependencies
└── README.md
```

## License

MIT License
