# 🚀 GitHub Repository Setup Instructions

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Fill in the details:
   - **Repository name:** `Lock-Cloud`
   - **Description:** `Cloud-based Face Recognition & QR Code Door Lock System for ESP32-CAM with Railway deployment`
   - **Visibility:** Public (or Private if preferred)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

3. Click **"Create repository"**

## Step 2: Push Your Code

After creating the repository, run these commands in PowerShell:

```powershell
cd "d:\LOCK CLOUD\Lock-Cloud-Railway"

# Add your GitHub username to the URL below
git remote add origin https://github.com/YOUR_USERNAME/Lock-Cloud.git

# Rename branch to main (GitHub standard)
git branch -M main

# Push to GitHub
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 3: Configure Railway Deployment

1. Go to [Railway](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose **"Lock-Cloud"** repository
5. Add environment variables (see below)

## Environment Variables for Railway

Add these in Railway Dashboard → Variables tab:

```
MONGO_URI=mongodb+srv://your_username:your_password@cluster.mongodb.net/
QR_HASH=7eb04163ef896754651041b69afe0bb9a45eb932faa787d3e93a262f7e074186
ADMIN_PHONE=+917889273694
ENABLE_WHATSAPP=false
```

## Step 4: Deploy!

Railway will automatically:
- Detect Python application
- Install dependencies from requirements.txt
- Use runtime.txt for Python version
- Start server with Procfile configuration

## 🎉 You're Done!

Your Railway URL will be: `https://your-app-name.railway.app`

Test it:
```bash
curl https://your-app-name.railway.app/api/status
```

---

## Alternative: Using Git Commands with Personal Access Token

If you want to push via command line:

1. Create a [Personal Access Token](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `workflow`
   - Copy the token

2. Push using token:
```powershell
cd "d:\LOCK CLOUD\Lock-Cloud-Railway"
git remote add origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/Lock-Cloud.git
git branch -M main
git push -u origin main
```

---

## Need Help?

- Check [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md) for detailed instructions
- See [README.md](README.md) for project overview
- Review [DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md) for quick reference
