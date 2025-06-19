import os
import time
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
DB_NAME = os.getenv("MONGO_DB_NAME", "testdb")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ensure profiling is enabled at level 2 with slowms 0
try:
    db.set_profiling_level(2, slowms=0)
except Exception:
    pass

coll = db.users
if coll.estimated_document_count() == 0:
    docs = [
        {"name": f"user{i}", "age": i % 50, "email": f"user{i}@example.com"}
        for i in range(1000)
    ]
    coll.insert_many(docs)

for _ in range(5):
    list(coll.find({"age": {"$gte": 10}}).sort("name"))
    time.sleep(0.1)

print("Seeded slow queries.")
