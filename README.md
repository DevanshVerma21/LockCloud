# 🔐 Lock Cloud - ESP32-CAM Door Lock System

> Cloud-based Face Recognition & QR Code Door Lock System powered by ESP32-CAM, Flask, and MongoDB Atlas

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

## 🌟 Features

- 🎯 **Face Recognition** - Advanced AI-powered face recognition using deep learning
- 📱 **QR Code Authentication** - Secure QR code verification with SHA-256 hashing
- ☁️ **Cloud-Ready** - Deploy instantly on Railway with MongoDB Atlas
- 🔔 **WhatsApp Notifications** - Optional access alerts via WhatsApp (using PyWhatKit)
- 📊 **Access Logs** - Complete audit trail stored in MongoDB
- 🚀 **REST API** - Clean API for ESP32-CAM integration
- 🔒 **Secure** - Encrypted connections, environment-based configuration

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  ESP32-CAM  │─────>│  Railway Cloud   │─────>│  MongoDB Atlas  │
│             │      │  (Flask Server)  │      │  (Database)     │
└─────────────┘      └──────────────────┘      └─────────────────┘
     Capture              Process                   Store
     Image               Face/QR                    Data
```

## 📁 Project Structure

```
Lock-Cloud-Railway/
├── cloud_server.py              # Main Flask application
├── mongo_config.py              # MongoDB configuration & operations
├── upload_to_cloud.py           # Upload face dataset to MongoDB
├── test_mongo_connection.py    # Test MongoDB connection
├── view_mongodb_data.py         # View stored data in MongoDB
├── Procfile                     # Railway deployment configuration
├── railway.json                 # Railway-specific settings
├── runtime.txt                  # Python version specification
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
├── RAILWAY_DEPLOYMENT_GUIDE.md  # Complete deployment guide
├── DEPLOYMENT_QUICK_START.md    # Quick start reference
└── dataset/                     # Face training images (local only)
    └── .gitkeep
```

## 🚀 Quick Start - Deploy in 5 Minutes

### Prerequisites

- [Railway Account](https://railway.app) (free tier available)
- [MongoDB Atlas Account](https://cloud.mongodb.com) (free tier available)
- ESP32-CAM hardware (for door lock integration)

### 1️⃣ Set Up MongoDB Atlas

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free cluster (M0 Sandbox)
3. Create database user with password
4. Set Network Access to `0.0.0.0/0` (allow from anywhere)
5. Get your connection string: `mongodb+srv://username:password@cluster.mongodb.net/`

### 2️⃣ Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click "Deploy on Railway" or go to [railway.app](https://railway.app)
2. Create new project from GitHub repository
3. Add environment variables:

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
QR_HASH=your_sha256_hash_here
ADMIN_PHONE=+919876543210
ENABLE_WHATSAPP=false
```

4. Deploy! Railway will build and start your server automatically.

### 3️⃣ Upload Face Data

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Lock-Cloud.git
cd Lock-Cloud

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your MongoDB URI

# Add face images to dataset folder
mkdir dataset/PersonName
# Add JPG/PNG images to the folder

# Upload to MongoDB
python upload_to_cloud.py
```

### 4️⃣ Test Deployment

```bash
curl https://your-app.railway.app/api/status
```

Expected response:
```json
{
  "status": "online",
  "message": "ESP32-CAM Door Lock Server is running",
  "timestamp": "2026-02-04 15:30:45",
  "faces_loaded": 3
}
```

## 🔌 API Endpoints

### Check Server Status
```http
GET /api/status
```

### Verify QR Code
```http
POST /api/verify-qr
Content-Type: application/json

{
  "image": "base64_encoded_image_data"
}
```

**Response:**
```json
{
  "success": true,
  "message": "QR code verified successfully"
}
```

### Recognize Face
```http
POST /api/recognize-face
Content-Type: application/json

{
  "image": "base64_encoded_image_data"
}
```

**Response:**
```json
{
  "success": true,
  "name": "John Doe",
  "confidence": 0.95
}
```

### Reload Face Encodings
```http
POST /api/reload-encodings
```

### Get Access Logs
```http
GET /api/logs
```

## 🔐 Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MONGO_URI` | ✅ Yes | MongoDB Atlas connection string | `mongodb+srv://...` |
| `QR_HASH` | ✅ Yes | SHA-256 hash of your QR code | `7eb04163ef8...` |
| `ADMIN_PHONE` | ⚠️ Optional | Phone number for notifications | `+919876543210` |
| `ENABLE_WHATSAPP` | ⚠️ Optional | Enable WhatsApp alerts | `true` or `false` |
| `PORT` | ❌ No | Auto-assigned by Railway | - |

### Generate QR Hash

```bash
python -c "import hashlib; print(hashlib.sha256(b'YourSecretText').hexdigest())"
```

## 📊 MongoDB Collections

The system uses three collections:

- **users** - Store user information
- **face_encodings** - Store face recognition data
- **access_logs** - Store access attempts and events

## 🛠️ Local Development

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/Lock-Cloud.git
cd Lock-Cloud

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env
# Edit .env with your credentials

# Run server
python cloud_server.py
```

Server will start on `http://localhost:5000`

## 🔧 Troubleshooting

### Build Failed
- Check `requirements.txt` for correct package versions
- Verify Python version in `runtime.txt` matches Railway support

### MongoDB Connection Failed
- Verify `MONGO_URI` is correct
- Check IP whitelist includes `0.0.0.0/0`
- Confirm database user has read/write permissions

### Face Recognition Not Working
- Ensure face data is uploaded to MongoDB
- Check `/api/status` shows `faces_loaded > 0`
- Verify images are clear and contain visible faces

### ESP32 Can't Connect
- Update ESP32 code with correct Railway URL
- Check ESP32 has internet connection
- Verify no firewall blocking requests

## 📚 Documentation

- **[Railway Deployment Guide](RAILWAY_DEPLOYMENT_GUIDE.md)** - Detailed step-by-step deployment
- **[Quick Start Guide](DEPLOYMENT_QUICK_START.md)** - Commands and checklists
- **[API Documentation](#-api-endpoints)** - Complete API reference

## 🔒 Security Best Practices

1. ✅ Never commit `.env` file
2. ✅ Use strong MongoDB passwords
3. ✅ Change default QR hash
4. ✅ Enable admin password for production
5. ✅ Restrict MongoDB IP after testing
6. ✅ Monitor access logs regularly
7. ✅ Keep dependencies updated

## 💰 Cost

**Free Tier Included:**
- **Railway**: $5 credit/month (~500 hours runtime)
- **MongoDB Atlas**: 512MB storage (good for hundreds of faces)

Perfect for personal projects and small deployments!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Face recognition powered by [face_recognition](https://github.com/ageitgey/face_recognition)
- Cloud deployment on [Railway](https://railway.app)
- Database hosted on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/Lock-Cloud/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/Lock-Cloud/discussions)

---

**Made with ❤️ for secure access control**

**Last Updated:** February 4, 2026  
**Version:** 2.0.0  
**Status:** Production Ready ✅
