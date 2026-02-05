"""
Cloud Server for ESP32-CAM Door Lock System
Flask REST API for QR Code validation and Face Recognition

Deploy this to Railway, AWS, Google Cloud, or any cloud platform

Installation:
    pip install -r requirements.txt

Usage:
    python cloud_server.py

Endpoints:
    POST /api/verify-qr      - Verify QR code from image
    POST /api/recognize-face - Recognize face from image
    GET  /api/status         - Check server status
    POST /api/upload-dataset - Upload training images (admin only)
"""

from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
import hashlib
import os
import pickle
from datetime import datetime
import face_recognition
from pyzbar.pyzbar import decode
import threading
import time
from mongo_config import MongoDBConfig

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ==================== CONFIGURATION ====================

# WhatsApp notification (optional)
ADMIN_PHONE = os.environ.get('ADMIN_PHONE', '+917889273694')  # Change this
ENABLE_WHATSAPP = os.environ.get('ENABLE_WHATSAPP', 'false').lower() == 'true'

# QR Code Hash - must match the QR code used by ESP32-CAM
CORRECT_QR_HASH = os.environ.get('QR_HASH', '7eb04163ef896754651041b69afe0bb9a45eb932faa787d3e93a262f7e074186')

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'dataset')
ENCODINGS_FILE = os.path.join(BASE_DIR, 'face_encodings.pkl')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create necessary directories
os.makedirs(DATASET_PATH, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Initialize MongoDB connection
mongo_db = None
try:
    mongo_uri = os.environ.get('MONGO_URI')
    if mongo_uri:
        mongo_db = MongoDBConfig(mongo_uri)
        print("✓ MongoDB connected for cloud deployment")
    else:
        print("⚠ Warning: MONGO_URI not set. Face recognition will not work.")
except Exception as e:
    print(f"⚠ MongoDB connection failed: {e}")
    mongo_db = None

# Global variables
known_face_encodings = []
known_face_names = []
encodings_loaded = False
session_cache = {}  # Store session data

# ==================== LOGGING ====================

def log_access(event_type, details):
    """Log access events to file and MongoDB"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(LOGS_DIR, f"access_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Log to file
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {event_type}: {details}\n")
    
    # Log to MongoDB if available
    if mongo_db:
        try:
            mongo_db.log_access_event(event_type, details)
        except Exception as e:
            print(f"Failed to log to MongoDB: {e}")
    
    print(f"[{timestamp}] {event_type}: {details}")

# ==================== FACE RECOGNITION ====================

def load_face_encodings():
    """Load face encodings from MongoDB or pickle file"""
    global known_face_encodings, known_face_names, encodings_loaded
    
    # Try MongoDB first
    if mongo_db:
        try:
            print("Loading face encodings from MongoDB...")
            encodings, names = mongo_db.get_all_face_encodings()
            if len(encodings) > 0:
                known_face_encodings = encodings
                known_face_names = names
                print(f"✓ Loaded {len(known_face_encodings)} face encodings from MongoDB")
                encodings_loaded = True
                return True
        except Exception as e:
            print(f"Error loading from MongoDB: {e}")
    
    # Fallback to pickle file
    if os.path.exists(ENCODINGS_FILE):
        try:
            print("Loading pre-computed face encodings from file...")
            with open(ENCODINGS_FILE, 'rb') as f:
                data = pickle.load(f)
            known_face_encodings = data['encodings']
            known_face_names = data['names']
            print(f"✓ Loaded {len(known_face_encodings)} face encodings from file")
            encodings_loaded = True
            return True
        except Exception as e:
            print(f"Error loading encodings from file: {e}")
            return False
    else:
        print("No encodings found. Please upload training data first.")
        return False

def create_face_encodings_from_dataset():
    """Create face encodings from dataset images"""
    global known_face_encodings, known_face_names, encodings_loaded
    
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset folder not found at {DATASET_PATH}")
        return False
    
    known_face_encodings = []
    known_face_names = []
    
    print("Creating face encodings from dataset...")
    total_faces = 0
    
    for person_name in os.listdir(DATASET_PATH):
        person_folder = os.path.join(DATASET_PATH, person_name)
        
        if not os.path.isdir(person_folder):
            continue
        
        print(f"  Processing {person_name}...", end=" ")
        person_face_count = 0
        
        for image_name in os.listdir(person_folder):
            if not image_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            
            image_path = os.path.join(person_folder, image_name)
            
            try:
                # Load image
                image = face_recognition.load_image_file(image_path)
                
                # Get face encodings
                face_encodings = face_recognition.face_encodings(image, model='large')
                
                if len(face_encodings) > 0:
                    encoding = face_encodings[0]
                    known_face_encodings.append(encoding)
                    known_face_names.append(person_name)
                    person_face_count += 1
                    total_faces += 1
                
            except Exception as e:
                print(f"\n  Warning: Could not process {image_name}: {e}")
                continue
        
        print(f"✓ {person_face_count} faces loaded")
    
    print(f"\n✓ Total: {total_faces} face encodings from {len(set(known_face_names))} people")
    
    # Save encodings to MongoDB if available
    if total_faces > 0:
        if mongo_db:
            try:
                print("Saving encodings to MongoDB...")
                for i, (encoding, name) in enumerate(zip(known_face_encodings, known_face_names)):
                    mongo_db.save_face_encoding(name, encoding, f"dataset_image_{i}")
                print("✓ Encodings saved to MongoDB")
            except Exception as e:
                print(f"Warning: Could not save to MongoDB: {e}")
        
        # Also save to file as backup
        with open(ENCODINGS_FILE, 'wb') as f:
            pickle.dump({'encodings': known_face_encodings, 'names': known_face_names}, f)
        print(f"✓ Encodings saved to {ENCODINGS_FILE}")
        encodings_loaded = True
        return True
    else:
        print("✗ No faces found in dataset!")
        return False

def preprocess_image_for_recognition(image_np):
    """Preprocess image to improve face recognition accuracy"""
    try:
        # Convert to RGB
        rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        
        # Apply histogram equalization to improve contrast
        # Convert to YCrCb color space
        ycrcb = cv2.cvtColor(image_np, cv2.COLOR_BGR2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        enhanced = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        rgb_image = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        
        # Apply slight Gaussian blur to reduce noise
        rgb_image = cv2.GaussianBlur(rgb_image, (3, 3), 0)
        
        # Sharpen the image slightly for better feature detection
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        rgb_image = cv2.filter2D(rgb_image, -1, kernel)
        
        return rgb_image
    except:
        # Fallback to simple conversion if preprocessing fails
        return cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)

def recognize_face_from_image(image_np):
    """Recognize face from numpy image array with optimized settings"""
    global known_face_encodings, known_face_names
    
    if not encodings_loaded or len(known_face_encodings) == 0:
        return None, "No face encodings loaded"
    
    try:
        # Preprocess image for better recognition
        rgb_image = preprocess_image_for_recognition(image_np)
        
        # Find face locations using HOG (faster than CNN)
        # Try with different scales for better detection
        face_locations = face_recognition.face_locations(rgb_image, model='hog', number_of_times_to_upsample=1)
        
        if len(face_locations) == 0:
            return None, "No face detected in image"
        
        # Check face size - reject if too small or too far
        top, right, bottom, left = face_locations[0]
        face_height = bottom - top
        face_width = right - left
        image_height, image_width = rgb_image.shape[:2]
        
        face_area_ratio = (face_height * face_width) / (image_height * image_width)
        
        if face_area_ratio < 0.05:  # Face is too small (less than 5% of image)
            return None, "Face too small or too far. Move closer to camera"
        
        # Get face encodings using 'large' model for accuracy
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations, model='large')
        
        if len(face_encodings) == 0:
            return None, "Could not encode face"
        
        # Compare with known faces - LOWER TOLERANCE for better differentiation
        face_encoding = face_encodings[0]
        
        # Tolerance: 0.45 = stricter matching, better differentiation between users
        # Lower = more strict, Higher = more lenient
        TOLERANCE = 0.45
        MIN_CONFIDENCE = 52.0  # Minimum 52% confidence to accept
        
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=TOLERANCE)
        
        name = None
        confidence = 0.0
        
        # Calculate face distances (lower = better match)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        
        if len(face_distances) > 0:
            # Get best match
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]
            
            # Convert distance to confidence percentage (0-100%)
            confidence = (1 - best_distance) * 100
            
            print(f"Best match: {known_face_names[best_match_index]}, Distance: {best_distance:.4f}, Confidence: {confidence:.1f}%")
            
            # Accept only if match is confirmed AND confidence is above threshold
            if matches[best_match_index] and confidence >= MIN_CONFIDENCE:
                name = known_face_names[best_match_index]
                
                # Get all matches for this person to verify consistency
                person_matches = [i for i, n in enumerate(known_face_names) if n == name]
                person_distances = [face_distances[i] for i in person_matches]
                avg_person_distance = np.mean(person_distances)
                avg_confidence = (1 - avg_person_distance) * 100
                
                return name, f"Recognized with {avg_confidence:.1f}% confidence"
            else:
                # Log why recognition failed
                if confidence < MIN_CONFIDENCE:
                    return None, f"Confidence too low ({confidence:.1f}%). Face not in database"
                else:
                    return None, f"Face not recognized. No match found"
        
        return None, "Face not recognized"
        
    except Exception as e:
        return None, f"Error during recognition: {str(e)}"

# ==================== QR CODE VALIDATION ====================

def decode_qr_from_image(image_np):
    """Decode QR code from numpy image array"""
    try:
        # Convert to grayscale for better QR detection
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        
        # Decode QR codes
        qr_codes = decode(gray)
        
        if len(qr_codes) > 0:
            decoded_data = qr_codes[0].data.decode('utf-8')
            return decoded_data
        else:
            # Try with original image
            qr_codes = decode(image_np)
            if len(qr_codes) > 0:
                return qr_codes[0].data.decode('utf-8')
        
        return None
        
    except Exception as e:
        print(f"Error decoding QR: {e}")
        return None

def validate_qr_code(qr_data):
    """Validate QR code against correct hash"""
    if qr_data is None:
        return False
    
    # Direct comparison
    if qr_data.lower() == CORRECT_QR_HASH.lower():
        return True
    
    # Hash comparison (if QR contains plain text)
    qr_hash = hashlib.sha256(qr_data.encode()).hexdigest()
    if qr_hash.lower() == CORRECT_QR_HASH.lower():
        return True
    
    return False

# ==================== WHATSAPP NOTIFICATION ====================

def send_whatsapp_notification(message):
    """Send WhatsApp notification (async) - Not available in cloud environment"""
    if not ENABLE_WHATSAPP:
        return
    
    # WhatsApp notifications disabled in cloud (requires pywhatkit which needs GUI)
    # For cloud notifications, consider using Twilio, SendGrid, or webhook integrations
    print(f"⚠️ WhatsApp notifications not available in cloud environment")
    print(f"   Message would have been sent: {message}")
    print(f"   Consider integrating Twilio API for SMS/WhatsApp in production")

# ==================== API ENDPOINTS ====================

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'service': 'ESP32-CAM Door Lock System',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'qr_validation': '/api/verify-qr',
            'face_recognition': '/api/recognize-face',
            'status': '/api/status'
        }
    })

@app.route('/api/status', methods=['GET'])
def status():
    """Check server status"""
    return jsonify({
        'status': 'online',
        'encodings_loaded': encodings_loaded,
        'known_faces': len(set(known_face_names)),
        'total_encodings': len(known_face_encodings),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/verify-qr', methods=['POST'])
def verify_qr():
    """Verify QR code from ESP32-CAM"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        image_base64 = data['image']
        image_bytes = base64.b64decode(image_base64)
        image_np = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        if image_np is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Decode QR code
        qr_data = decode_qr_from_image(image_np)
        
        if qr_data is None:
            log_access("QR_SCAN_FAILED", "No QR code detected")
            return jsonify({
                'valid': False,
                'message': 'No QR code detected'
            })
        
        # Validate QR code
        is_valid = validate_qr_code(qr_data)
        
        if is_valid:
            # Create session ID
            session_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()
            session_cache[session_id] = {
                'timestamp': datetime.now(),
                'qr_validated': True
            }
            
            log_access("QR_VALID", f"Session: {session_id}")
            
            return jsonify({
                'valid': True,
                'success': True,
                'message': 'QR code validated',
                'session_id': session_id
            })
        else:
            log_access("QR_INVALID", f"Wrong QR: {qr_data[:50]}")
            return jsonify({
                'valid': False,
                'message': 'Invalid QR code'
            })
    
    except Exception as e:
        log_access("QR_ERROR", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/recognize-face', methods=['POST'])
def recognize_face():
    """Recognize face from ESP32-CAM"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        image_base64 = data['image']
        image_bytes = base64.b64decode(image_base64)
        image_np = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        
        if image_np is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Recognize face
        name, message = recognize_face_from_image(image_np)
        
        if name is not None:
            log_access("FACE_RECOGNIZED", f"Name: {name}, {message}")
            
            # Send WhatsApp notification (async)
            if ENABLE_WHATSAPP:
                threading.Thread(target=send_whatsapp_notification, 
                               args=(f"🔓 Door unlocked by {name} at {datetime.now().strftime('%H:%M:%S')}",)).start()
            
            return jsonify({
                'recognized': True,
                'success': True,
                'name': name,
                'message': message,
                'access': 'granted',
                'timestamp': datetime.now().isoformat()
            })
        else:
            log_access("FACE_NOT_RECOGNIZED", message)
            return jsonify({
                'recognized': False,
                'success': False,
                'message': message,
                'access': 'denied'
            })
    
    except Exception as e:
        log_access("FACE_ERROR", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/reload-encodings', methods=['POST'])
def reload_encodings():
    """Reload face encodings from dataset (admin only)"""
    try:
        success = create_face_encodings_from_dataset()
        
        if success:
            log_access("ENCODINGS_RELOADED", f"{len(known_face_encodings)} encodings")
            return jsonify({
                'success': True,
                'message': f'Loaded {len(known_face_encodings)} encodings from {len(set(known_face_names))} people'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to load encodings'
            }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get today's access logs (admin only)"""
    try:
        log_file = os.path.join(LOGS_DIR, f"access_{datetime.now().strftime('%Y%m%d')}.log")
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
            
            return jsonify({
                'success': True,
                'logs': logs[-50:],  # Last 50 entries
                'count': len(logs)
            })
        else:
            return jsonify({
                'success': True,
                'logs': [],
                'message': 'No logs for today'
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== STARTUP ====================

def initialize_system():
    """Initialize system on startup"""
    print("\n" + "="*50)
    print("ESP32-CAM Door Lock - Cloud Server")
    print("="*50 + "\n")
    
    # Load face encodings
    load_face_encodings()
    
    print("\n" + "="*50)
    print("Server Ready!")
    print("="*50 + "\n")

# ==================== MAIN ====================

if __name__ == '__main__':
    # Initialize system
    initialize_system()
    
    # Get port from environment (Railway, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    
    # Run server
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
