#!/usr/bin/env python3
"""
Production Database Setup Script for MongoDB Query Optimizer

This script helps you set up profiling on your existing production database
and provides guidance for safe usage.
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

def setup_production_profiling():
    """
    Interactive setup for production database profiling
    """
    print("🔧 MongoDB Query Optimizer - Production Database Setup")
    print("=" * 60)
    
    # Get connection details
    mongo_uri = input("Enter MongoDB URI (e.g., mongodb://localhost:27017/): ").strip()
    if not mongo_uri:
        mongo_uri = "mongodb://localhost:27017/"
    
    db_name = input("Enter database name: ").strip()
    if not db_name:
        print("❌ Database name is required!")
        return False
    
    try:
        # Connect to MongoDB
        print(f"\n🔌 Connecting to {mongo_uri}...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
        
        # Get database
        db = client.get_database(db_name)
        
        # Check current profiling status
        print(f"\n📊 Checking current profiling status for '{db_name}'...")
        current_status = db.command("profile", -1)
        print(f"Current profiling level: {current_status.get('was', 'unknown')}")
        print(f"Current slowms threshold: {current_status.get('slowms', 'unknown')}ms")
        
        # Recommend profiling settings
        print(f"\n💡 Recommended profiling settings for production:")
        print(f"   Level 1: Profile only slow operations")
        print(f"   slowms: 1000ms (1 second) - adjust based on your needs")
        print(f"   sampleRate: 0.1 (10%) - MongoDB 4.4+ only")
        
        # Ask for confirmation
        setup_profiling = input(f"\n❓ Set up profiling for '{db_name}'? (y/N): ").strip().lower()
        
        if setup_profiling == 'y':
            # Get profiling parameters
            slowms = input("Enter slowms threshold in milliseconds (default: 1000): ").strip()
            if not slowms:
                slowms = 1000
            else:
                slowms = int(slowms)
            
            # Check MongoDB version for sampleRate support
            server_info = client.server_info()
            version = server_info.get('version', '0.0.0')
            major_version = int(version.split('.')[0])
            minor_version = int(version.split('.')[1]) if '.' in version else 0
            
            supports_sample_rate = (major_version > 4) or (major_version == 4 and minor_version >= 4)
            
            if supports_sample_rate:
                sample_rate = input("Enter sample rate (0.1 for 10%, default: 0.1): ").strip()
                if not sample_rate:
                    sample_rate = 0.1
                else:
                    sample_rate = float(sample_rate)
                
                # Set profiling with sample rate
                result = db.command("profile", 1, slowms=slowms, sampleRate=sample_rate)
                print(f"✅ Profiling enabled: Level 1, slowms={slowms}ms, sampleRate={sample_rate}")
            else:
                # Set profiling without sample rate (older MongoDB versions)
                result = db.command("profile", 1, slowms=slowms)
                print(f"✅ Profiling enabled: Level 1, slowms={slowms}ms")
                print(f"ℹ️  Note: sampleRate not supported in MongoDB {version}")
        
        # Check system.profile collection
        profile_count = db.system.profile.count_documents({})
        print(f"\n📈 Current profile collection size: {profile_count} documents")
        
        if profile_count == 0:
            print("⚠️  No profiling data found. Generate some database activity to see results.")
        
        # Generate environment variables
        print(f"\n🔧 Environment variables for the optimizer:")
        print(f"export MONGO_URI=\"{mongo_uri}\"")
        print(f"export MONGO_DB_NAME=\"{db_name}\"")
        print(f"export OPENROUTER_API_KEY=\"your_openrouter_api_key\"")
        
        # Save to .env file
        save_env = input(f"\n💾 Save environment variables to .env file? (y/N): ").strip().lower()
        if save_env == 'y':
            with open('.env', 'w') as f:
                f.write(f"MONGO_URI={mongo_uri}\n")
                f.write(f"MONGO_DB_NAME={db_name}\n")
                f.write(f"OPENROUTER_API_KEY=your_openrouter_api_key\n")
                f.write(f"# Optional: Uncomment to use mock LLM service\n")
                f.write(f"# OPENROUTER_API_URL=http://localhost:8080/api/v1/chat/completions\n")
            print("✅ Environment variables saved to .env file")
            print("⚠️  Remember to update OPENROUTER_API_KEY with your actual API key!")
        
        print(f"\n🚀 Setup complete! You can now run the optimizer:")
        print(f"   source venv/bin/activate")
        print(f"   python mongo-optimiser-agent.py")
        
        return True
        
    except ConnectionFailure:
        print(f"❌ Failed to connect to MongoDB at {mongo_uri}")
        print("   Check your connection string and ensure MongoDB is running")
        return False
    except OperationFailure as e:
        print(f"❌ MongoDB operation failed: {e}")
        print("   Check your permissions - you may need dbAdmin role")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("MongoDB Query Optimizer - Production Database Setup")
        print("Usage: python setup_production_db.py")
        print("\nThis script helps you:")
        print("- Connect to your existing MongoDB database")
        print("- Set up appropriate profiling settings")
        print("- Generate environment variables for the optimizer")
        return
    
    success = setup_production_profiling()
    if success:
        print(f"\n🎉 Setup completed successfully!")
    else:
        print(f"\n💥 Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
