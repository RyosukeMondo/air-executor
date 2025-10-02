#!/bin/bash
# Install Redis for state management

set -e

echo "🔧 Installing Redis..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Cannot detect OS"
    exit 1
fi

# Install based on OS
case "$OS" in
    ubuntu|debian)
        echo "📦 Installing via apt..."
        sudo apt-get update
        sudo apt-get install -y redis-server redis-tools

        # Configure Redis
        sudo systemctl enable redis-server
        sudo systemctl start redis-server
        ;;

    fedora|rhel|centos)
        echo "📦 Installing via dnf/yum..."
        sudo dnf install -y redis || sudo yum install -y redis

        # Configure Redis
        sudo systemctl enable redis
        sudo systemctl start redis
        ;;

    arch|manjaro)
        echo "📦 Installing via pacman..."
        sudo pacman -S --noconfirm redis

        # Configure Redis
        sudo systemctl enable redis
        sudo systemctl start redis
        ;;

    *)
        echo "❌ Unsupported OS: $OS"
        echo "Please install Redis manually from https://redis.io/download"
        exit 1
        ;;
esac

# Test Redis
echo "🔍 Testing Redis connection..."
if redis-cli ping | grep -q PONG; then
    echo "✅ Redis installed and running!"
else
    echo "⚠️ Redis installed but not responding. Check status with:"
    echo "    sudo systemctl status redis"
fi

echo ""
echo "Redis CLI: redis-cli"
echo "Monitor: redis-cli monitor"
echo "Stop: sudo systemctl stop redis"
echo "Start: sudo systemctl start redis"
