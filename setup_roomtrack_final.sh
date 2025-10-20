#!/bin/bash

echo "🚀 RoomTrack Final Setup"
echo "========================"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Reset database
echo "🗃️  Resetting database..."
python complete_reset.py

# Create sample data
echo "📊 Creating sample data..."
python create_sample_data.py

echo ""
echo "✅ SETUP COMPLETE!"
echo ""
echo "🎯 To start RoomTrack:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 Then open: http://localhost:5000"
echo ""
echo "👤 DEMO ACCOUNTS:"
echo "   👑 Admin:    admin / admin123"
echo "   🏠 Landlord: landlord1 / pass123"
echo "   👤 Tenant:   tenant1 / pass123"
