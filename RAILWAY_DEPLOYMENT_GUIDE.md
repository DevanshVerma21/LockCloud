# 🚂 Railway Deployment Guide
## ESP32-CAM Door Lock System - Cloud Server

This guide will help you deploy your ESP32-CAM Door Lock system to Railway in minutes.

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ A Railway account (sign up at [railway.app](https://railway.app))
- ✅ A MongoDB Atlas account (sign up at [cloud.mongodb.com](https://cloud.mongodb.com))
- ✅ Git installed on your computer
- ✅ Your QR code hash ready (see below to generate)

---

## 🗄️ Step 1: Set Up MongoDB Atlas

### 1.1 Create MongoDB Cluster

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Sign in or create a new account (free tier available)
3. Click **"Create"** to create a new cluster
4. Choose **FREE** tier (M0 Sandbox)
5. Select a cloud provider and region (choose closest to you)
6. Click **"Create Cluster"** (takes 3-5 minutes)

### 1.2 Configure Database Access

1. In left sidebar, click **"Database Access"**
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Create username and password (SAVE THESE!)
5. Set privileges to **"Read and write to any database"**
6. Click **"Add User"**

### 1.3 Configure Network Access

1. In left sidebar, click **"Network Access"**
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
4. Click **"Confirm"**

⚠️ **Note:** For production, restrict to Railway's IP addresses

### 1.4 Get Connection String

1. Go back to **"Database"** in left sidebar
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Copy the connection string (looks like: `mongodb+srv://...`)
5. Replace `<password>` with your actual password

Example:
```
mongodb+srv://myuser:MyP@ssw0rd@cluster0.xxxxx.mongodb.net/
```

---

## 🔐 Step 2: Generate QR Code Hash

Your QR code data needs to be hashed for security. Run this Python command:

```bash
python -c "import hashlib; print(hashlib.sha256(b'YOUR_SECRET_TEXT').hexdigest())"
```

Replace `YOUR_SECRET_TEXT` with the data in your physical QR code.

**Example:**
```bash
python -c "import hashlib; print(hashlib.sha256(b'MySecretDoorCode123').hexdigest())"
```

Save this hash - you'll need it for Railway environment variables.

---

## 🚀 Step 3: Deploy to Railway

### 3.1 Push Code to GitHub (if not already done)

```bash
cd "d:\LOCK CLOUD\website lock\website lock\whatsapp lock\QRcode-FaceRecognition-Door-Lock-system-Arduino-IOT-master"
git init
git add .
git commit -m "Initial commit for Railway deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 3.2 Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Choose **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your repository
6. Railway will automatically detect it as a Python app

### 3.3 Configure Environment Variables

After deployment starts, click on your service, then go to **"Variables"** tab:

Add these variables:

| Variable Name | Value | Example |
|--------------|-------|---------|
| `MONGO_URI` | Your MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `QR_HASH` | Your QR code SHA-256 hash | `7eb04163ef896754...` |
| `ADMIN_PHONE` | Your phone with country code | `+917889273694` |
| `ENABLE_WHATSAPP` | `false` (or `true` if needed) | `false` |
| `PORT` | Leave empty (Railway auto-assigns) | - |

**Click "Add" after each variable**

### 3.4 Verify Deployment

1. Click **"Deployments"** tab
2. Wait for build to complete (3-5 minutes)
3. Once deployed, you'll see a URL like: `https://your-app.railway.app`
4. Click **"View Logs"** to check for errors

---

## 🧪 Step 4: Test Your Deployment

### 4.1 Check Server Status

Open your browser or use curl:

```bash
curl https://your-app.railway.app/api/status
```

Expected response:
```json
{
  "status": "online",
  "message": "ESP32-CAM Door Lock Server is running",
  "timestamp": "2026-02-04 15:30:45",
  "faces_loaded": 0
}
```

### 4.2 Upload Face Data

You need to upload face encodings to MongoDB. Use the provided script:

```bash
python capture_new_user.py
```

Or use the API endpoint (see API documentation below).

---

## 📡 Step 5: Connect ESP32-CAM

Update your ESP32 Arduino code with the Railway URL:

```cpp
const char* serverUrl = "https://your-app.railway.app";
```

Update in your `esp32_cam_door_lock.ino` file:
- Line where `serverUrl` is defined
- Replace with your Railway URL

Then re-upload code to ESP32-CAM.

---

## 🔧 Troubleshooting

### Build Failed

**Error:** `Could not find requirement`
- Check [requirements_cloud.txt](requirements_cloud.txt) for typos
- Ensure all dependencies are available

**Error:** `MongoDB connection failed`
- Verify `MONGO_URI` is correct in Railway variables
- Check MongoDB Atlas IP whitelist includes 0.0.0.0/0
- Ensure database user has correct permissions

### Deployment Runs But No Response

- Check Railway logs: `Deployments` → `View Logs`
- Look for startup errors
- Verify `PORT` is not manually set (Railway assigns it)

### Face Recognition Not Working

```bash
# Check if encodings are loaded
curl https://your-app.railway.app/api/status
```

If `faces_loaded: 0`, you need to upload face data to MongoDB.

### ESP32-CAM Can't Connect

- Ensure Railway URL is correct in ESP32 code
- Check ESP32 has internet connection
- Verify no firewall blocking requests
- Check Railway logs for incoming requests

---

## 🔄 Update Deployment

When you make changes:

```bash
git add .
git commit -m "Your update message"
git push
```

Railway will automatically redeploy!

---

## 📊 Monitor Your Application

### View Logs
Railway Dashboard → Your Service → Deployments → View Logs

### Check Metrics
Railway Dashboard → Your Service → Metrics

Shows:
- CPU usage
- Memory usage
- Network traffic
- Request count

---

## 💰 Cost Considerations

**Railway Free Tier:**
- $5 credit per month
- Enough for hobby projects
- ~500 hours of runtime

**MongoDB Atlas Free Tier:**
- 512 MB storage
- Shared CPU
- Good for hundreds of face encodings

**Upgrade if needed:**
- Railway: $5/month for 200 hours
- MongoDB: $9/month for 2GB storage

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** - use `.env.example` instead
2. **Use strong MongoDB passwords** - mix of letters, numbers, symbols
3. **Change default QR hash** - generate unique hash for your system
4. **Enable admin password** - add `ADMIN_PASSWORD` variable in Railway
5. **Restrict MongoDB IP** - after testing, limit to Railway IPs only
6. **Use HTTPS only** - Railway provides this by default

---

## 📞 API Endpoints

Your deployed server exposes these endpoints:

### 1. Check Status
```http
GET /api/status
```

### 2. Verify QR Code
```http
POST /api/verify-qr
Content-Type: application/json

{
  "image": "base64_encoded_image_data"
}
```

### 3. Recognize Face
```http
POST /api/recognize-face
Content-Type: application/json

{
  "image": "base64_encoded_image_data"
}
```

### 4. Reload Encodings
```http
POST /api/reload-encodings
```

### 5. Get Logs (Admin)
```http
GET /api/logs
```

---

## ✅ Deployment Checklist

Use this checklist to ensure everything is set up:

- [ ] MongoDB Atlas cluster created
- [ ] Database user created with password
- [ ] IP whitelist set to 0.0.0.0/0
- [ ] MongoDB connection string obtained
- [ ] QR code hash generated
- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables set in Railway
- [ ] Deployment successful (green check)
- [ ] Server status endpoint returns 200 OK
- [ ] Face data uploaded to MongoDB
- [ ] ESP32-CAM code updated with Railway URL
- [ ] ESP32-CAM successfully connects to server
- [ ] QR code verification works
- [ ] Face recognition works
- [ ] Logs are being recorded

---

## 🎉 Success!

Your ESP32-CAM Door Lock System is now running on Railway with MongoDB!

**Next Steps:**
- Monitor logs for any issues
- Test thoroughly before installing on actual door
- Set up backup MongoDB instance for critical applications
- Consider adding authentication for admin endpoints

**Need Help?**
- Check [README.md](README.md) for general information
- See [ESP32_CAM_SETUP_GUIDE.md](ESP32_CAM_SETUP_GUIDE.md) for hardware setup
- Review [MONGODB_SETUP.md](MONGODB_SETUP.md) for database details

---

## 📝 Notes

- Railway URL: Save your Railway URL for ESP32 configuration
- MongoDB URI: Keep secure, never share publicly
- Logs: Check regularly for unauthorized access attempts
- Backups: Export MongoDB data periodically

**Deployment Date:** February 4, 2026  
**Last Updated:** February 4, 2026
