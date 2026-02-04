"""
View MongoDB Database Contents
This script displays all data stored in MongoDB including:
- Users/Dataset
- Face Encodings
- Access Logs
"""

import os
from mongo_config import MongoDBConfig
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def view_users(mongo_db):
    """Display all users in the database"""
    print_header("USERS / DATASET")
    
    users = mongo_db.get_all_users()
    
    if len(users) == 0:
        print("No users found in database.")
        return
    
    print(f"\nTotal Users: {len(users)}\n")
    
    for idx, user in enumerate(users, 1):
        print(f"{idx}. Name: {user['name']}")
        print(f"   User ID: {user['_id']}")
        print(f"   Role: {user.get('role', 'user')}")
        print(f"   Phone: {user.get('phone_number', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   Created: {user['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Status: {'Active' if user.get('is_active', True) else 'Inactive'}")
        print()

def view_face_encodings(mongo_db):
    """Display face encodings statistics"""
    print_header("FACE ENCODINGS")
    
    # Get all encodings
    cursor = mongo_db.encodings_collection.find()
    encodings_list = list(cursor)
    
    if len(encodings_list) == 0:
        print("No face encodings found in database.")
        return
    
    # Group by user
    user_encodings = {}
    for enc in encodings_list:
        user_name = enc['user_name']
        if user_name not in user_encodings:
            user_encodings[user_name] = []
        user_encodings[user_name].append(enc)
    
    print(f"\nTotal Encodings: {len(encodings_list)}")
    print(f"Total Users: {len(user_encodings)}\n")
    
    print(f"{'User Name':<25} {'Encodings':<12} {'Last Updated':<20}")
    print("-" * 80)
    
    for user_name, encodings in sorted(user_encodings.items()):
        latest_date = max([enc['created_at'] for enc in encodings])
        print(f"{user_name:<25} {len(encodings):<12} {latest_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "-" * 80)
    print("Note: Each user should have multiple encodings (from different images)")
    print("      for better recognition accuracy.")

def view_access_logs(mongo_db, limit=20):
    """Display recent access logs"""
    print_header(f"ACCESS LOGS (Last {limit} entries)")
    
    logs = mongo_db.get_access_logs(limit=limit)
    
    if len(logs) == 0:
        print("No access logs found in database.")
        return
    
    print(f"\nTotal Logs in Database: {mongo_db.access_logs_collection.count_documents({})}")
    print(f"Showing last {len(logs)} entries:\n")
    
    print(f"{'#':<4} {'Timestamp':<20} {'User Name':<20} {'Status':<10} {'Confidence':<12}")
    print("-" * 80)
    
    for idx, log in enumerate(logs, 1):
        timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        user_name = log['user_name']
        status = log['status']
        confidence = f"{log.get('confidence', 'N/A')}%" if log.get('confidence') else 'N/A'
        
        print(f"{idx:<4} {timestamp:<20} {user_name:<20} {status:<10} {confidence:<12}")
    
    print("\n" + "-" * 80)
    
    # Statistics
    total_opened = mongo_db.access_logs_collection.count_documents({'status': 'opened'})
    total_denied = mongo_db.access_logs_collection.count_documents({'status': 'denied'})
    
    print(f"\nStatistics:")
    print(f"  Total Opened: {total_opened}")
    print(f"  Total Denied: {total_denied}")
    print(f"  Success Rate: {(total_opened / (total_opened + total_denied) * 100):.2f}%" if (total_opened + total_denied) > 0 else "  Success Rate: N/A")

def view_database_stats(mongo_db):
    """Display overall database statistics"""
    print_header("DATABASE OVERVIEW")
    
    user_count = mongo_db.users_collection.count_documents({})
    encoding_count = mongo_db.encodings_collection.count_documents({})
    log_count = mongo_db.access_logs_collection.count_documents({})
    
    print(f"\n{'Category':<30} {'Count':<15}")
    print("-" * 50)
    print(f"{'Total Users':<30} {user_count:<15}")
    print(f"{'Total Face Encodings':<30} {encoding_count:<15}")
    print(f"{'Total Access Logs':<30} {log_count:<15}")
    
    if user_count > 0:
        avg_encodings = encoding_count / user_count
        print(f"{'Avg Encodings per User':<30} {avg_encodings:<15.2f}")
    
    # Database size
    db_stats = mongo_db.db.command("dbstats")
    db_size_mb = db_stats.get('dataSize', 0) / (1024 * 1024)
    print(f"{'Database Size':<30} {db_size_mb:<15.2f} MB")

def search_user_logs(mongo_db, user_name):
    """Search logs for a specific user"""
    print_header(f"ACCESS LOGS FOR: {user_name}")
    
    logs = mongo_db.get_access_logs(limit=100, user_name=user_name)
    
    if len(logs) == 0:
        print(f"No access logs found for user '{user_name}'.")
        return
    
    print(f"\nTotal Access Attempts: {len(logs)}\n")
    
    for idx, log in enumerate(logs, 1):
        timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        status = log['status']
        confidence = f"{log.get('confidence', 'N/A')}%" if log.get('confidence') else 'N/A'
        
        print(f"{idx}. {timestamp} - Status: {status} - Confidence: {confidence}")

def main():
    """Main function"""
    try:
        # Connect to MongoDB
        connection_string = os.getenv('MONGO_URI')
        if connection_string:
            mongo_db = MongoDBConfig(connection_string)
        else:
            print("Using default MongoDB connection...")
            mongo_db = MongoDBConfig()
        
        while True:
            print("\n" + "=" * 80)
            print(" MONGODB DATABASE VIEWER")
            print("=" * 80)
            print("\nOptions:")
            print("  1. View Database Overview")
            print("  2. View All Users/Dataset")
            print("  3. View Face Encodings")
            print("  4. View Access Logs (last 20)")
            print("  5. View Access Logs (last 50)")
            print("  6. Search User Access Logs")
            print("  7. View Everything")
            print("  0. Exit")
            print()
            
            choice = input("Enter your choice (0-7): ").strip()
            
            if choice == '1':
                view_database_stats(mongo_db)
            elif choice == '2':
                view_users(mongo_db)
            elif choice == '3':
                view_face_encodings(mongo_db)
            elif choice == '4':
                view_access_logs(mongo_db, limit=20)
            elif choice == '5':
                view_access_logs(mongo_db, limit=50)
            elif choice == '6':
                user_name = input("Enter user name: ").strip()
                if user_name:
                    search_user_logs(mongo_db, user_name)
                else:
                    print("Invalid user name!")
            elif choice == '7':
                view_database_stats(mongo_db)
                view_users(mongo_db)
                view_face_encodings(mongo_db)
                view_access_logs(mongo_db, limit=20)
            elif choice == '0':
                print("\nExiting...")
                break
            else:
                print("Invalid choice! Please try again.")
            
            input("\nPress Enter to continue...")
        
        # Close connection
        mongo_db.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
