# FleetFlow

FleetFlow is a Fleet Management System developed using FastAPI, React, and PostgreSQL. It helps organizations manage vehicles, drivers, shipments, trips, maintenance, fuel records, GPS tracking, attendance, and notifications.

## Tech Stack

### Backend
- FastAPI
- Python
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT Authentication

### Frontend
- React
- Vite
- Tailwind CSS
- Axios

## Project Structure

```
fleetflow/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── driver.py
│   │   │   ├── vehicle.py
│   │   │   ├── shipment.py
│   │   │   ├── trip.py
│   │   │   ├── gps_tracking.py
│   │   │   ├── maintenance.py
│   │   │   ├── fuel_record.py
│   │   │   ├── notification.py
│   │   │   └── attendance.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   └── crud/
│   │       ├── __init__.py
│   │       └── user.py
│   ├── alembic/
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env
│   └── .gitignore
└── frontend/
    ├── public/
    ├── src/
    │   ├── api/
    │   │   └── axios.js
    │   ├── components/
    │   │   └── auth/
    │   │       ├── LoginForm.jsx
    │   │       └── SignupForm.jsx
    │   ├── context/
    │   │   └── AuthContext.jsx
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   ├── Signup.jsx
    │   │   └── Dashboard.jsx
    │   ├── routes/
    │   │   └── ProtectedRoute.jsx
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    └── .env
```

## Features

- User Authentication (JWT)
- Driver Management
- Vehicle Management
- Shipment Management
- Trip Management
- GPS Tracking
- Fuel Records
- Maintenance Records
- Attendance Management
- Notifications
- RESTful APIs
- Responsive React Dashboard

## Installation

### Clone Repository

```bash
git clone https://github.com/springboardmentor9595x-ops/Fleet-Flow-Team3.git
cd Fleet-Flow-Team3
```

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file and configure your PostgreSQL database.

Run migrations:

```bash
alembic upgrade head
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Team

- Ayush Singh

## License

This project is developed for academic purposes.
