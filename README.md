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
│   ├── alembic/
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
└── README.md
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
