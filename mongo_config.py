"""
MongoDB Configuration for Face Recognition System
This file handles all MongoDB connections and operations
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from datetime import datetime
import pickle
import numpy as np

class MongoDBConfig:
    def __init__(self, connection_string=None):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB URI (local or Atlas)
                              If None, reads from environment variable MONGO_URI
                              
        Example for local: "mongodb://localhost:27017/"
        Example for Atlas: "mongodb+srv://username:password@cluster.mongodb.net/"
        """
        if connection_string is None:
            connection_string = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            print("✓ Connected to MongoDB successfully!")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ Failed to connect to MongoDB: {e}")
            print("Please ensure MongoDB is running or check your connection string.")
            raise
        
        # Database and collections
        self.db = self.client['face_recognition_db']
        self.users_collection = self.db['users']
        self.encodings_collection = self.db['face_encodings']
        self.access_logs_collection = self.db['access_logs']
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create indexes for efficient querying"""
        self.users_collection.create_index('name', unique=True)
        self.encodings_collection.create_index('user_id')
        self.access_logs_collection.create_index([('timestamp', -1)])
        self.access_logs_collection.create_index('user_name')
    
    def add_user(self, name, phone_number=None, email=None, role='user'):
        """
        Add a new user to the database
        
        Args:
            name: User's name
            phone_number: User's phone number (optional)
            email: User's email (optional)
            role: User role (default: 'user', can be 'admin')
        
        Returns:
            user_id if successful, None otherwise
        """
        try:
            user_doc = {
                'name': name,
                'phone_number': phone_number,
                'email': email,
                'role': role,
                'created_at': datetime.now(),
                'is_active': True
            }
            result = self.users_collection.insert_one(user_doc)
            print(f"✓ User '{name}' added successfully!")
            return str(result.inserted_id)
        except Exception as e:
            print(f"✗ Error adding user '{name}': {e}")
            return None
    
    def get_user_by_name(self, name):
        """Get user document by name"""
        return self.users_collection.find_one({'name': name})
    
    def get_all_users(self):
        """Get all active users"""
        return list(self.users_collection.find({'is_active': True}))
    
    def save_face_encoding(self, user_name, encoding, image_name=None):
        """
        Save face encoding for a user
        
        Args:
            user_name: User's name
            encoding: Face encoding (numpy array)
            image_name: Original image filename (optional)
        
        Returns:
            encoding_id if successful, None otherwise
        """
        try:
            # Get or create user
            user = self.get_user_by_name(user_name)
            if not user:
                user_id = self.add_user(user_name)
            else:
                user_id = str(user['_id'])
            
            # Convert numpy array to list for JSON serialization
            encoding_list = encoding.tolist() if isinstance(encoding, np.ndarray) else encoding
            
            encoding_doc = {
                'user_id': user_id,
                'user_name': user_name,
                'encoding': encoding_list,
                'image_name': image_name,
                'created_at': datetime.now()
            }
            
            result = self.encodings_collection.insert_one(encoding_doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"✗ Error saving encoding for '{user_name}': {e}")
            return None
    
    def get_all_face_encodings(self):
        """
        Get all face encodings from database
        
        Returns:
            tuple: (encodings_list, names_list)
        """
        try:
            encodings = []
            names = []
            
            cursor = self.encodings_collection.find()
            for doc in cursor:
                # Convert list back to numpy array
                encoding = np.array(doc['encoding'])
                encodings.append(encoding)
                names.append(doc['user_name'])
            
            print(f"✓ Loaded {len(encodings)} face encodings from MongoDB")
            return encodings, names
        except Exception as e:
            print(f"✗ Error loading encodings: {e}")
            return [], []
    
    def log_access(self, user_name, status, access_type='face_recognition', confidence=None):
        """
        Log door access event
        
        Args:
            user_name: Name of person accessing
            status: 'opened' or 'denied'
            access_type: Type of access (default: 'face_recognition')
            confidence: Recognition confidence percentage (optional)
        
        Returns:
            log_id if successful, None otherwise
        """
        try:
            log_doc = {
                'user_name': user_name,
                'status': status,
                'access_type': access_type,
                'confidence': confidence,
                'timestamp': datetime.now()
            }
            
            result = self.access_logs_collection.insert_one(log_doc)
            print(f"✓ Access logged: {user_name} - {status}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"✗ Error logging access: {e}")
            return None
    
    def get_access_logs(self, limit=100, user_name=None):
        """
        Get access logs
        
        Args:
            limit: Number of logs to retrieve (default: 100)
            user_name: Filter by user name (optional)
        
        Returns:
            List of access log documents
        """
        query = {}
        if user_name:
            query['user_name'] = user_name
        
        return list(self.access_logs_collection.find(query).sort('timestamp', -1).limit(limit))
    
    def delete_user_encodings(self, user_name):
        """Delete all encodings for a user"""
        try:
            result = self.encodings_collection.delete_many({'user_name': user_name})
            print(f"✓ Deleted {result.deleted_count} encodings for '{user_name}'")
            return result.deleted_count
        except Exception as e:
            print(f"✗ Error deleting encodings: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✓ MongoDB connection closed")


# Utility function for migration from local files to MongoDB
def migrate_local_to_mongodb(dataset_path, mongo_config):
    """
    Migrate local face encodings to MongoDB
    
    Args:
        dataset_path: Path to local dataset folder
        mongo_config: MongoDBConfig instance
    """
    import face_recognition
    
    print("="*70)
    print(" MIGRATING LOCAL DATASET TO MONGODB")
    print("="*70)
    
    total_migrated = 0
    
    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        
        if not os.path.isdir(person_folder):
            continue
        
        print(f"\nProcessing {person_name}...")
        person_count = 0
        
        for image_name in os.listdir(person_folder):
            if not image_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            
            image_path = os.path.join(person_folder, image_name)
            
            try:
                # Load and encode face
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image, model='large')
                
                if len(face_encodings) > 0:
                    encoding = face_encodings[0]
                    
                    # Save to MongoDB
                    mongo_config.save_face_encoding(person_name, encoding, image_name)
                    person_count += 1
                    total_migrated += 1
                    print(f"  ✓ {image_name}")
                
            except Exception as e:
                print(f"  ✗ Error processing {image_name}: {e}")
        
        print(f"  Total: {person_count} faces migrated")
    
    print(f"\n{'='*70}")
    print(f" MIGRATION COMPLETE: {total_migrated} face encodings migrated")
    print(f"{'='*70}")


if __name__ == "__main__":
    # Test connection
    try:
        mongo = MongoDBConfig()
        
        # Print some stats
        user_count = mongo.users_collection.count_documents({})
        encoding_count = mongo.encodings_collection.count_documents({})
        log_count = mongo.access_logs_collection.count_documents({})
        
        print(f"\nDatabase Statistics:")
        print(f"  Users: {user_count}")
        print(f"  Face Encodings: {encoding_count}")
        print(f"  Access Logs: {log_count}")
        
        mongo.close()
    except Exception as e:
        print(f"Error: {e}")
