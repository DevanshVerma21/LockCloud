# Railway Deployment Checklist for Raspberry Pi Door Lock System

## ✅ Pre-Deployment Checklist

### Files Required:
- [x] `cloud_server.py` - Main Flask application
- [x] `requirements.txt` - Python dependencies
- [x] `Procfile` - Gunicorn startup command
- [x] `runtime.txt` - Python version specification
- [x] `railway.json` - Railway configuration
- [x] `mongo_config.py` - MongoDB connection handler
- [x] `dataset/` - Face recognition training images

### Configuration Status:
- [x] Port configured from environment variable
- [x] MongoDB connection via environment variable
- [x] Base64 image encoding/decoding
- [x] CORS headers (if needed)
- [x] Error handling and logging
- [x] Headless OpenCV (opencv-python-headless)
- [x] Production-ready with Gunicorn

---

## 🚀 Deployment Steps

### 1. Verify All Files

```bash
cd "d:\LOCK CLOUD\Lock-Cloud-Railway"
ls
```

Expected files:
```
cloud_server.py
requirements.txt
Procfile
runtime.txt
railway.json
mongo_config.py
raspberry_pi_door_lock.py
requirements_pi.txt
install_pi.sh
deploy_to_pi.bat
door_lock.service
dataset/
```

### 2. Check Requirements

Verify `requirements.txt` contains:
```
Flask==3.0.0
opencv-python-headless==4.8.1.78
numpy==1.24.3
face-recognition==1.3.0
pyzbar==0.1.9
gunicorn==21.2.0
pymongo==4.6.0
dnspython==2.4.2
```

### 3. Check Procfile

Should contain:
```
web: gunicorn cloud_server:app --workers 2 --threads 4 --timeout 120
```

### 4. Check runtime.txt

Should specify:
```
python-3.11.6
```

---

## 🔧 Railway Configuration

### Environment Variables to Set in Railway Dashboard:

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/dbname` |
| `QR_HASH` | SHA256 hash of valid QR code | `7eb04163ef896754651041b69afe0bb9a45eb932faa787d3e93a262f7e074186` |
| `ADMIN_PHONE` | WhatsApp notification number (optional) | `+1234567890` |
| `ENABLE_WHATSAPP` | Enable WhatsApp notifications | `false` |
| `PORT` | Server port (auto-set by Railway) | Auto |

---

## 📦 Deployment Commands

### Option 1: Using Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm install -g @railway/cli

# Login
railway login

# Link project (first time only)
railway link

# Deploy
railway up

# Check logs
railway logs

# Check status
railway status
```

### Option 2: Using Git (Recommended)

```bash
# Initialize git if not already
git init

# Add Railway remote (get from Railway dashboard)
git remote add railway your-railway-git-url

# Add all files
git add .

# Commit
git commit -m "Deploy Raspberry Pi door lock system"

# Push to Railway
git push railway main
```

### Option 3: Using GitHub Integration

1. Push your code to GitHub
2. In Railway dashboard, connect your GitHub repository
3. Railway will auto-deploy on every push to main branch

---

## 🧪 Testing After Deployment

### 1. Check Server Status

```bash
curl https://your-app.railway.app/api/status
```

Expected response:
```json
{
  "status": "online",
  "message": "Cloud server is running"
}
```

### 2. Test QR Verification Endpoint

Create a test script:

```python
import requests
import base64

# Load test QR image
with open('test_qr.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Send to server
response = requests.post(
    'https://your-app.railway.app/api/verify-qr',
    json={'image': image_data}
)

print(response.json())
```

### 3. Test Face Recognition Endpoint

```python
import requests
import base64

# Load test face image
with open('test_face.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Send to server
response = requests.post(
    'https://your-app.railway.app/api/recognize-face',
    json={'image': image_data}
)

print(response.json())
```

### 4. Check Logs in Railway

```bash
railway logs
```

Look for:
```
✓ MongoDB connected for cloud deployment
✓ Loaded X face encodings from MongoDB
Server Ready!
Starting server on port 5000...
```

---

## 📊 Monitoring

### View Live Logs

In Railway dashboard:
1. Go to your project
2. Click on "Deployments"
3. Click on latest deployment
4. View logs in real-time

### Check Metrics

Monitor:
- CPU usage
- Memory usage
- Response times
- Error rates

---

## 🔒 Security Checklist

- [ ] MongoDB connection string uses SSL
- [ ] QR_HASH environment variable is set correctly
- [ ] No hardcoded credentials in code
- [ ] HTTPS is enabled (Railway default)
- [ ] Rate limiting configured (if needed)
- [ ] Access logs are being recorded
- [ ] Regular backups of MongoDB data

---

## 🐛 Troubleshooting

### Deployment Fails

**Check build logs:**
```bash
railway logs --deployment
```

**Common issues:**
- Missing dependencies in `requirements.txt`
- Wrong Python version in `runtime.txt`
- Syntax errors in `cloud_server.py`
- Missing environment variables

### Server Starts But Crashes

**Check runtime logs:**
```bash
railway logs
```

**Common issues:**
- MongoDB connection failed (check MONGO_URI)
- Face encodings not loaded (check dataset)
- Port binding issues (Railway sets PORT automatically)

### API Endpoints Return Errors

**Check server logs and test locally:**
```bash
# Run locally
python3 cloud_server.py

# Test endpoint
curl http://localhost:5000/api/status
```

### Raspberry Pi Can't Connect

**Verify:**
1. Railway URL is correct in Pi configuration
2. Railway app is running (check dashboard)
3. Pi has internet connection
4. No firewall blocking requests

**Test from Pi:**
```bash
curl https://your-app.railway.app/api/status
```

---

## 🔄 Updating the Deployment

### Quick Update

```bash
# Make changes to code
# Commit and push
git add .
git commit -m "Update message"
git push railway main
```

### Update Face Dataset

1. Add/remove images in `dataset/` folder
2. Deploy to Railway
3. Call reload endpoint:

```bash
curl -X POST https://your-app.railway.app/api/reload-encodings
```

### Update Environment Variables

1. Go to Railway dashboard
2. Click on your project
3. Go to "Variables"
4. Add/modify variables
5. Redeploy automatically happens

---

## 📈 Performance Optimization

### Current Configuration:
- Workers: 2
- Threads per worker: 4
- Timeout: 120 seconds
- Max concurrent requests: ~8

### To Handle More Traffic:

Update `Procfile`:
```
web: gunicorn cloud_server:app --workers 4 --threads 8 --timeout 120
```

**Note:** More workers = more memory usage. Monitor Railway metrics.

---

## ✅ Raspberry Pi Integration

### Update Pi Configuration

After deploying to Railway, update your Raspberry Pi:

```bash
# SSH into Pi
ssh pi@<pi-ip>

# Edit environment file
sudo nano /etc/door_lock.env

# Update CLOUD_SERVER_URL
CLOUD_SERVER_URL=https://your-new-app.railway.app

# Restart service
sudo systemctl restart door_lock
```

### Verify Connection

```bash
# Check Pi logs
sudo tail -f /var/log/door_lock.log

# Should show:
# ✓ Cloud server is reachable
```

---

## 📝 Post-Deployment Checklist

- [ ] Server accessible via HTTPS
- [ ] Status endpoint returns "online"
- [ ] QR verification endpoint works
- [ ] Face recognition endpoint works
- [ ] MongoDB connection successful
- [ ] Face encodings loaded
- [ ] Raspberry Pi can connect
- [ ] Door lock system operational
- [ ] Logs are being recorded
- [ ] Monitoring is active

---

## 🎉 Success!

If all checks pass, your system is ready:

```
Raspberry Pi → Railway Cloud Server → MongoDB
     ↓              ↓                    ↓
  QR Scan      Validation           Logging
  Face Scan    Recognition          Storage
  Door Control Access Control       History
```

Your door lock system is now cloud-connected and scalable! 🚀🔒

---

## 📞 Support Resources

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- MongoDB Atlas: https://www.mongodb.com/atlas
- Face Recognition Library: https://github.com/ageitgey/face_recognition

---

## 🔗 Quick Links

- Railway CLI: `npm install -g @railway/cli`
- Railway Dashboard: https://railway.app/dashboard
- Project Logs: `railway logs`
- Project Status: `railway status`

**Congratulations on your deployment! 🎊**
