# 🚀 Quick Start Guide - Raspberry Pi Door Lock System

Get your door lock system running in **3 simple steps**!

---

## ⚡ Step 1: Deploy Cloud Server (5 minutes)

### From your Windows laptop:

```bash
# Open PowerShell in the project directory
cd "d:\LOCK CLOUD\Lock-Cloud-Railway"

# Install Railway CLI (one time only)
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy to Railway
railway up
```

### Set environment variables in Railway dashboard:

1. Go to https://railway.app/dashboard
2. Select your project
3. Go to "Variables" tab
4. Add:
   - `MONGO_URI` = Your MongoDB connection string
   - `QR_HASH` = `7eb04163ef896754651041b69afe0bb9a45eb932faa787d3e93a262f7e074186`

5. Copy your Railway URL (e.g., `https://web-production-xxxxx.up.railway.app`)

✅ **Cloud server is now live!**

---

## 📡 Step 2: Setup Raspberry Pi (10 minutes)

### Prerequisites:
- Raspberry Pi with OS installed
- Pi connected to your network
- SSH enabled on Pi
- Pi Camera connected

### From your Windows laptop:

```bash
# Run the deployment script
deploy_to_pi.bat
```

**Enter when prompted:**
- Pi username (default: `pi`)
- Pi IP address (find it from your router)

**Files will be automatically transferred to your Pi.**

### Connect to your Pi:

```bash
ssh pi@<your-pi-ip-address>
```

### Run the installer:

```bash
cd ~/door_lock
sudo bash install_pi.sh
```

**Follow the prompts:**
- Enter your Railway URL (from Step 1)
- Press Enter for default QR hash (or enter custom)

**The installer will:**
- Install all dependencies
- Configure the camera
- Setup systemd service
- Create log files

✅ **Raspberry Pi is now configured!**

---

## 🧪 Step 3: Test & Start (5 minutes)

### Test the system manually:

```bash
sudo python3 raspberry_pi_door_lock.py
```

**You should see:**
```
============================================================
Raspberry Pi Door Lock System - Starting
============================================================

✓ GPIO initialized successfully
✓ Camera initialized successfully
✓ Cloud server is reachable
============================================================
✓ System Ready - Waiting for QR codes...
✓ Cloud Server: https://web-production-xxxxx.up.railway.app
✓ Auto Scan: Enabled
============================================================
```

**Press Ctrl+C to stop the test.**

### Start the service:

```bash
sudo systemctl start door_lock
sudo systemctl enable door_lock
```

### Check status:

```bash
sudo systemctl status door_lock
```

Should show:
```
● door_lock.service - Raspberry Pi Door Lock System
   Loaded: loaded
   Active: active (running)
```

✅ **System is running!**

---

## 🎯 How to Use

### Normal Operation:

1. **Show QR code** to the camera
2. **Wait for green LED** blink (QR validated)
3. **Show your face** to the camera
4. **Door unlocks** automatically if face recognized
5. **Wait 5 seconds** - door locks automatically

### Monitor the system:

```bash
# View live logs
sudo tail -f /var/log/door_lock.log

# Or using journalctl
sudo journalctl -u door_lock -f
```

---

## 🎨 Hardware Wiring (Quick Reference)

| Component | GPIO Pin | Physical Pin |
|-----------|----------|--------------|
| **Relay (Door Lock)** | GPIO 17 | Pin 11 |
| **Status LED (Green)** | GPIO 27 | Pin 13 |
| **Error LED (Red)** | GPIO 22 | Pin 15 |
| **Flash LED (Optional)** | GPIO 23 | Pin 16 |

**Power:**
- Raspberry Pi: 5V 2.5A (micro-USB)
- Solenoid Lock: 12V 1A

**⚠️ Important: Connect all grounds together!**

---

## 🔧 Common Issues & Quick Fixes

### 1. Camera not working

```bash
# Enable camera
sudo raspi-config
# → Interface Options → Camera → Enable → Reboot

# Test camera
libcamera-hello
```

### 2. GPIO permission denied

```bash
# Always run as root
sudo python3 raspberry_pi_door_lock.py

# Or for service
sudo systemctl restart door_lock
```

### 3. Can't connect to cloud server

```bash
# Test connectivity
ping google.com
curl https://your-railway-url.app/api/status

# Check configuration
cat /etc/door_lock.env

# Update if needed
sudo nano /etc/door_lock.env
```

### 4. Service won't start

```bash
# Check logs
sudo journalctl -u door_lock -n 50

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart door_lock
```

### 5. Face not recognized

- Ensure you've uploaded face dataset to cloud
- Good lighting is essential
- Face should be clearly visible
- Reload face encodings on server

---

## 📊 Useful Commands

```bash
# Start service
sudo systemctl start door_lock

# Stop service
sudo systemctl stop door_lock

# Restart service
sudo systemctl restart door_lock

# Check status
sudo systemctl status door_lock

# View logs (live)
sudo tail -f /var/log/door_lock.log

# View logs (last 50 lines)
sudo journalctl -u door_lock -n 50

# Test manually
sudo python3 ~/door_lock/raspberry_pi_door_lock.py

# Reboot Pi
sudo reboot
```

---

## 📱 Upload Face Dataset

To add faces for recognition:

### Method 1: Direct upload to cloud

```bash
# On your laptop (in Lock-Cloud-Railway directory)
python3 upload_to_cloud.py
```

### Method 2: Add to dataset folder

1. Create folder: `dataset/PersonName/`
2. Add 5-10 photos of the person
3. Deploy to Railway:

```bash
railway up
```

4. Reload encodings:

```bash
curl -X POST https://your-railway-url.app/api/reload-encodings
```

---

## 🎉 That's It!

Your door lock system is now **fully operational**! 

### What you have:
- ✅ Cloud-connected door lock
- ✅ QR code validation
- ✅ Face recognition
- ✅ Automatic door control
- ✅ Real-time logging
- ✅ Auto-start on boot

### Next steps:
- Add more faces to the dataset
- Monitor the logs regularly
- Customize timing settings
- Add more LEDs for better feedback
- Integrate with home automation

---

## 📚 Full Documentation

For detailed information, see:

- **[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md)** - Complete Pi guide
- **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** - Cloud deployment
- **[README_SYSTEM.md](README_SYSTEM.md)** - System overview
- **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** - Architecture details

---

## 🆘 Need Help?

1. Check the troubleshooting sections in documentation
2. Review logs: `sudo journalctl -u door_lock -f`
3. Test components individually
4. Ensure good lighting for camera
5. Verify cloud server is running

---

## 🎊 Congratulations!

You've successfully set up a professional-grade door lock system using Raspberry Pi and cloud technology!

**Enjoy your smart door lock! 🚪✨🔒**

---

*Setup time: ~20 minutes | Difficulty: Beginner-friendly*
