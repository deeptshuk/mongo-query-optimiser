# Mongo Query Optimiser

This tool analyses slow MongoDB queries using data from the `system.profile` collection and suggests optimisations with the help of a language model. The code has been modularised into a small package for easier reuse.

## Usage
1. Ensure MongoDB is running and profiling is enabled (`db.setProfilingLevel(2)`).
2. Set the following environment variables:
   - `MONGO_URI` – MongoDB connection URI (default: `mongodb://localhost:27017/`).
   - `MONGO_DB_NAME` – target database name.
   - `OPENROUTER_API_KEY` – API key for OpenRouter.
   - `LLM_MODEL` – optional model name on OpenRouter.
3. Run the optimiser:
   ```bash
   python mongo-optimiser-agent.py
   ```

The output will include recommendations for each slow query found.
