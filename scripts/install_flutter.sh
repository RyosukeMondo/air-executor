#!/bin/bash
# Install Flutter SDK

set -e

FLUTTER_VERSION="3.24.3"
INSTALL_DIR="$HOME/flutter"

echo "🔧 Installing Flutter SDK ${FLUTTER_VERSION}..."

# Check if Flutter already installed
if [ -d "$INSTALL_DIR" ]; then
    echo "✅ Flutter already installed at $INSTALL_DIR"
    echo "Current version:"
    "$INSTALL_DIR/bin/flutter" --version
    read -p "Reinstall? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping installation. Updating PATH..."
        exit 0
    fi
    rm -rf "$INSTALL_DIR"
fi

# Download Flutter
echo "📥 Downloading Flutter SDK..."
cd "$HOME"
git clone https://github.com/flutter/flutter.git -b stable --depth 1

# Add to PATH for this session
export PATH="$INSTALL_DIR/bin:$PATH"

# Run Flutter doctor to download Dart SDK and other dependencies
echo "🔍 Running Flutter doctor..."
flutter doctor

# Configure Flutter
echo "⚙️ Configuring Flutter..."
flutter config --no-analytics
flutter precache

echo ""
echo "✅ Flutter installed successfully!"
echo ""
echo "📝 Add this to your ~/.bashrc or ~/.zshrc:"
echo "    export PATH=\"\$HOME/flutter/bin:\$PATH\""
echo ""
echo "Then run: source ~/.bashrc (or ~/.zshrc)"
echo ""
echo "Verify installation with: flutter doctor"
