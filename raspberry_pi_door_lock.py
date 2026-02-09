#!/usr/bin/env python3
"""
Raspberry Pi Zero 2 W Door Lock System
QR Code & Face Recognition with Cloud Server Integration

Hardware Requirements:
- Raspberry Pi Zero 2 W
- Pi Camera Module (v1/v2/HQ)
- 5V Relay Module
- 12V Solenoid Lock
- Power Supply (5V 2.5A for Pi + 12V 1A for solenoid)

GPIO Connections:
- GPIO 17: Relay control (Door Lock)
- GPIO 27: Status LED (Green)
- GPIO 22: Error LED (Red)
- GPIO 23: Flash LED (optional, for low light)

Author: Door Lock System
Date: 2026
"""

import os
import sys
import time
import base64
import requests
import json
import hashlib
from datetime import datetime
from io import BytesIO
import signal
import logging

# GPIO and Camera imports (with error handling for development)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("⚠ WARNING: RPi.GPIO not available. Running in simulation mode.")
    GPIO_AVAILABLE = False

try:
    from picamera2 import Picamera2
    from libcamera import controls
    CAMERA_AVAILABLE = True
except ImportError:
    print("⚠ WARNING: picamera2 not available. Running in simulation mode.")
    CAMERA_AVAILABLE = False

try:
    import cv2
    import numpy as np
    from pyzbar.pyzbar import decode
    CV2_AVAILABLE = True
except ImportError:
    print("⚠ WARNING: OpenCV not available. QR detection disabled.")
    CV2_AVAILABLE = False

# ==================== CONFIGURATION ====================

class Config:
    """System Configuration"""
    
    # Cloud Server Configuration
    CLOUD_SERVER_URL = os.environ.get('CLOUD_SERVER_URL', 
                                      'https://web-production-e2281.up.railway.app')
    QR_ENDPOINT = '/api/verify-qr'
    FACE_ENDPOINT = '/api/recognize-face'
    STATUS_ENDPOINT = '/api/status'
    
    # GPIO Pin Assignments (BCM numbering)
    RELAY_PIN = 17       # Door lock relay
    STATUS_LED = 27      # Green status LED
    ERROR_LED = 22       # Red error LED
    FLASH_LED = 23       # Optional flash LED for low light
    
    # Timing Configuration (in seconds)
    DOOR_OPEN_TIME = 5           # How long door stays unlocked
    QR_SCAN_INTERVAL = 2         # QR code scan frequency
    FACE_SCAN_INTERVAL = 2.5     # Face scan frequency
    FACE_CAPTURE_DELAY = 1       # Wait before capturing face after QR
    RETRY_DELAY = 0.5            # Delay between retries
    
    # Camera Configuration
    CAMERA_WIDTH = 640           # Camera resolution width
    CAMERA_HEIGHT = 480          # Camera resolution height
    CAMERA_BRIGHTNESS = 0.0      # -1.0 to 1.0
    CAMERA_CONTRAST = 1.0        # 0.0 to 2.0
    JPEG_QUALITY = 85            # JPEG compression quality (0-100)
    
    # QR Code Configuration (must match cloud server)
    QR_HASH = os.environ.get('QR_HASH', 
                             '7eb04163ef896754651041b69afe0bb9a45eb932faa787d3e93a262f7e074186')
    
    # System Configuration
    MAX_RETRIES = 3              # Max retry attempts for network requests
    ENABLE_LOCAL_QR = True       # Decode QR locally before sending to cloud
    ENABLE_FLASH = False         # Use flash LED in low light
    AUTO_SCAN_ENABLED = True     # Enable automatic scanning mode
    
    # Logging
    LOG_FILE = '/var/log/door_lock.log'
    LOG_LEVEL = logging.INFO

# ==================== LOGGING SETUP ====================

# Setup logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE) if os.access('/var/log', os.W_OK) 
        else logging.FileHandler('door_lock.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== GPIO CONTROL ====================

class GPIOController:
    """Manages GPIO pins for door lock and LEDs"""
    
    def __init__(self):
        self.initialized = False
        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                # Setup output pins
                GPIO.setup(Config.RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)  # HIGH = locked
                GPIO.setup(Config.STATUS_LED, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(Config.ERROR_LED, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(Config.FLASH_LED, GPIO.OUT, initial=GPIO.LOW)
                
                self.initialized = True
                logger.info("✓ GPIO initialized successfully")
            except Exception as e:
                logger.error(f"GPIO initialization failed: {e}")
        else:
            logger.warning("GPIO not available - running in simulation mode")
    
    def lock_door(self):
        """Lock the door (relay OFF)"""
        if self.initialized:
            GPIO.output(Config.RELAY_PIN, GPIO.HIGH)
            logger.info("🔒 Door LOCKED")
        else:
            logger.info("🔒 [SIMULATION] Door LOCKED")
    
    def unlock_door(self):
        """Unlock the door (relay ON)"""
        if self.initialized:
            GPIO.output(Config.RELAY_PIN, GPIO.LOW)
            logger.info("🔓 Door UNLOCKED")
        else:
            logger.info("🔓 [SIMULATION] Door UNLOCKED")
    
    def set_status_led(self, state):
        """Control status LED (Green)"""
        if self.initialized:
            GPIO.output(Config.STATUS_LED, GPIO.HIGH if state else GPIO.LOW)
    
    def set_error_led(self, state):
        """Control error LED (Red)"""
        if self.initialized:
            GPIO.output(Config.ERROR_LED, GPIO.HIGH if state else GPIO.LOW)
    
    def set_flash(self, state):
        """Control flash LED"""
        if self.initialized and Config.ENABLE_FLASH:
            GPIO.output(Config.FLASH_LED, GPIO.HIGH if state else GPIO.LOW)
    
    def blink_led(self, pin, times=3, delay=0.2):
        """Blink an LED"""
        if self.initialized:
            for _ in range(times):
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(delay)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(delay)
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if self.initialized:
            self.lock_door()  # Ensure door is locked
            GPIO.cleanup()
            logger.info("GPIO cleanup completed")

# ==================== CAMERA CONTROLLER ====================

class CameraController:
    """Manages Pi Camera for image capture"""
    
    def __init__(self):
        self.camera = None
        self.initialized = False
        
        if CAMERA_AVAILABLE:
            try:
                self.camera = Picamera2()
                
                # Configure camera
                camera_config = self.camera.create_still_configuration(
                    main={"size": (Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT)},
                    controls={
                        "Brightness": Config.CAMERA_BRIGHTNESS,
                        "Contrast": Config.CAMERA_CONTRAST
                    }
                )
                self.camera.configure(camera_config)
                self.camera.start()
                
                # Warm up camera
                time.sleep(2)
                
                self.initialized = True
                logger.info("✓ Camera initialized successfully")
            except Exception as e:
                logger.error(f"Camera initialization failed: {e}")
        else:
            logger.warning("Camera not available - running in simulation mode")
    
    def capture_image(self):
        """Capture image and return as numpy array"""
        if not self.initialized:
            logger.warning("Camera not initialized")
            return None
        
        try:
            # Capture image as numpy array
            image = self.camera.capture_array()
            
            # Convert from RGB to BGR for OpenCV compatibility
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            return image
        except Exception as e:
            logger.error(f"Image capture failed: {e}")
            return None
    
    def capture_and_encode_base64(self):
        """Capture image and encode to base64 string"""
        image = self.capture_image()
        if image is None:
            return None
        
        try:
            # Encode image as JPEG
            _, buffer = cv2.imencode('.jpg', image, 
                                    [cv2.IMWRITE_JPEG_QUALITY, Config.JPEG_QUALITY])
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            return image_base64
        except Exception as e:
            logger.error(f"Image encoding failed: {e}")
            return None
    
    def cleanup(self):
        """Cleanup camera resources"""
        if self.initialized and self.camera:
            self.camera.stop()
            logger.info("Camera cleanup completed")

# ==================== QR CODE HANDLER ====================

class QRCodeHandler:
    """Handles QR code detection and validation"""
    
    @staticmethod
    def decode_qr_local(image):
        """Decode QR code locally from image"""
        if not CV2_AVAILABLE:
            return None
        
        try:
            # Decode QR codes
            decoded_objects = decode(image)
            
            if len(decoded_objects) > 0:
                qr_data = decoded_objects[0].data.decode('utf-8')
                logger.info(f"QR code detected locally: {qr_data[:20]}...")
                return qr_data
            return None
        except Exception as e:
            logger.error(f"Local QR decode failed: {e}")
            return None
    
    @staticmethod
    def validate_qr_hash(qr_data):
        """Validate QR code hash locally"""
        try:
            qr_hash = hashlib.sha256(qr_data.encode()).hexdigest()
            is_valid = qr_hash == Config.QR_HASH
            
            if is_valid:
                logger.info("✓ QR code hash validated locally")
            else:
                logger.warning("✗ Invalid QR code hash")
            
            return is_valid
        except Exception as e:
            logger.error(f"QR hash validation failed: {e}")
            return False

# ==================== CLOUD API CLIENT ====================

class CloudAPIClient:
    """Handles communication with cloud server"""
    
    def __init__(self):
        self.session_id = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'RaspberryPi-DoorLock/1.0'
        })
    
    def check_server_status(self):
        """Check if cloud server is reachable"""
        try:
            url = Config.CLOUD_SERVER_URL + Config.STATUS_ENDPOINT
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info("✓ Cloud server is reachable")
                return True
            else:
                logger.warning(f"Cloud server returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cloud server unreachable: {e}")
            return False
    
    def verify_qr_code(self, image_base64):
        """Send QR code image to cloud for verification"""
        try:
            url = Config.CLOUD_SERVER_URL + Config.QR_ENDPOINT
            payload = {'image': image_base64}
            
            logger.info("Sending QR code to cloud for verification...")
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    self.session_id = result.get('session_id')
                    logger.info(f"✓ QR code validated by cloud (Session: {self.session_id})")
                    return True, result.get('message', 'QR code valid')
                else:
                    logger.warning(f"✗ QR validation failed: {result.get('message')}")
                    return False, result.get('message', 'Invalid QR code')
            else:
                logger.error(f"Cloud server error: {response.status_code}")
                return False, "Server error"
                
        except Exception as e:
            logger.error(f"QR verification request failed: {e}")
            return False, str(e)
    
    def recognize_face(self, image_base64):
        """Send face image to cloud for recognition"""
        try:
            url = Config.CLOUD_SERVER_URL + Config.FACE_ENDPOINT
            payload = {
                'image': image_base64,
                'session_id': self.session_id
            }
            
            logger.info("Sending face image to cloud for recognition...")
            response = self.session.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    name = result.get('name', 'Unknown')
                    confidence = result.get('confidence', 0)
                    logger.info(f"✓ Face recognized: {name} (confidence: {confidence:.2f})")
                    return True, name, confidence
                else:
                    logger.warning(f"✗ Face not recognized: {result.get('message')}")
                    return False, None, 0
            else:
                logger.error(f"Cloud server error: {response.status_code}")
                return False, None, 0
                
        except Exception as e:
            logger.error(f"Face recognition request failed: {e}")
            return False, None, 0

# ==================== MAIN DOOR LOCK SYSTEM ====================

class DoorLockSystem:
    """Main door lock system controller"""
    
    def __init__(self):
        self.gpio = GPIOController()
        self.camera = CameraController()
        self.qr_handler = QRCodeHandler()
        self.api_client = CloudAPIClient()
        
        self.system_ready = False
        self.qr_validated = False
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.running = False
    
    def initialize(self):
        """Initialize the system"""
        logger.info("="*60)
        logger.info("Raspberry Pi Door Lock System - Starting")
        logger.info("="*60)
        
        # Check cloud server
        self.gpio.set_error_led(True)
        if not self.api_client.check_server_status():
            logger.warning("⚠ Cloud server not reachable - system may not function properly")
        
        # Check camera
        if not self.camera.initialized:
            logger.error("✗ Camera initialization failed - cannot proceed")
            self.gpio.blink_led(Config.ERROR_LED, times=5, delay=0.3)
            return False
        
        # System ready
        self.system_ready = True
        self.gpio.set_error_led(False)
        self.gpio.blink_led(Config.STATUS_LED, times=3, delay=0.2)
        
        logger.info("="*60)
        logger.info("✓ System Ready - Waiting for QR codes...")
        logger.info(f"✓ Cloud Server: {Config.CLOUD_SERVER_URL}")
        logger.info(f"✓ Auto Scan: {'Enabled' if Config.AUTO_SCAN_ENABLED else 'Disabled'}")
        logger.info("="*60)
        
        return True
    
    def scan_qr_code(self):
        """Scan and validate QR code"""
        logger.info("📷 Scanning for QR code...")
        
        # Enable flash if needed
        if Config.ENABLE_FLASH:
            self.gpio.set_flash(True)
            time.sleep(0.1)
        
        # Capture image
        image_base64 = self.camera.capture_and_encode_base64()
        
        if Config.ENABLE_FLASH:
            self.gpio.set_flash(False)
        
        if image_base64 is None:
            logger.error("Failed to capture image")
            return False
        
        # Try local QR decoding first (faster)
        if Config.ENABLE_LOCAL_QR and CV2_AVAILABLE:
            image = self.camera.capture_image()
            if image is not None:
                qr_data = self.qr_handler.decode_qr_local(image)
                
                if qr_data:
                    # Validate hash locally
                    if self.qr_handler.validate_qr_hash(qr_data):
                        self.qr_validated = True
                        self.gpio.blink_led(Config.STATUS_LED, times=2, delay=0.1)
                        return True
        
        # Send to cloud for validation
        success, message = self.api_client.verify_qr_code(image_base64)
        
        if success:
            self.qr_validated = True
            self.gpio.blink_led(Config.STATUS_LED, times=2, delay=0.1)
        
        return success
    
    def scan_face(self):
        """Capture and recognize face"""
        logger.info("📷 Capturing face for recognition...")
        
        # Wait a moment for person to position
        time.sleep(Config.FACE_CAPTURE_DELAY)
        
        # Enable flash if needed
        if Config.ENABLE_FLASH:
            self.gpio.set_flash(True)
            time.sleep(0.1)
        
        # Capture image
        image_base64 = self.camera.capture_and_encode_base64()
        
        if Config.ENABLE_FLASH:
            self.gpio.set_flash(False)
        
        if image_base64 is None:
            logger.error("Failed to capture face image")
            return False, None
        
        # Send to cloud for recognition
        success, name, confidence = self.api_client.recognize_face(image_base64)
        
        return success, name
    
    def open_door(self, person_name=None):
        """Unlock door temporarily"""
        logger.info(f"🔓 ACCESS GRANTED for {person_name or 'User'}")
        
        # Visual feedback
        self.gpio.set_status_led(True)
        
        # Unlock door
        self.gpio.unlock_door()
        
        # Keep door open for configured time
        logger.info(f"Door will remain open for {Config.DOOR_OPEN_TIME} seconds...")
        time.sleep(Config.DOOR_OPEN_TIME)
        
        # Lock door
        self.gpio.lock_door()
        self.gpio.set_status_led(False)
        
        logger.info("Door locked again - Ready for next scan")
    
    def access_denied(self, reason="Unknown"):
        """Handle access denial"""
        logger.warning(f"🔒 ACCESS DENIED: {reason}")
        
        # Visual feedback
        self.gpio.blink_led(Config.ERROR_LED, times=3, delay=0.3)
    
    def run(self):
        """Main system loop"""
        if not self.initialize():
            return
        
        last_qr_scan = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # QR Code Scanning Phase
                if not self.qr_validated:
                    if current_time - last_qr_scan >= Config.QR_SCAN_INTERVAL:
                        last_qr_scan = current_time
                        
                        if self.scan_qr_code():
                            logger.info("✓ QR Code validated - Proceeding to face scan")
                            self.qr_validated = True
                        else:
                            # Blink error LED briefly
                            self.gpio.set_error_led(True)
                            time.sleep(0.1)
                            self.gpio.set_error_led(False)
                
                # Face Scanning Phase
                elif self.qr_validated:
                    success, person_name = self.scan_face()
                    
                    if success and person_name:
                        self.open_door(person_name)
                    else:
                        self.access_denied("Face not recognized")
                    
                    # Reset for next scan
                    self.qr_validated = False
                    time.sleep(Config.FACE_SCAN_INTERVAL)
                
                # Small delay to prevent CPU hogging
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup all resources"""
        logger.info("Shutting down system...")
        self.camera.cleanup()
        self.gpio.cleanup()
        logger.info("System shutdown complete")

# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point"""
    
    # Check if running as root (needed for GPIO)
    if GPIO_AVAILABLE and os.geteuid() != 0:
        logger.warning("⚠ Warning: Not running as root. GPIO may not work.")
        logger.warning("   Run with: sudo python3 raspberry_pi_door_lock.py")
    
    # Create and run door lock system
    door_lock = DoorLockSystem()
    door_lock.run()

if __name__ == "__main__":
    main()
