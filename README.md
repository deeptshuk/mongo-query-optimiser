# Mongo Query Optimiser

This tool analyses slow MongoDB queries using data from the `system.profile` collection and suggests optimisations with the help of a language model. The code has been modularised into a small package for easier reuse.

## Usage
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure MongoDB is running and profiling is enabled (`db.setProfilingLevel(2)`).
3. Set the following environment variables:
   - `MONGO_URI` – MongoDB connection URI (default: `mongodb://localhost:27017/`).
   - `MONGO_DB_NAME` – target database name.
   - `OPENROUTER_API_KEY` – API key for OpenRouter.
   - `LLM_MODEL` – optional model name on OpenRouter.
4. (Optional) set `OPENROUTER_API_URL` if using a custom endpoint.
5. Run the optimiser:
   ```bash
   python mongo-optimiser-agent.py
   ```

The output will include recommendations for each slow query found.

## Local Docker Test Setup

The repository includes a `docker-compose.yml` that starts a MongoDB instance with profiling enabled, seeds it with sample data and slow queries, launches a small FastAPI service that mocks the LLM API and finally runs the optimiser against this environment.

To try it locally:

```bash
docker compose up --build
```

The optimiser container will print optimisation suggestions in the logs based on the mocked LLM responses.
