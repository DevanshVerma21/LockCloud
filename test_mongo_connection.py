"""
Quick test script to verify MongoDB Atlas connection
Run this before migration to ensure connection works
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys

def test_connection(connection_string):
    """Test MongoDB connection"""
    print("="*70)
    print(" MONGODB CONNECTION TEST")
    print("="*70)
    
    # Validate connection string format
    if '<db_username>' in connection_string or '<db_password>' in connection_string:
        print("\n✗ Error: Please replace <db_username> and <db_password> with actual values!")
        print("\nYour connection string should look like:")
        print("mongodb+srv://myuser:mypassword123@cluster0.fnatvnd.mongodb.net/?appName=Cluster0")
        return False
    
    print(f"\nConnection string: {connection_string[:50]}...")
    print("\nAttempting to connect...")
    
    try:
        # Try to connect
        client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
        
        # Verify connection
        client.admin.command('ping')
        
        print("\n✓ SUCCESS! Connected to MongoDB Atlas")
        
        # Show server info
        info = client.server_info()
        print(f"\nMongoDB Version: {info['version']}")
        
        # List databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")
        
        # Test database operations
        db = client['face_recognition_db']
        print(f"\n✓ Database 'face_recognition_db' ready")
        
        # List collections
        collections = db.list_collection_names()
        if collections:
            print(f"Existing collections: {collections}")
        else:
            print("No collections yet (will be created during migration)")
        
        client.close()
        
        print("\n" + "="*70)
        print(" CONNECTION TEST PASSED!")
        print("="*70)
        print("\nNext step: Run migration script")
        print("  python migrate_to_mongo.py")
        
        return True
        
    except ServerSelectionTimeoutError:
        print("\n✗ ERROR: Connection timeout")
        print("\nPossible issues:")
        print("  1. Check your internet connection")
        print("  2. Verify IP whitelist in MongoDB Atlas")
        print("     - Go to Network Access in Atlas dashboard")
        print("     - Add your IP or use 0.0.0.0/0 for testing")
        print("  3. Check if connection string is correct")
        return False
        
    except ConnectionFailure as e:
        print(f"\n✗ ERROR: Connection failed - {e}")
        print("\nCheck:")
        print("  1. Username and password are correct")
        print("  2. Special characters in password are URL-encoded")
        print("  3. Database user has proper permissions")
        return False
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nMongoDB Atlas Connection Tester")
    print("-" * 70)
    
    # Get connection string
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    else:
        print("\nEnter your MongoDB Atlas connection string:")
        print("(Replace <db_username> and <db_password> with your actual credentials)")
        print("\nExample: mongodb+srv://myuser:mypass@cluster0.fnatvnd.mongodb.net/?appName=Cluster0")
        connection_string = input("\nConnection string: ").strip()
    
    if not connection_string:
        print("✗ No connection string provided!")
        sys.exit(1)
    
    # Test connection
    success = test_connection(connection_string)
    
    if not success:
        sys.exit(1)
