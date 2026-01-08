#!/bin/bash

# Start both Django backend and React frontend for development

echo "Starting Unravel development servers..."
echo ""

# Start Django backend in background
echo "Starting Django backend on http://localhost:8000..."
cd backend
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 2

# Start React frontend
echo "Starting React frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=================================="
echo "Development servers are running!"
echo "=================================="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Admin:    http://localhost:8000/admin"
echo "API:      http://localhost:8000/api/"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
