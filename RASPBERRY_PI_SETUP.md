# Raspberry Pi Zero 2 W Door Lock System
## Complete Setup and Configuration Guide

This guide will help you set up your Raspberry Pi Zero 2 W as a QR code and face recognition door lock system connected to your cloud server on Railway.

---

## 📋 Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [System Architecture](#system-architecture)
3. [Quick Start Guide](#quick-start-guide)
4. [Detailed Installation](#detailed-installation)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Cloud Server Deployment](#cloud-server-deployment)

---

## 🛠 Hardware Requirements

### Required Components:

1. **Raspberry Pi Zero 2 W** (or any Raspberry Pi model)
2. **Pi Camera Module** (v1, v2, or HQ Camera)
3. **5V Relay Module** (1-channel)
4. **12V DC Solenoid Door Lock**
5. **Power Supplies:**
   - 5V 2.5A for Raspberry Pi
   - 12V 1A for Solenoid Lock
6. **Optional:**
   - Status LEDs (Green and Red)
   - Flash LED for low-light conditions
   - Jumper wires and breadboard

### GPIO Connections:

| Component | GPIO Pin (BCM) | Physical Pin |
|-----------|----------------|--------------|
| Relay (Door Lock) | GPIO 17 | Pin 11 |
| Status LED (Green) | GPIO 27 | Pin 13 |
| Error LED (Red) | GPIO 22 | Pin 15 |
| Flash LED (Optional) | GPIO 23 | Pin 16 |

**Important:** All grounds must be connected together (common ground).

---

## 🏗 System Architecture

```
┌─────────────────┐
│  User Shows QR  │
└────────┬────────┘
         │
┌────────▼────────────┐
│  Raspberry Pi       │
│  - Captures Image   │
│  - Local QR Decode  │
└────────┬────────────┘
         │ WiFi/HTTPS
┌────────▼────────────┐
│  Cloud Server       │
│  (Railway)          │
│  - Validates QR     │
│  - Returns Session  │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Raspberry Pi       │
│  - Captures Face    │
└────────┬────────────┘
         │ WiFi/HTTPS
┌────────▼────────────┐
│  Cloud Server       │
│  - Recognizes Face  │
│  - Returns Name     │
└────────┬────────────┘
         │
┌────────▼────────────┐
│  Raspberry Pi       │
│  - Unlocks Door     │
│  - Waits 5 seconds  │
│  - Locks Door       │
└─────────────────────┘
```

---

## 🚀 Quick Start Guide

### From Your Windows Laptop:

1. **Download all files to your laptop**
2. **Connect to your Raspberry Pi's network or ensure it's on the same network**
3. **Find your Pi's IP address** (check your router or use `ping raspberrypi.local`)
4. **Run the deployment script:**

```bash
deploy_to_pi.bat
```

5. **Follow the prompts to enter:**
   - Pi username (default: `pi`)
   - Pi IP address (e.g., `192.168.1.100`)

6. **SSH into your Raspberry Pi:**

```bash
ssh pi@<your-pi-ip-address>
```

7. **Navigate to the door_lock directory:**

```bash
cd ~/door_lock
```

8. **Run the installation script:**

```bash
sudo bash install_pi.sh
```

9. **Follow the installation prompts**

10. **Test the system:**

```bash
sudo python3 raspberry_pi_door_lock.py
```

---

## 📥 Detailed Installation

### Step 1: Prepare Your Raspberry Pi

1. **Flash Raspberry Pi OS** (Lite or Desktop) to your SD card
2. **Enable SSH** (create empty `ssh` file in boot partition)
3. **Configure WiFi** (create `wpa_supplicant.conf` in boot partition):

```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourWiFiName"
    psk="YourWiFiPassword"
}
```

4. **Boot your Pi and connect via SSH**

### Step 2: Transfer Files

**Option A - Using the batch script (Windows):**
```bash
deploy_to_pi.bat
```

**Option B - Manual transfer:**
```bash
scp raspberry_pi_door_lock.py pi@<pi-ip>:~/door_lock/
scp requirements_pi.txt pi@<pi-ip>:~/door_lock/
scp install_pi.sh pi@<pi-ip>:~/door_lock/
scp door_lock.service pi@<pi-ip>:~/door_lock/
```

### Step 3: Run Installation

SSH into your Pi and run:

```bash
cd ~/door_lock
sudo bash install_pi.sh
```

The installer will:
- Update system packages
- Install all dependencies
- Configure the camera
- Set up environment variables
- Install systemd service
- Create log files

### Step 4: Hardware Setup

1. **Connect the camera module** to the Pi's camera port
2. **Wire the GPIO pins** according to the table above
3. **Connect power supplies**:
   - Pi: 5V 2.5A via micro-USB
   - Solenoid: 12V 1A
4. **Ensure common ground** between all components

---

## ⚙️ Configuration

### Environment Variables

Edit `/etc/door_lock.env`:

```bash
sudo nano /etc/door_lock.env
```

Configure:

```bash
# Cloud Server URL (your Railway deployment)
CLOUD_SERVER_URL=https://your-server.railway.app

# QR Code Hash (must match the QR code you're using)
QR_HASH=7eb04163ef896754651041b69afe0bb9a45eb932faa787d3e93a262f7e074186
```

### System Configuration

Edit `raspberry_pi_door_lock.py` to customize:

```python
class Config:
    # Timing
    DOOR_OPEN_TIME = 5           # Seconds door stays unlocked
    QR_SCAN_INTERVAL = 2         # QR scan frequency
    FACE_SCAN_INTERVAL = 2.5     # Face scan frequency
    
    # Camera
    CAMERA_WIDTH = 640           # Resolution
    CAMERA_HEIGHT = 480
    JPEG_QUALITY = 85            # Image quality (0-100)
    
    # Features
    ENABLE_LOCAL_QR = True       # Decode QR locally
    ENABLE_FLASH = False         # Use flash LED
    AUTO_SCAN_ENABLED = True     # Auto scanning mode
```

---

## 🧪 Testing

### Manual Test

Test the system manually:

```bash
sudo python3 raspberry_pi_door_lock.py
```

**Expected output:**
```
============================================================
Raspberry Pi Door Lock System - Starting
============================================================

✓ GPIO initialized successfully
✓ Camera initialized successfully
✓ Cloud server is reachable
============================================================
✓ System Ready - Waiting for QR codes...
✓ Cloud Server: https://your-server.railway.app
✓ Auto Scan: Enabled
============================================================

📷 Scanning for QR code...
```

### Service Test

Start the systemd service:

```bash
sudo systemctl start door_lock
sudo systemctl status door_lock
```

View logs:

```bash
sudo tail -f /var/log/door_lock.log
```

Or using journalctl:

```bash
sudo journalctl -u door_lock -f
```

### Enable Auto-Start on Boot

```bash
sudo systemctl enable door_lock
```

---

## 🔧 Troubleshooting

### Camera Not Working

```bash
# Check if camera is detected
vcgencmd get_camera

# Should output: supported=1 detected=1

# Enable camera interface
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable
```

### GPIO Permission Issues

```bash
# Add user to gpio group
sudo usermod -a -G gpio pi

# Or run as root
sudo python3 raspberry_pi_door_lock.py
```

### Cloud Server Connection Failed

```bash
# Test connectivity
curl https://your-server.railway.app/api/status

# Check DNS
ping your-server.railway.app

# Check environment variable
cat /etc/door_lock.env
```

### QR Code Not Detected

- Ensure good lighting
- Hold QR code steady
- Adjust camera focus if using HQ camera
- Check QR code hash matches in cloud server
- Enable flash LED: `ENABLE_FLASH = True`

### Face Recognition Fails

- Ensure face dataset is uploaded to cloud server
- Good lighting is essential
- Face should be clearly visible (not too far)
- Check cloud server logs

### Service Won't Start

```bash
# Check service status
sudo systemctl status door_lock

# View detailed logs
sudo journalctl -xe -u door_lock

# Check file permissions
ls -la ~/door_lock/

# Reload systemd
sudo systemctl daemon-reload
```

---

## ☁️ Cloud Server Deployment (Railway)

Your cloud server is already set up at `Lock-Cloud-Railway`. To deploy or update:

### Verify Files for Railway

Ensure these files exist in `Lock-Cloud-Railway/`:

- ✅ `cloud_server.py` - Main server application
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Railway startup command
- ✅ `runtime.txt` - Python version
- ✅ `railway.json` - Railway configuration
- ✅ `mongo_config.py` - MongoDB configuration
- ✅ `dataset/` - Face recognition training data

### Deploy to Railway

1. **Install Railway CLI** (if not already):

```bash
npm install -g @railway/cli
```

2. **Login to Railway:**

```bash
railway login
```

3. **Navigate to your cloud server directory:**

```bash
cd "d:\LOCK CLOUD\Lock-Cloud-Railway"
```

4. **Link to your Railway project:**

```bash
railway link
```

5. **Deploy:**

```bash
railway up
```

6. **Set environment variables in Railway dashboard:**

- `MONGO_URI` - Your MongoDB connection string
- `QR_HASH` - QR code hash (must match Pi configuration)
- `ADMIN_PHONE` - Optional WhatsApp notification number

### Test Cloud Server

```bash
# Check server status
curl https://your-server.railway.app/api/status

# Should return:
# {"status":"online","message":"Cloud server is running"}
```

### Upload Face Dataset

Upload training images to the cloud server:

```bash
python3 upload_to_cloud.py
```

Or manually place images in `dataset/` folder:
```
dataset/
  ├── Person1/
  │   ├── image1.jpg
  │   ├── image2.jpg
  │   └── image3.jpg
  ├── Person2/
  │   ├── image1.jpg
  │   └── image2.jpg
```

Then redeploy to Railway.

---

## 📊 System Monitoring

### Real-Time Logs

```bash
# On Raspberry Pi
sudo tail -f /var/log/door_lock.log

# Or using journalctl
sudo journalctl -u door_lock -f --since "5 minutes ago"
```

### System Status

```bash
# Check service status
sudo systemctl status door_lock

# Check if script is running
ps aux | grep raspberry_pi_door_lock

# Check GPIO states
gpio readall
```

### Performance Monitoring

```bash
# CPU and Memory usage
top -u root

# Temperature
vcgencmd measure_temp

# Storage space
df -h
```

---

## 🔒 Security Best Practices

1. **Change default Pi password:**
```bash
passwd
```

2. **Use SSH keys instead of password**
3. **Keep system updated:**
```bash
sudo apt update && sudo apt upgrade
```

4. **Use HTTPS for cloud communication** (already configured)
5. **Secure your WiFi network**
6. **Regularly update QR code hash**
7. **Monitor access logs**

---

## 📱 Integration with Existing System

This Raspberry Pi system is fully compatible with your existing architecture and follows the same flowchart:

1. ✅ QR Code validation (local + cloud)
2. ✅ Face recognition (cloud-based)
3. ✅ Door lock control
4. ✅ Session management
5. ✅ MongoDB integration
6. ✅ Access logging

The system seamlessly replaces the ESP32-CAM with more powerful hardware while maintaining the same API and workflow.

---

## 🆘 Support

### Useful Commands Reference

```bash
# Start service
sudo systemctl start door_lock

# Stop service
sudo systemctl stop door_lock

# Restart service
sudo systemctl restart door_lock

# Enable auto-start
sudo systemctl enable door_lock

# Disable auto-start
sudo systemctl disable door_lock

# View logs
sudo journalctl -u door_lock -n 50

# Test manually
sudo python3 ~/door_lock/raspberry_pi_door_lock.py

# Check network
ping google.com
ping your-server.railway.app

# Check camera
libcamera-hello

# Reboot Pi
sudo reboot
```

---

## 📝 Notes

- The system automatically handles network disconnections and reconnections
- Local QR decoding reduces latency and server load
- Face recognition is always performed on the cloud for accuracy
- Logs are stored both locally and in MongoDB (if configured)
- The system locks the door by default on startup for safety

---

## 🎉 Success!

Once everything is set up, your door lock system will:

1. 🔍 Automatically scan for QR codes every 2 seconds
2. ✅ Validate QR codes (locally and with cloud)
3. 📸 Capture face image after valid QR
4. 🧠 Send face to cloud for recognition
5. 🔓 Unlock door for recognized faces
6. ⏱️ Keep door open for 5 seconds
7. 🔒 Lock door automatically
8. 🔄 Ready for next scan

Enjoy your automated door lock system! 🚪✨
