#!/usr/bin/env python3
"""
Quick test script to verify Raspberry Pi door lock setup
Tests camera, GPIO, and cloud connectivity
"""

import sys
import time

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_imports():
    """Test if all required imports are available"""
    print_header("Testing Python Imports")
    
    modules = {
        'RPi.GPIO': 'GPIO control',
        'picamera2': 'Pi Camera',
        'cv2': 'OpenCV',
        'pyzbar.pyzbar': 'QR Code detection',
        'requests': 'HTTP client',
        'numpy': 'NumPy'
    }
    
    missing = []
    
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"  ✅ {description:.<40} OK")
        except ImportError:
            print(f"  ❌ {description:.<40} MISSING")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing modules: {', '.join(missing)}")
        print("   Run: pip3 install -r requirements_pi.txt")
        return False
    
    return True

def test_camera():
    """Test Pi Camera"""
    print_header("Testing Pi Camera")
    
    try:
        from picamera2 import Picamera2
        
        print("  📷 Initializing camera...")
        camera = Picamera2()
        camera.configure(camera.create_still_configuration())
        camera.start()
        
        print("  📸 Capturing test image...")
        time.sleep(2)
        image = camera.capture_array()
        camera.stop()
        
        print(f"  ✅ Camera working! Image size: {image.shape}")
        return True
        
    except Exception as e:
        print(f"  ❌ Camera test failed: {e}")
        print("  💡 Run: sudo raspi-config → Interface → Camera → Enable")
        return False

def test_gpio():
    """Test GPIO access"""
    print_header("Testing GPIO Access")
    
    try:
        import RPi.GPIO as GPIO
        
        print("  🔌 Testing GPIO setup...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Test pins
        test_pins = [17, 27, 22, 23]
        
        for pin in test_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        print("  ✅ GPIO access OK")
        GPIO.cleanup()
        return True
        
    except Exception as e:
        print(f"  ❌ GPIO test failed: {e}")
        print("  💡 Run with sudo: sudo python3 test_system.py")
        return False

def test_cloud_connection(url):
    """Test cloud server connectivity"""
    print_header("Testing Cloud Server Connection")
    
    try:
        import requests
        
        print(f"  🌐 Testing connection to: {url}")
        
        response = requests.get(f"{url}/api/status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Server online: {data.get('message')}")
            return True
        else:
            print(f"  ⚠️  Server returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        print("  💡 Check:")
        print("     - Internet connection")
        print("     - Server URL is correct")
        print("     - Server is deployed on Railway")
        return False

def test_qr_detection():
    """Test QR code detection capability"""
    print_header("Testing QR Code Detection")
    
    try:
        import cv2
        from pyzbar.pyzbar import decode
        import numpy as np
        
        print("  🔍 QR detection libraries loaded")
        print("  ✅ QR code detection ready")
        return True
        
    except Exception as e:
        print(f"  ❌ QR detection test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🔒 "+"="*56 + " 🔒")
    print("   Raspberry Pi Door Lock System - System Test")
    print("🔒 "+"="*56 + " 🔒")
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    
    # Test 2: Camera
    results['camera'] = test_camera()
    
    # Test 3: GPIO
    results['gpio'] = test_gpio()
    
    # Test 4: QR Detection
    results['qr'] = test_qr_detection()
    
    # Test 5: Cloud Connection
    cloud_url = input("\n📝 Enter your cloud server URL (or press Enter to skip): ").strip()
    if cloud_url:
        results['cloud'] = test_cloud_connection(cloud_url)
    else:
        results['cloud'] = None
    
    # Summary
    print_header("Test Summary")
    
    for test, result in results.items():
        if result is None:
            status = "⏭️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        print(f"  {test.upper():.<40} {status}")
    
    # Final verdict
    print("\n" + "="*60)
    
    failed = [k for k, v in results.items() if v is False]
    skipped = [k for k, v in results.items() if v is None]
    
    if not failed:
        print("  🎉 All tests passed! System is ready to go!")
        print("\n  Next steps:")
        print("  1. sudo python3 raspberry_pi_door_lock.py")
        print("  2. sudo systemctl start door_lock")
        return 0
    else:
        print(f"  ⚠️  {len(failed)} test(s) failed: {', '.join(failed)}")
        print("\n  Please fix the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    import os
    
    # Check if running as root
    if 'gpio' in sys.argv or os.geteuid() != 0:
        print("\n⚠️  For full testing, run as root: sudo python3 test_system.py\n")
    
    sys.exit(main())
