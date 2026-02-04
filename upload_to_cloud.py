"""
Upload Face Dataset to Cloud MongoDB
This script uploads your local face encodings to MongoDB Atlas for cloud deployment

Usage:
    1. Set MONGO_URI in .env file or as environment variable
    2. Ensure dataset/ folder has face images organized by person name
    3. Run: python upload_to_cloud.py

Directory structure:
    dataset/
        Person1/
            image1.jpg
            image2.jpg
        Person2/
            image1.jpg
"""

import os
from mongo_config import MongoDBConfig
import face_recognition
from pathlib import Path

def upload_dataset_to_mongo():
    """Upload face encodings from dataset folder to MongoDB"""
    
    # Get MongoDB URI from environment
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("❌ Error: MONGO_URI environment variable not set")
        print("   Set it in .env file or export MONGO_URI='your_connection_string'")
        return False
    
    # Connect to MongoDB
    try:
        print("🔌 Connecting to MongoDB...")
        mongo_db = MongoDBConfig(mongo_uri)
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    
    # Check dataset folder
    dataset_path = Path(__file__).parent / 'dataset'
    if not dataset_path.exists():
        print(f"❌ Dataset folder not found at: {dataset_path}")
        return False
    
    print(f"\n📁 Scanning dataset folder: {dataset_path}")
    
    total_uploaded = 0
    total_people = 0
    
    # Process each person's folder
    for person_folder in dataset_path.iterdir():
        if not person_folder.is_dir():
            continue
        
        person_name = person_folder.name
        print(f"\n👤 Processing: {person_name}")
        
        # Add user to MongoDB if not exists
        user = mongo_db.get_user_by_name(person_name)
        if not user:
            mongo_db.add_user(person_name)
        
        person_count = 0
        
        # Process each image
        for image_file in person_folder.iterdir():
            if image_file.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                continue
            
            try:
                print(f"   📸 Processing: {image_file.name}...", end=" ")
                
                # Load image and get face encoding
                image = face_recognition.load_image_file(str(image_file))
                encodings = face_recognition.face_encodings(image, model='large')
                
                if len(encodings) == 0:
                    print("⚠️  No face found")
                    continue
                
                # Save to MongoDB
                encoding = encodings[0]
                mongo_db.save_face_encoding(person_name, encoding, image_file.name)
                
                print("✅")
                person_count += 1
                total_uploaded += 1
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        if person_count > 0:
            print(f"   ✅ Uploaded {person_count} encodings for {person_name}")
            total_people += 1
        else:
            print(f"   ⚠️  No valid faces found for {person_name}")
    
    # Summary
    print("\n" + "="*50)
    print(f"✅ Upload Complete!")
    print(f"   Total people: {total_people}")
    print(f"   Total encodings: {total_uploaded}")
    print("="*50)
    
    # Verify upload
    print("\n🔍 Verifying uploaded data...")
    encodings, names = mongo_db.get_all_face_encodings()
    print(f"✅ Verified: {len(encodings)} encodings in MongoDB")
    print(f"   People: {list(set(names))}")
    
    return True

if __name__ == '__main__':
    print("="*50)
    print("Upload Face Dataset to Cloud MongoDB")
    print("="*50)
    print()
    
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed (optional)")
    except Exception as e:
        print(f"⚠️  Could not load .env: {e}")
    
    print()
    
    success = upload_dataset_to_mongo()
    
    if success:
        print("\n🎉 Success! Your face dataset is now in MongoDB Atlas")
        print("   You can now deploy to Railway")
    else:
        print("\n❌ Upload failed. Please check errors above")
