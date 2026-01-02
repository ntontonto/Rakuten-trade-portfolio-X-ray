#!/bin/bash
# Setup local Python environment for development/testing

echo "🐍 Setting up local Python environment..."

# Check Python version
python3 --version

# Create virtual environment
echo "📦 Creating virtual environment..."
cd backend
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  cd backend && source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest tests/test_price_fetcher_unit.py -v"
echo ""
echo "To deactivate:"
echo "  deactivate"
echo ""
echo "⚠️  Note: You'll still need Docker for the database and full application"
