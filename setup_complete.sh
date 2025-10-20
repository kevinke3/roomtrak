#!/bin/bash

echo "🚀 Setting up RoomTrack Complete System..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directory structure..."
mkdir -p static/css static/js static/images templates/admin templates/landlord templates/tenant

# Run the application to initialize database
echo "Initializing database..."
python app.py &

# Wait a bit for the app to start
sleep 3

# Stop the app
pkill -f "python app.py"

# Create sample data
echo "Creating sample data..."
python create_sample_data.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run RoomTrack:"
echo "source venv/bin/activate"
echo "python app.py"
echo ""
echo "📱 Access the application at: http://localhost:5000"
echo ""
echo "Demo Accounts:"
echo "Admin:    admin / admin123"
echo "Landlord: landlord1 / pass123"
echo "Tenant:   tenant1 / pass123"
