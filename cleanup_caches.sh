#!/bin/bash

# Cache Cleanup Script for Rakuten Trade Portfolio X-Ray
# This script helps identify and clean various cache and build artifacts

set -e

echo "==================================================================="
echo "Cache and Build Artifact Cleanup for Portfolio X-Ray"
echo "==================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print size
print_size() {
    local path=$1
    local desc=$2
    if [ -e "$path" ]; then
        size=$(du -sh "$path" 2>/dev/null | cut -f1)
        echo -e "${YELLOW}$desc${NC}: $size"
    else
        echo -e "${YELLOW}$desc${NC}: Not found"
    fi
}

# Function to ask yes/no
ask_yes_no() {
    local prompt=$1
    while true; do
        read -p "$prompt (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

echo "📊 Current Cache Sizes:"
echo "-------------------------------------------------------------------"

# 1. Node modules
print_size "./frontend/node_modules" "Frontend node_modules"

# 2. Python cache
pycache_size=$(find ./backend -type d -name '__pycache__' -exec du -sh {} + 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "0")
echo -e "${YELLOW}Python __pycache__${NC}: ${pycache_size}K"

# 3. Pytest cache
print_size "./backend/.pytest_cache" "Pytest cache"

# 4. Coverage reports
print_size "./backend/htmlcov" "Coverage HTML reports"

# 5. Docker
echo ""
echo -e "${YELLOW}Docker Images:${NC}"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "(portfolio|rakuten|REPOSITORY)" || echo "No portfolio images found"

echo ""
echo -e "${YELLOW}Docker System Usage:${NC}"
docker system df 2>/dev/null || echo "Docker not running"

echo ""
echo "==================================================================="
echo "Cleanup Options:"
echo "==================================================================="
echo ""

# Cleanup options
total_freed=0

# 1. Python cache
if ask_yes_no "${GREEN}Remove Python __pycache__ directories?${NC}"; then
    echo "Removing Python cache..."
    find ./backend -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find ./backend -type f -name '*.pyc' -delete 2>/dev/null || true
    find ./backend -type f -name '*.pyo' -delete 2>/dev/null || true
    echo "✅ Python cache removed"
fi

# 2. Pytest cache
if [ -d "./backend/.pytest_cache" ]; then
    if ask_yes_no "${GREEN}Remove pytest cache?${NC}"; then
        rm -rf ./backend/.pytest_cache
        echo "✅ Pytest cache removed"
    fi
fi

# 3. Coverage reports
if [ -d "./backend/htmlcov" ]; then
    if ask_yes_no "${GREEN}Remove coverage HTML reports?${NC}"; then
        rm -rf ./backend/htmlcov
        rm -f ./backend/.coverage
        echo "✅ Coverage reports removed"
    fi
fi

# 4. Node modules (WARNING: requires npm install to restore)
if [ -d "./frontend/node_modules" ]; then
    echo ""
    echo "${RED}⚠️  WARNING: Removing node_modules requires 'npm install' to restore${NC}"
    if ask_yes_no "${GREEN}Remove frontend node_modules (278MB)?${NC}"; then
        rm -rf ./frontend/node_modules
        echo "✅ node_modules removed"
        echo "ℹ️  Run 'cd frontend && npm install' to restore"
    fi
fi

# 5. Docker cleanup
echo ""
echo "${YELLOW}Docker Cleanup Options:${NC}"
echo "  1. Remove unused containers: docker container prune"
echo "  2. Remove unused images: docker image prune"
echo "  3. Remove build cache: docker builder prune"
echo "  4. Remove everything unused: docker system prune -a"
echo ""

if ask_yes_no "${GREEN}Remove stopped Docker containers?${NC}"; then
    docker container prune -f
    echo "✅ Stopped containers removed"
fi

if ask_yes_no "${GREEN}Remove dangling Docker images?${NC}"; then
    docker image prune -f
    echo "✅ Dangling images removed"
fi

if ask_yes_no "${GREEN}Remove Docker build cache?${NC}"; then
    docker builder prune -f
    echo "✅ Build cache removed"
fi

# 6. System-wide caches (macOS specific)
echo ""
echo "==================================================================="
echo "System-wide Cache Cleanup (macOS)"
echo "==================================================================="
echo ""
echo "Common system caches on macOS:"
echo "  - Homebrew: ~/Library/Caches/Homebrew"
echo "  - Pip: ~/Library/Caches/pip"
echo "  - npm: ~/.npm"
echo "  - Docker: ~/Library/Containers/com.docker.docker/Data"
echo ""

if ask_yes_no "${GREEN}Check Homebrew cache size?${NC}"; then
    if [ -d ~/Library/Caches/Homebrew ]; then
        brew_size=$(du -sh ~/Library/Caches/Homebrew 2>/dev/null | cut -f1)
        echo "Homebrew cache: $brew_size"
        if ask_yes_no "  Clean Homebrew cache?"; then
            brew cleanup -s
            rm -rf ~/Library/Caches/Homebrew/*
            echo "✅ Homebrew cache cleaned"
        fi
    else
        echo "Homebrew cache not found"
    fi
fi

if ask_yes_no "${GREEN}Check pip cache size?${NC}"; then
    if [ -d ~/Library/Caches/pip ]; then
        pip_size=$(du -sh ~/Library/Caches/pip 2>/dev/null | cut -f1)
        echo "Pip cache: $pip_size"
        if ask_yes_no "  Clean pip cache?"; then
            pip cache purge 2>/dev/null || rm -rf ~/Library/Caches/pip
            echo "✅ Pip cache cleaned"
        fi
    else
        echo "Pip cache not found"
    fi
fi

if ask_yes_no "${GREEN}Check npm cache size?${NC}"; then
    if [ -d ~/.npm ]; then
        npm_size=$(du -sh ~/.npm 2>/dev/null | cut -f1)
        echo "npm cache: $npm_size"
        if ask_yes_no "  Clean npm cache?"; then
            npm cache clean --force
            echo "✅ npm cache cleaned"
        fi
    else
        echo "npm cache not found"
    fi
fi

echo ""
echo "==================================================================="
echo "Cleanup Complete!"
echo "==================================================================="
echo ""
echo "📝 Additional cleanup commands you can run manually:"
echo ""
echo "  # Remove all Docker data (CAUTION: removes all images and containers)"
echo "  docker system prune -a --volumes"
echo ""
echo "  # Clean macOS system caches"
echo "  sudo rm -rf ~/Library/Caches/*"
echo "  sudo rm -rf /Library/Caches/*"
echo ""
echo "  # Check disk usage"
echo "  du -sh ~/* | sort -hr | head -20"
echo ""
echo "  # Find large files"
echo "  find ~ -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -20"
echo ""
