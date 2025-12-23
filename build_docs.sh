#!/usr/bin/env bash
# Build script for VitePress documentation

set -e

echo "================================================"
echo "DDNS Documentation Builder"
echo "Using VitePress (Vue-powered Static Site Generator)"
echo "================================================"
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

# Create docs directory structure
echo "Setting up documentation structure..."

# Create docs directory if it doesn't exist
mkdir -p docs

# Copy README as index
if [ -f "README.md" ]; then
    cp README.md docs/index.md
    echo "✓ Copied README.md to docs/index.md"
fi

# Copy English README if exists
if [ -f "README.en.md" ]; then
    mkdir -p docs/en
    cp README.en.md docs/en/index.md
    echo "✓ Copied README.en.md to docs/en/index.md"
fi

# Copy doc directory
if [ -d "doc" ]; then
    # Copy to root level docs
    cp -r doc docs/
    echo "✓ Copied doc/ directory"
    
    # For English version, also copy the doc directory
    if [ -d "docs/en" ]; then
        cp -r doc docs/en/
        echo "✓ Copied doc/ to English version"
    fi
fi

echo ""
echo "Building documentation website..."
npm run docs:build

echo ""
echo "================================================"
echo "Build complete!"
echo "================================================"
echo ""
echo "Output directory: docs/.vitepress/dist"
echo ""
echo "To preview locally:"
echo "  npm run docs:preview"
echo ""
echo "To start development server:"
echo "  npm run docs:dev"
echo ""
