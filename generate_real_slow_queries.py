#!/usr/bin/env python3
"""
Generate real slow queries for testing the optimizer
"""
import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongo_optimiser.config import MONGO_MODE, MONGO_DB_NAME, build_mongo_uri
from mongo_optimiser.docker_utils import start_mongodb_container, is_docker_available
from pymongo import MongoClient

def connect_to_mongodb() -> MongoClient:
    """Connect to MongoDB."""
    if MONGO_MODE == "local":
        if not is_docker_available():
            print("❌ Docker not available")
            sys.exit(1)
        if not start_mongodb_container():
            print("❌ Failed to start MongoDB container")
            sys.exit(1)
    
    uri = build_mongo_uri()
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    print(f"✅ Connected to MongoDB")
    return client

def generate_real_slow_queries(db):
    """Generate queries that will actually be slow and show up in profiling."""
    print("🐌 Generating REAL slow queries...")
    
    users_coll = db.users
    orders_coll = db.orders
    products_coll = db.products
    
    # 1. Large unindexed sort (should be slow)
    print("   1. Large unindexed sort on users by registration_date...")
    result = list(users_coll.find().sort("registration_date", -1).limit(100))
    print(f"      Found {len(result)} users")
    
    # 2. Complex aggregation with multiple stages
    print("   2. Complex aggregation on orders...")
    pipeline = [
        {"$match": {"status": {"$in": ["delivered", "shipped"]}}},
        {"$group": {
            "_id": "$user_id", 
            "total_spent": {"$sum": "$price"}, 
            "order_count": {"$sum": 1},
            "avg_order_value": {"$avg": "$price"}
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": 50}
    ]
    result = list(orders_coll.aggregate(pipeline))
    print(f"      Aggregated {len(result)} user spending records")
    
    # 3. Regex search on large text field
    print("   3. Regex search on product descriptions...")
    result = list(products_coll.find({
        "description": {"$regex": "product.*description", "$options": "i"}
    }).limit(20))
    print(f"      Found {len(result)} products matching regex")
    
    # 4. Range query without index
    print("   4. Date range query on orders...")
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=30)
    result = list(orders_coll.find({
        "order_date": {"$gte": cutoff_date}
    }).limit(100))
    print(f"      Found {len(result)} recent orders")
    
    # 5. Multi-field sort without compound index
    print("   5. Multi-field sort on users...")
    result = list(users_coll.find({
        "status": "active"
    }).sort([("age", 1), ("registration_date", -1)]).limit(50))
    print(f"      Found {len(result)} active users sorted by age and date")
    
    # 6. Large skip operation (very inefficient)
    print("   6. Large skip operation on orders...")
    result = list(orders_coll.find().skip(5000).limit(10))
    print(f"      Skipped 5000 and got {len(result)} orders")
    
    # 7. Array element query
    print("   7. Array element query on users...")
    result = list(users_coll.find({
        "tags": {"$in": ["premium", "vip"]}
    }).limit(100))
    print(f"      Found {len(result)} premium/vip users")
    
    # 8. Nested field query without index
    print("   8. Nested field query on user preferences...")
    result = list(users_coll.find({
        "preferences.theme": "dark",
        "preferences.notifications": True
    }).limit(50))
    print(f"      Found {len(result)} users with dark theme and notifications")
    
    # 9. Count operation on large collection
    print("   9. Count operation on orders...")
    count = orders_coll.count_documents({"status": {"$ne": "cancelled"}})
    print(f"      Counted {count} non-cancelled orders")
    
    # 10. Cross-collection lookup simulation
    print("   10. Cross-collection lookup simulation...")
    # Get orders and then lookup user details (inefficient way)
    orders = list(orders_coll.find({"status": "delivered"}).limit(100))
    user_ids = [order["user_id"] for order in orders]
    users = list(users_coll.find({"user_id": {"$in": user_ids}}))
    print(f"      Looked up {len(users)} users for {len(orders)} orders")
    
    print("✅ Generated 10 types of real slow operations")

def main():
    """Main function."""
    print("🐌 Generating Real Slow Queries for Testing")
    print("=" * 60)
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[MONGO_DB_NAME]
    
    try:
        # Clear existing profile data first (need to turn off profiling)
        try:
            db.command("profile", 0)  # Turn off profiling
            db.system.profile.drop()
            print("🗑️  Cleared existing profile data")
        except Exception as e:
            print(f"⚠️  Could not clear profile data: {e}")

        # Enable profiling with 0ms threshold to catch everything
        db.command("profile", 2, slowms=0)
        print("✅ Profiling enabled with 0ms threshold")
        
        # Generate slow queries
        generate_real_slow_queries(db)
        
        # Show profiling results
        profile_count = db.system.profile.count_documents({})
        print(f"\n📊 Profiling Results:")
        print(f"   Total profile entries: {profile_count}")
        
        # Show queries by duration
        slow_queries = list(db.system.profile.find({
            "op": {"$in": ["query", "command"]},
            "millis": {"$gte": 1}
        }).sort("millis", -1).limit(10))
        
        if slow_queries:
            print(f"   Top slow queries:")
            for i, query in enumerate(slow_queries, 1):
                op_type = query.get('op', 'unknown')
                duration = query.get('millis', 0)
                ns = query.get('ns', 'unknown')
                print(f"     {i}. {ns} ({op_type}) - {duration}ms")
        
        print(f"\n✅ Real slow queries generated successfully!")
        print(f"💡 Now run: python mongo-optimiser-agent.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()
