#!/usr/bin/env python3
"""
Enhanced seed data script for MongoDB Query Optimizer.
Creates realistic data and generates slow queries for testing.
"""
import os
import sys
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongo_optimiser.config import MONGO_MODE, MONGO_DB_NAME, build_mongo_uri
from mongo_optimiser.docker_utils import start_mongodb_container, is_docker_available

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
except ImportError:
    print("❌ pymongo not installed. Run: pip install pymongo")
    sys.exit(1)


def connect_to_mongodb() -> MongoClient:
    """Connect to MongoDB with automatic container management."""
    if MONGO_MODE == "local":
        print("🐳 Local mode: Starting MongoDB container...")
        if not is_docker_available():
            print("❌ Docker not available")
            sys.exit(1)
        if not start_mongodb_container():
            print("❌ Failed to start MongoDB container")
            sys.exit(1)

    uri = build_mongo_uri()
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        print(f"✅ Connected to MongoDB")
        return client
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)


def enable_profiling(db) -> None:
    """Enable MongoDB profiling to capture slow queries."""
    try:
        # Enable profiling for all operations with 0ms threshold
        result = db.command("profile", 2, slowms=0)
        print(f"✅ Profiling enabled: {result}")
    except Exception as e:
        print(f"⚠️  Could not enable profiling: {e}")


def create_users_data(db, count: int = 5000) -> None:
    """Create users collection with realistic data."""
    print(f"👥 Creating {count} users...")

    users_coll = db.users

    # Check if data already exists
    if users_coll.estimated_document_count() > 0:
        print(f"ℹ️  Users collection already has data, skipping creation")
        return

    # Generate realistic user data
    cities = ["New York", "London", "Tokyo", "Paris", "Sydney", "Toronto", "Berlin", "Mumbai", "São Paulo", "Cairo"]
    countries = ["USA", "UK", "Japan", "France", "Australia", "Canada", "Germany", "India", "Brazil", "Egypt"]
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "company.com", "university.edu"]

    users = []
    for i in range(count):
        city = random.choice(cities)
        country = random.choice(countries)
        domain = random.choice(domains)

        user = {
            "user_id": i + 1,
            "name": f"User {i+1}",
            "email": f"user{i+1}@{domain}",
            "age": random.randint(18, 80),
            "city": city,
            "country": country,
            "registration_date": datetime.now() - timedelta(days=random.randint(1, 1000)),
            "last_login": datetime.now() - timedelta(days=random.randint(0, 30)),
            "status": random.choice(["active", "inactive", "premium", "trial"]),
            "preferences": {
                "theme": random.choice(["light", "dark"]),
                "notifications": random.choice([True, False]),
                "language": random.choice(["en", "es", "fr", "de", "ja"])
            },
            "tags": random.sample(["premium", "active", "new", "verified", "vip"], random.randint(1, 3))
        }
        users.append(user)

    # Insert in batches
    batch_size = 1000
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        users_coll.insert_many(batch)
        print(f"   Inserted batch {i//batch_size + 1}/{(len(users) + batch_size - 1)//batch_size}")

    print(f"✅ Created {count} users")


def create_orders_data(db, count: int = 10000) -> None:
    """Create orders collection with realistic data."""
    print(f"🛒 Creating {count} orders...")

    orders_coll = db.orders

    if orders_coll.estimated_document_count() > 0:
        print(f"ℹ️  Orders collection already has data, skipping creation")
        return

    # Get user IDs for foreign key relationships
    users_coll = db.users
    user_count = users_coll.estimated_document_count()
    if user_count == 0:
        print("⚠️  No users found, creating orders without user references")
        user_ids = list(range(1, 1001))
    else:
        user_ids = [doc["user_id"] for doc in users_coll.find({}, {"user_id": 1}).limit(1000)]

    products = ["Laptop", "Phone", "Tablet", "Headphones", "Camera", "Watch", "Keyboard", "Mouse", "Monitor", "Speaker"]
    statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]

    orders = []
    for i in range(count):
        order = {
            "order_id": i + 1,
            "user_id": random.choice(user_ids),
            "product": random.choice(products),
            "quantity": random.randint(1, 5),
            "price": round(random.uniform(10.0, 1000.0), 2),
            "order_date": datetime.now() - timedelta(days=random.randint(0, 365)),
            "status": random.choice(statuses),
            "shipping_address": {
                "street": f"{random.randint(1, 999)} Main St",
                "city": f"City {random.randint(1, 100)}",
                "zipcode": f"{random.randint(10000, 99999)}"
            }
        }
        orders.append(order)

    # Insert in batches
    batch_size = 1000
    for i in range(0, len(orders), batch_size):
        batch = orders[i:i + batch_size]
        orders_coll.insert_many(batch)
        print(f"   Inserted batch {i//batch_size + 1}/{(len(orders) + batch_size - 1)//batch_size}")

    print(f"✅ Created {count} orders")


def create_products_data(db, count: int = 1000) -> None:
    """Create products collection with realistic data."""
    print(f"📦 Creating {count} products...")

    products_coll = db.products

    if products_coll.estimated_document_count() > 0:
        print(f"ℹ️  Products collection already has data, skipping creation")
        return

    categories = ["Electronics", "Clothing", "Books", "Home", "Sports", "Beauty", "Toys", "Automotive"]
    brands = ["BrandA", "BrandB", "BrandC", "BrandD", "BrandE"]

    products = []
    for i in range(count):
        product = {
            "product_id": i + 1,
            "name": f"Product {i+1}",
            "category": random.choice(categories),
            "brand": random.choice(brands),
            "price": round(random.uniform(5.0, 500.0), 2),
            "description": f"Description for product {i+1} " * random.randint(5, 20),  # Variable length
            "in_stock": random.choice([True, False]),
            "stock_quantity": random.randint(0, 1000),
            "rating": round(random.uniform(1.0, 5.0), 1),
            "reviews_count": random.randint(0, 1000),
            "created_date": datetime.now() - timedelta(days=random.randint(1, 1000)),
            "tags": random.sample(["new", "popular", "sale", "featured", "limited"], random.randint(0, 3))
        }
        products.append(product)

    products_coll.insert_many(products)
    print(f"✅ Created {count} products")


def generate_slow_queries(db) -> None:
    """Generate various slow queries to populate the profiler."""
    print(f"🐌 Generating slow queries...")

    users_coll = db.users
    orders_coll = db.orders
    products_coll = db.products

    slow_operations = []

    # 1. Unindexed sort on large collection
    print("   1. Large unindexed sort on users...")
    list(users_coll.find().sort("registration_date", -1).limit(100))
    slow_operations.append("Unindexed sort on registration_date")

    # 2. Complex aggregation without proper indexes
    print("   2. Complex aggregation on orders...")
    list(orders_coll.aggregate([
        {"$match": {"status": "delivered"}},
        {"$group": {"_id": "$user_id", "total_spent": {"$sum": "$price"}, "order_count": {"$sum": 1}}},
        {"$sort": {"total_spent": -1}},
        {"$limit": 50}
    ]))
    slow_operations.append("Complex aggregation on orders")

    # 3. Text search without text index
    print("   3. Regex search on product descriptions...")
    list(products_coll.find({"description": {"$regex": "product.*description", "$options": "i"}}).limit(10))
    slow_operations.append("Regex search on descriptions")

    # 4. Cross-collection lookup simulation (slow joins)
    print("   4. Manual join simulation...")
    user_orders = {}
    for order in orders_coll.find({"status": "delivered"}).limit(1000):
        user_id = order["user_id"]
        if user_id not in user_orders:
            user_orders[user_id] = []
        user_orders[user_id].append(order)
    slow_operations.append("Manual join simulation")

    # 5. Range query without index
    print("   5. Date range query without index...")
    cutoff_date = datetime.now() - timedelta(days=30)
    list(users_coll.find({"last_login": {"$gte": cutoff_date}}).limit(100))
    slow_operations.append("Date range query on last_login")

    # 6. Multiple field sort without compound index
    print("   6. Multi-field sort without compound index...")
    list(users_coll.find({"status": "active"}).sort([("age", 1), ("registration_date", -1)]).limit(50))
    slow_operations.append("Multi-field sort on age and registration_date")

    # 7. Large skip operation
    print("   7. Large skip operation...")
    list(orders_coll.find().skip(5000).limit(10))
    slow_operations.append("Large skip operation")

    # 8. Inefficient array query
    print("   8. Array element query...")
    list(users_coll.find({"tags": {"$in": ["premium", "vip"]}}).limit(100))
    slow_operations.append("Array element query on tags")

    # 9. Count operation on large collection
    print("   9. Count operation...")
    count = orders_coll.count_documents({"status": {"$ne": "cancelled"}})
    slow_operations.append(f"Count operation (result: {count})")

    # 10. Nested field query without index
    print("   10. Nested field query...")
    list(users_coll.find({"preferences.theme": "dark", "preferences.notifications": True}).limit(50))
    slow_operations.append("Nested field query on preferences")

    print(f"✅ Generated {len(slow_operations)} types of slow operations")
    for i, op in enumerate(slow_operations, 1):
        print(f"   {i}. {op}")


def main():
    """Main function to seed the database."""
    print("🌱 MongoDB Query Optimizer - Enhanced Seed Data")
    print("=" * 60)

    # Connect to MongoDB
    client = connect_to_mongodb()
    db = client[MONGO_DB_NAME]

    try:
        # Enable profiling
        enable_profiling(db)

        # Create collections with data
        create_users_data(db, count=5000)
        create_orders_data(db, count=10000)
        create_products_data(db, count=1000)

        # Generate slow queries
        generate_slow_queries(db)

        # Show profiling results
        profile_count = db.system.profile.count_documents({})
        print(f"\n📊 Profiling Results:")
        print(f"   Total profile entries: {profile_count}")

        # Show sample slow queries
        slow_queries = list(db.system.profile.find({"millis": {"$gte": 10}}).sort("millis", -1).limit(5))
        if slow_queries:
            print(f"   Sample slow queries:")
            for i, query in enumerate(slow_queries, 1):
                print(f"     {i}. {query.get('ns', 'N/A')} - {query.get('millis', 0)}ms")

        print(f"\n✅ Database seeding completed successfully!")
        print(f"💡 Run the optimizer: python mongo-optimiser-agent.py")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    main()
