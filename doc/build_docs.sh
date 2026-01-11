#!/usr/bin/env bash
# Build script for VitePress documentation

set -e

echo "================================================"
echo "DDNS Documentation Builder"
echo "Using VitePress (Vue-powered Static Site Generator)"
echo "================================================"
echo ""

# Get the script's directory (doc/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "Node.js version: $(node --version)"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed"
    exit 1
fi

echo "npm version: $(npm --version)"
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

# Build the documentation
echo "Building documentation website..."
npm run build

echo ""
echo "================================================"
echo "Build complete!"
echo "================================================"
echo ""
echo "Output directory: .vitepress/dist"
echo ""
echo "To preview locally:"
echo "  cd doc && npm run docs:preview"
echo ""
echo "To start development server:"
echo "  cd doc && npm run docs:dev"
echo ""
