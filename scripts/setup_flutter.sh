#!/bin/bash
# Setup Flutter development tools for autonomous fixing
# Based on config/projects/money-making-app.yaml

set -e

echo "=================================="
echo "Flutter Tools Setup"
echo "=================================="
echo ""

# Check if Flutter is already installed
echo "1. Checking Flutter installation..."
FLUTTER_ALREADY_INSTALLED=false
if command -v flutter &> /dev/null; then
    FLUTTER_VERSION=$(flutter --version | head -1)
    echo "✅ Flutter already installed: $FLUTTER_VERSION"
    FLUTTER_ALREADY_INSTALLED=true
    INSTALL_DIR=$(dirname $(dirname $(which flutter)))
else
    echo "❌ Flutter not found. Will install Flutter..."
fi
echo ""

# Detect OS
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

echo "Detected OS: $OS, Architecture: $ARCH"
echo ""

# Installation directory
if [ "$FLUTTER_ALREADY_INSTALLED" = false ]; then
    INSTALL_DIR="$HOME/flutter"
fi

# Check if we should use sudo (for dependencies)
USE_SUDO=""
if [ "$1" = "--sudo" ]; then
    USE_SUDO="sudo"
    echo "Using sudo for system dependencies"
fi
echo ""

# Install dependencies based on OS (skip if Flutter already installed)
if [ "$FLUTTER_ALREADY_INSTALLED" = false ]; then
    echo "2. Installing dependencies..."
    case $OS in
        linux)
            if command -v apt &> /dev/null; then
                echo "Installing dependencies via apt..."
                $USE_SUDO apt update
                # Basic Flutter dependencies
                $USE_SUDO apt install -y curl git unzip xz-utils zip libglu1-mesa
                # Linux desktop development toolchain
                $USE_SUDO apt install -y clang cmake ninja-build libgtk-3-dev mesa-utils
                # Java (required for Android SDK)
                $USE_SUDO apt install -y openjdk-17-jdk
            elif command -v yum &> /dev/null; then
                echo "Installing dependencies via yum..."
                # Basic Flutter dependencies
                $USE_SUDO yum install -y curl git unzip xz zip mesa-libGLU
                # Linux desktop development toolchain
                $USE_SUDO yum install -y clang cmake ninja-build gtk3-devel mesa-demos
                # Java (required for Android SDK)
                $USE_SUDO yum install -y java-17-openjdk-devel
            else
                echo "⚠️  Could not detect package manager. Please install manually:"
                echo "   Basic: curl, git, unzip, xz-utils, zip, libglu1-mesa"
                echo "   Linux desktop: clang, cmake, ninja-build, libgtk-3-dev, mesa-utils"
            fi
            ;;
        darwin)
            if ! command -v brew &> /dev/null; then
                echo "⚠️  Homebrew not found. Install from: https://brew.sh"
                exit 1
            fi
            echo "Installing dependencies via Homebrew..."
            brew install git curl unzip
            ;;
        *)
            echo "❌ Unsupported OS: $OS"
            exit 1
            ;;
    esac

    echo "✅ Dependencies installed"
    echo ""

    # Clone Flutter SDK
    echo "3. Downloading Flutter SDK..."
    if [ -d "$INSTALL_DIR" ]; then
        echo "⚠️  $INSTALL_DIR already exists. Removing..."
        rm -rf "$INSTALL_DIR"
    fi

    git clone https://github.com/flutter/flutter.git -b stable "$INSTALL_DIR"

    echo "✅ Flutter SDK downloaded to $INSTALL_DIR"
    echo ""

    # Add Flutter to PATH
    echo "4. Configuring PATH..."
    PROFILE_FILE="$HOME/.profile"

    if ! grep -q "flutter/bin" "$PROFILE_FILE" 2>/dev/null; then
        echo "" >> "$PROFILE_FILE"
        echo "# Flutter SDK" >> "$PROFILE_FILE"
        echo "export PATH=\"\$PATH:$INSTALL_DIR/bin\"" >> "$PROFILE_FILE"
        echo "✅ Added Flutter to $PROFILE_FILE"
    else
        echo "✅ Flutter already in PATH configuration"
    fi

    # Add to current session
    export PATH="$PATH:$INSTALL_DIR/bin"

    echo ""
else
    echo "2. Skipping Flutter installation (already installed)"
    echo ""

    # Install Java if needed (for Android SDK)
    if [ "$OS" = "linux" ]; then
        if ! command -v java &> /dev/null; then
            echo "Installing Java (required for Android SDK)..."
            if command -v apt &> /dev/null; then
                $USE_SUDO apt update
                $USE_SUDO apt install -y openjdk-17-jdk
            elif command -v yum &> /dev/null; then
                $USE_SUDO yum install -y java-17-openjdk-devel
            fi
            echo "✅ Java installed"
        else
            echo "✅ Java already installed: $(java -version 2>&1 | head -1)"
        fi
    fi
    echo ""
fi

PROFILE_FILE="$HOME/.profile"

# Install Android SDK (Linux only)
if [ "$OS" = "linux" ]; then
    echo "3. Setting up Android SDK..."
    ANDROID_HOME="$HOME/Android/Sdk"
    CMDLINE_TOOLS_DIR="$ANDROID_HOME/cmdline-tools/latest"

    if [ ! -d "$ANDROID_HOME" ]; then
        echo "Installing Android command-line tools..."

        # Create directories
        mkdir -p "$ANDROID_HOME/cmdline-tools"

        # Download Android command-line tools
        CMDLINE_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
        TEMP_ZIP="/tmp/cmdline-tools.zip"

        echo "Downloading from $CMDLINE_TOOLS_URL..."
        curl -L "$CMDLINE_TOOLS_URL" -o "$TEMP_ZIP"

        # Extract to temporary location
        unzip -q "$TEMP_ZIP" -d "$ANDROID_HOME/cmdline-tools"

        # Move to 'latest' directory (required structure)
        mv "$ANDROID_HOME/cmdline-tools/cmdline-tools" "$CMDLINE_TOOLS_DIR"

        # Cleanup
        rm "$TEMP_ZIP"

        echo "✅ Android command-line tools downloaded"
    else
        echo "✅ Android SDK directory already exists"
    fi

    # Configure environment variables
    echo ""
    echo "4. Configuring Android environment variables..."

    # Set JAVA_HOME if not already set
    if [ -z "$JAVA_HOME" ]; then
        if [ -d "/usr/lib/jvm/java-17-openjdk-amd64" ]; then
            export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
        elif [ -d "/usr/lib/jvm/java-17-openjdk" ]; then
            export JAVA_HOME="/usr/lib/jvm/java-17-openjdk"
        else
            # Try to find Java home automatically
            JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
            export JAVA_HOME
        fi
        echo "Set JAVA_HOME=$JAVA_HOME"
    fi

    # Add to profile
    if ! grep -q "ANDROID_HOME" "$PROFILE_FILE" 2>/dev/null; then
        echo "" >> "$PROFILE_FILE"
        echo "# Android SDK" >> "$PROFILE_FILE"
        if ! grep -q "JAVA_HOME" "$PROFILE_FILE" 2>/dev/null; then
            echo "export JAVA_HOME=\"$JAVA_HOME\"" >> "$PROFILE_FILE"
        fi
        echo "export ANDROID_HOME=\"$ANDROID_HOME\"" >> "$PROFILE_FILE"
        echo "export PATH=\"\$PATH:\$ANDROID_HOME/cmdline-tools/latest/bin\"" >> "$PROFILE_FILE"
        echo "export PATH=\"\$PATH:\$ANDROID_HOME/platform-tools\"" >> "$PROFILE_FILE"
        echo "✅ Added Android SDK to $PROFILE_FILE"
    else
        echo "✅ Android SDK already in PATH configuration"
    fi

    # Add to current session
    export ANDROID_HOME="$ANDROID_HOME"
    export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin"
    export PATH="$PATH:$ANDROID_HOME/platform-tools"

    # Install SDK components
    echo ""
    echo "5. Installing Android SDK components..."

    # Accept licenses automatically
    yes | "$CMDLINE_TOOLS_DIR/bin/sdkmanager" --licenses 2>/dev/null || true

    # Install required SDK components
    "$CMDLINE_TOOLS_DIR/bin/sdkmanager" \
        "platform-tools" \
        "platforms;android-34" \
        "build-tools;34.0.0" \
        "cmdline-tools;latest" 2>/dev/null || echo "⚠️  Some SDK components may already be installed"

    echo "✅ Android SDK components installed"
    echo ""
else
    echo "3. Skipping Android SDK setup (not on Linux)"
    echo ""
fi

# Run flutter doctor
echo "6. Running flutter doctor..."
flutter doctor

echo ""
echo "=================================="
echo "Verification"
echo "=================================="
echo ""

echo "Checking installed versions..."
flutter --version

echo ""
echo "✅ Flutter toolchain setup complete!"
echo ""
echo "Flutter SDK location: $INSTALL_DIR"
if [ "$OS" = "linux" ] && [ -d "$ANDROID_HOME" ]; then
    echo "Android SDK location: $ANDROID_HOME"
fi
echo ""
echo "Tools available:"
echo "  - flutter        (SDK)"
echo "  - dart           (comes with Flutter)"
echo "  - flutter analyze (static analysis)"
echo "  - flutter test   (test runner)"
if [ "$OS" = "linux" ] && [ -d "$ANDROID_HOME" ]; then
    echo "  - sdkmanager     (Android SDK manager)"
    echo "  - adb            (Android Debug Bridge)"
fi
echo ""
echo "⚠️  IMPORTANT: Reload your shell or run:"
echo "   source ~/.profile"
echo "   Or restart your terminal"
echo ""
echo "Then verify with: flutter doctor"
echo "Then run: python3 airflow_dags/autonomous_fixing/core/tool_validator.py --check-all"
