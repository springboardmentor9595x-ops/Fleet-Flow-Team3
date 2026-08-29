from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.vehicle import router as vehicle_router
from app.routers.dashboard import router as dashboard_router
from app.routers.driver import router as driver_router
from app.routers.shipment import router as shipment_router
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.routers.gps_tracking import (
    router as gps_tracking_router,
    start_gps_reliability_services,
    stop_gps_reliability_services,
)
from app.routers.trip import router as trip_router
from app.routers.maintenance import router as maintenance_router
from app.routers.attendance import router as attendance_router
from app.routers.analytics import router as analytics_router
from app.routers.fuel_record import router as fuel_record_router
from app.routers.notification import router as notification_router
from app.routers.reports import router as reports_router

@asynccontextmanager
async def lifespan(_: FastAPI):
    await start_gps_reliability_services()
    try:
        yield
    finally:
        await stop_gps_reliability_services()


app = FastAPI(
    lifespan=lifespan,
    title="FleetFlow API"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          
    allow_credentials=True,
    allow_methods=["*"],          
    allow_headers=["*"],          
)

# Register routers
app.include_router(auth_router)
app.include_router(vehicle_router)
app.include_router(dashboard_router)
app.include_router(driver_router)
app.include_router(shipment_router)
app.include_router(gps_tracking_router)
app.include_router(trip_router)
app.include_router(maintenance_router)
app.include_router(attendance_router)
app.include_router(analytics_router)
app.include_router(fuel_record_router)
app.include_router(notification_router)
app.include_router(reports_router)

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to FleetFlow API!"
    }
