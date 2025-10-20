#!/bin/bash

echo "🚀 Starting RoomTrack Complete Setup..."

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Reset database
echo "Resetting database..."
python reset_database.py

# Create sample data
echo "Creating sample data..."
python create_sample_data.py

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🎯 To start RoomTrack:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 Then open: http://localhost:5000"
echo ""
echo "👤 Demo Accounts:"
echo "   Admin:    admin / admin123"
echo "   Landlord: landlord1 / pass123"
echo "   Tenant:   tenant1 / pass123"
echo ""
echo "🏢 Sample Data:"
echo "   - Sunrise Apartments with 6 units"
echo "   - 3 occupied, 3 vacant units"
echo "   - Tenant1 in Unit A101 with payment history"
echo "   - Sample maintenance requests"
