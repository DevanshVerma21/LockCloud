"""
Check if all local faces are uploaded to cloud MongoDB
"""

import os
from mongo_config import MongoDBConfig
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

def count_local_images():
    """Count images in local dataset folders"""
    dataset_path = os.path.join(os.path.dirname(__file__), 'dataset')
    local_counts = {}
    
    print("\n" + "="*80)
    print(" LOCAL DATASET")
    print("="*80)
    
    for person_name in os.listdir(dataset_path):
        person_path = os.path.join(dataset_path, person_name)
        if os.path.isdir(person_path):
            images = [f for f in os.listdir(person_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
            local_counts[person_name] = len(images)
            print(f"  {person_name:<25} {len(images):>3} images")
    
    total_local = sum(local_counts.values())
    print(f"\n  {'TOTAL LOCAL IMAGES:':<25} {total_local:>3}")
    
    return local_counts, total_local

def count_cloud_encodings(mongo_db):
    """Count encodings in cloud MongoDB"""
    print("\n" + "="*80)
    print(" CLOUD DATABASE (MongoDB)")
    print("="*80)
    
    # Get all encodings
    encodings = list(mongo_db.encodings_collection.find())
    
    # Count by user
    cloud_counts = defaultdict(int)
    for enc in encodings:
        cloud_counts[enc['user_name']] += 1
    
    for user_name, count in sorted(cloud_counts.items()):
        print(f"  {user_name:<25} {count:>3} encodings")
    
    total_cloud = sum(cloud_counts.values())
    print(f"\n  {'TOTAL CLOUD ENCODINGS:':<25} {total_cloud:>3}")
    
    return dict(cloud_counts), total_cloud

def compare_sync(local_counts, cloud_counts):
    """Compare local and cloud data"""
    print("\n" + "="*80)
    print(" SYNC STATUS COMPARISON")
    print("="*80)
    print(f"\n  {'Person':<25} {'Local':<10} {'Cloud':<10} {'Status':<15}")
    print("  " + "-"*70)
    
    all_names = set(local_counts.keys()) | set(cloud_counts.keys())
    
    fully_synced = True
    missing_people = []
    partial_sync = []
    
    for name in sorted(all_names):
        local = local_counts.get(name, 0)
        cloud = cloud_counts.get(name, 0)
        
        if local == 0 and cloud > 0:
            status = "⚠️ Cloud Only"
            fully_synced = False
        elif cloud == 0 and local > 0:
            status = "❌ NOT UPLOADED"
            fully_synced = False
            missing_people.append(name)
        elif cloud < local:
            status = "⚠️ Partial"
            fully_synced = False
            partial_sync.append((name, local, cloud))
        elif cloud == local:
            status = "✅ Synced"
        else:
            status = "⚠️ More in cloud"
        
        print(f"  {name:<25} {local:<10} {cloud:<10} {status:<15}")
    
    print("\n" + "="*80)
    
    if fully_synced and len(all_names) > 0:
        print("\n✅ SUCCESS: All faces are uploaded to cloud!")
        print("   Local images match cloud encodings.")
    else:
        print("\n❌ SYNC ISSUES DETECTED:")
        
        if missing_people:
            print(f"\n  Missing from cloud ({len(missing_people)} people):")
            for name in missing_people:
                print(f"    - {name} ({local_counts[name]} images)")
        
        if partial_sync:
            print(f"\n  Partially synced ({len(partial_sync)} people):")
            for name, local, cloud in partial_sync:
                print(f"    - {name}: {local} local images, only {cloud} cloud encodings")
        
        print("\n  💡 Solution: Run 'python upload_to_cloud.py' to sync all faces")
    
    print("="*80 + "\n")
    
    return fully_synced

def main():
    try:
        print("\n" + "="*80)
        print(" FACE SYNC CHECKER - Local vs Cloud")
        print("="*80)
        
        # Get connection string
        connection_string = os.getenv('MONGO_URI')
        if not connection_string:
            print("\n❌ Error: MONGO_URI not found in environment variables")
            print("   Please check your .env file")
            return
        
        # Connect to MongoDB
        print("\n⏳ Connecting to MongoDB...")
        mongo_db = MongoDBConfig(connection_string)
        print("✅ Connected successfully!")
        
        # Count local images
        local_counts, total_local = count_local_images()
        
        # Count cloud encodings
        cloud_counts, total_cloud = count_cloud_encodings(mongo_db)
        
        # Compare and show status
        is_synced = compare_sync(local_counts, cloud_counts)
        
        # Close connection
        mongo_db.close()
        
        return is_synced
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
