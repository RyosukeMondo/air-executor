#!/bin/bash
# Setup JavaScript/TypeScript development tools for autonomous fixing
# Based on config/projects/cc-task-manager.yaml

set -e

echo "=================================="
echo "JavaScript/TypeScript Tools Setup"
echo "=================================="
echo ""

# Detect if we should use sudo
USE_SUDO=""
INSTALL_GLOBAL="-g"
if [ "$1" = "--sudo" ]; then
    USE_SUDO="sudo"
    echo "Running with sudo for global npm installation"
else
    echo "Installing globally without sudo (may require npm config)"
    echo "Use --sudo if you need system-wide installation"
fi
echo ""

# Check Node.js
echo "1. Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first:"
    echo "   Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt install -y nodejs"
    echo "   macOS: brew install node"
    echo "   Or visit: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "✅ Found Node.js: $NODE_VERSION"
echo "✅ Found npm: $NPM_VERSION"
echo ""

# Check npm global prefix (to avoid permission issues)
NPM_PREFIX=$(npm config get prefix)
echo "npm global prefix: $NPM_PREFIX"

if [ -z "$USE_SUDO" ] && [[ "$NPM_PREFIX" == "/usr"* ]]; then
    echo "⚠️  Warning: npm prefix points to /usr, may need --sudo"
    echo "   Or configure npm to use user directory:"
    echo "   mkdir -p ~/.npm-global"
    echo "   npm config set prefix '~/.npm-global'"
    echo "   export PATH=~/.npm-global/bin:\$PATH"
    echo ""
fi

# Install linters (from config: ["eslint"])
echo "2. Installing linters..."
echo "   - eslint (code quality)"

$USE_SUDO npm install $INSTALL_GLOBAL eslint

echo "✅ Linters installed"
echo ""

# Install type checker (from config: "tsc")
echo "3. Installing TypeScript compiler..."
echo "   - typescript (type checking with tsc)"

$USE_SUDO npm install $INSTALL_GLOBAL typescript

echo "✅ TypeScript installed"
echo ""

# Install test framework (from config: "jest")
echo "4. Installing test framework..."
echo "   - jest"

$USE_SUDO npm install $INSTALL_GLOBAL jest

echo "✅ Test framework installed"
echo ""

# Optional: Install additional useful tools
echo "5. Installing optional tools..."
echo "   - prettier (code formatting)"
echo "   - ts-node (run TypeScript directly)"

$USE_SUDO npm install $INSTALL_GLOBAL prettier ts-node

echo "✅ Optional tools installed"
echo ""

# Verify installation
echo "=================================="
echo "Verification"
echo "=================================="
echo ""

echo "Checking installed versions..."
node --version
npm --version
eslint --version
tsc --version
jest --version
prettier --version
ts-node --version

echo ""
echo "✅ JavaScript/TypeScript toolchain setup complete!"
echo ""
echo "Tools installed:"
echo "  - eslint     (linter)"
echo "  - typescript (type checker)"
echo "  - jest       (test runner)"
echo "  - prettier   (code formatter)"
echo "  - ts-node    (TypeScript execution)"
echo ""
echo "You can now run: python3 airflow_dags/autonomous_fixing/core/tool_validator.py --check-all"
