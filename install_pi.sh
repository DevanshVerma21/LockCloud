#!/bin/bash
# Raspberry Pi Zero 2 W Door Lock System - Installation Script
# This script installs all necessary dependencies and configures the system
# Run with: sudo bash install_pi.sh

set -e  # Exit on error

echo "=========================================="
echo "Raspberry Pi Door Lock System Installer"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo bash install_pi.sh"
    exit 1
fi

echo "✓ Running as root"
echo ""

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-picamera2 \
    libcamera-apps \
    libcamera-dev \
    libopencv-dev \
    libzbar0 \
    libzbar-dev \
    python3-opencv \
    python3-numpy \
    python3-pil \
    git \
    build-essential \
    cmake

echo ""
echo "📦 Installing Python dependencies..."

# Upgrade pip
python3 -m pip install --upgrade pip

# Install Python requirements
if [ -f "requirements_pi.txt" ]; then
    pip3 install -r requirements_pi.txt
else
    echo "⚠ Warning: requirements_pi.txt not found"
    echo "Installing core packages manually..."
    pip3 install requests numpy opencv-python pyzbar RPi.GPIO Pillow picamera2 psutil
fi

echo ""
echo "🔧 Configuring system..."

# Enable camera interface
echo "Enabling camera interface..."
raspi-config nonint do_camera 0

# Create log directory
mkdir -p /var/log
touch /var/log/door_lock.log
chmod 666 /var/log/door_lock.log

# Set environment variables
echo ""
echo "📝 Configuration:"
read -p "Enter your Cloud Server URL (e.g., https://your-server.railway.app): " CLOUD_URL
read -p "Enter QR Hash (press Enter to use default): " QR_HASH

# Create environment file
cat > /etc/door_lock.env << EOF
# Door Lock System Environment Variables
CLOUD_SERVER_URL=${CLOUD_URL}
QR_HASH=${QR_HASH:-7eb04163ef896754651041b69afe0bb9a45eb932faa787d3e93a262f7e074186}
EOF

chmod 600 /etc/door_lock.env
echo "✓ Configuration saved to /etc/door_lock.env"

# Install systemd service if service file exists
if [ -f "door_lock.service" ]; then
    echo ""
    echo "📝 Installing systemd service..."
    cp door_lock.service /etc/systemd/system/
    chmod 644 /etc/systemd/system/door_lock.service
    
    # Update service file with correct path
    SCRIPT_DIR=$(pwd)
    sed -i "s|/home/pi/door_lock|${SCRIPT_DIR}|g" /etc/systemd/system/door_lock.service
    
    systemctl daemon-reload
    systemctl enable door_lock.service
    echo "✓ Service installed and enabled"
fi

echo ""
echo "=========================================="
echo "✓ Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test the system manually:"
echo "   sudo python3 raspberry_pi_door_lock.py"
echo ""
echo "2. Start the service:"
echo "   sudo systemctl start door_lock"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status door_lock"
echo ""
echo "4. View logs:"
echo "   sudo tail -f /var/log/door_lock.log"
echo ""
echo "5. Reboot to apply all changes:"
echo "   sudo reboot"
echo ""
