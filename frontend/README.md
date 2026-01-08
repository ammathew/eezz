# Sunship Space Frontend

React + Vite frontend for Sunship Space, connecting to the Django backend.

## Tech Stack

- React 18
- Vite
- Axios for API requests
- Modern ES6+ JavaScript

## Prerequisites

- Node.js (managed via asdf)
- npm or yarn

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

The default configuration connects to the Django backend at `http://localhost:8000`.

### 3. Run development server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   └── HealthCheck.jsx
│   ├── services/         # API services
│   │   └── api.js
│   ├── assets/           # Static assets
│   ├── App.jsx           # Main App component
│   └── main.jsx          # Entry point
├── public/               # Public static files
├── .env                  # Environment variables
├── .env.example          # Environment variables template
└── vite.config.js        # Vite configuration
```

## API Integration

The app uses Axios to communicate with the Django backend. All API calls are centralized in `src/services/api.js`.

### Example Usage

```javascript
import { apiService } from './services/api';

// Call the health check endpoint
const response = await apiService.healthCheck();
console.log(response.data);
```

### Adding New API Endpoints

Edit `src/services/api.js` and add new methods to the `apiService` object:

```javascript
export const apiService = {
  healthCheck: () => api.get('/api/health/'),

  // Add your endpoints here
  getUsers: () => api.get('/api/users/'),
  createUser: (data) => api.post('/api/users/', data),
};
```

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Connecting to Backend

Make sure the Django backend is running before starting the frontend:

```bash
# In the unravel directory
cd ../unravel
source venv/bin/activate
python manage.py runserver
```

Then start the frontend:

```bash
# In the frontend directory
npm run dev
```

## Building for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

## CORS Configuration

The Django backend is already configured to allow requests from:
- `http://localhost:3000`
- `http://localhost:5173` (default Vite dev server port)

If you change the frontend port, update the `CORS_ALLOWED_ORIGINS` in the backend's `.env` file.
