# FleetFlow

FleetFlow is a Fleet Management System developed using **FastAPI**, **React**, and **PostgreSQL**. The system helps organizations manage drivers, vehicles, shipments, trips, fuel records, maintenance, GPS tracking, attendance, and notifications through a modern web application.

---

## 🚀 Tech Stack

### Backend
- FastAPI
- Python
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT Authentication
- Pydantic

### Frontend
- React
- Vite
- Tailwind CSS
- Axios
- React Context API

---

# 📁 Project Structure

```text
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

---

# ✨ Features

- User Authentication (JWT)
- User Registration & Login
- Driver Management
- Vehicle Management
- Shipment Management
- Trip Management
- GPS Tracking
- Fuel Record Management
- Vehicle Maintenance Records
- Attendance Management
- Notifications
- RESTful API
- Protected Routes
- Responsive User Interface

---

# ⚙️ Backend Setup

## 1. Navigate to Backend

```bash
cd backend
```

## 2. Create Virtual Environment

```bash
python -m venv venv
```

## 3. Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Configure Environment Variables

Create a `.env` file inside the backend folder and add your PostgreSQL configuration.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/fleetflow
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 6. Run Database Migrations

```bash
alembic upgrade head
```

## 7. Start Backend

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```
http://127.0.0.1:8000
```

API Documentation:

```
http://127.0.0.1:8000/docs
```

---

# 💻 Frontend Setup

## Navigate to Frontend

```bash
cd frontend
```

## Install Dependencies

```bash
npm install
```

## Start Development Server

```bash
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

# 🔐 Authentication

- JWT-based Authentication
- Login
- Signup
- Protected Routes
- Authorization Middleware

---

# 📌 Future Enhancements

- Driver Dashboard
- Admin Dashboard
- Vehicle Analytics
- Real-time GPS Tracking
- Email Notifications
- Report Generation
- Role-Based Access Control
- Deployment using Docker

---

# 👨‍💻 Team

**FleetFlow Team 3**

- Ayush Singh

---

# 📄 License

This project is developed for educational and academic purposes.
