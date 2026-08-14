from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import get_db
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.models.trip import Trip
from app.models.fuel_record import FuelRecord
from app.models.maintenance import VehicleMaintenance
from app.models.user import User
from app.core.deps import get_current_user, require_roles
from app.models.user import RoleEnum


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


# ============================================================
# FLEET SUMMARY
# ============================================================

@router.get(
    "/summary",
)
def get_fleet_analytics_summary(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            RoleEnum.Admin,
            RoleEnum.FleetManager,
            RoleEnum.Dispatcher,
        )
    ),
):
    # Fleet Vehicles
    total_vehicles = db.query(func.count(Vehicle.vehicle_id)).scalar() or 0
    available_vehicles = db.query(func.count(Vehicle.vehicle_id)).filter(Vehicle.status == "Available").scalar() or 0
    assigned_vehicles = db.query(func.count(Vehicle.vehicle_id)).filter(Vehicle.status == "Assigned").scalar() or 0
    in_transit_vehicles = db.query(func.count(Vehicle.vehicle_id)).filter(Vehicle.status == "In Transit").scalar() or 0
    maintenance_vehicles = db.query(func.count(Vehicle.vehicle_id)).filter(Vehicle.status == "Maintenance").scalar() or 0

    utilization_rate = round(((in_transit_vehicles + assigned_vehicles) / total_vehicles * 100), 1) if total_vehicles > 0 else 0.0

    # Drivers
    total_drivers = db.query(func.count(Driver.driver_id)).scalar() or 0

    # Shipments
    total_shipments = db.query(func.count(Shipment.shipment_id)).scalar() or 0
    delivered_shipments = db.query(func.count(Shipment.shipment_id)).filter(Shipment.status == "Delivered").scalar() or 0
    in_transit_shipments = db.query(func.count(Shipment.shipment_id)).filter(Shipment.status == "In Transit").scalar() or 0
    delayed_shipments = db.query(func.count(Shipment.shipment_id)).filter(Shipment.status == "Delayed").scalar() or 0
    on_time_rate = round((delivered_shipments / total_shipments * 100), 1) if total_shipments > 0 else 100.0

    # Trips & Distances
    total_trips = db.query(func.count(Trip.trip_id)).scalar() or 0
    total_distance_meters = db.query(func.sum(Trip.distance)).scalar() or 0.0
    total_distance_km = round(total_distance_meters / 1000.0, 1)

    # Costs
    total_fuel_cost = db.query(func.sum(FuelRecord.fuel_cost)).scalar() or 0.0
    total_maintenance_cost = db.query(func.sum(VehicleMaintenance.cost)).scalar() or 0.0

    return {
        "fleet": {
            "total_vehicles": total_vehicles,
            "available": available_vehicles,
            "assigned": assigned_vehicles,
            "in_transit": in_transit_vehicles,
            "maintenance": maintenance_vehicles,
            "utilization_rate_pct": utilization_rate,
        },
        "drivers": {
            "total_drivers": total_drivers,
        },
        "shipments": {
            "total": total_shipments,
            "delivered": delivered_shipments,
            "in_transit": in_transit_shipments,
            "delayed": delayed_shipments,
            "on_time_rate_pct": on_time_rate,
        },
        "operations": {
            "total_trips": total_trips,
            "total_distance_km": total_distance_km,
            "total_fuel_cost": round(total_fuel_cost, 2),
            "total_maintenance_cost": round(total_maintenance_cost, 2),
            "total_operating_cost": round(total_fuel_cost + total_maintenance_cost, 2),
        }
    }


# ============================================================
# DRIVER PERFORMANCE
# ============================================================

@router.get(
    "/driver-performance",
)
def get_driver_performance(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns per-driver metrics:
    - trips completed
    - total distance driven
    - on-time delivery rate (completed trips / all their trips)
    """
    drivers = db.query(Driver).all()
    result = []

    for driver in drivers:
        # All trips for this driver
        all_trips = (
            db.query(Trip)
            .filter(Trip.driver_id == driver.driver_id)
            .all()
        )

        total_trips = len(all_trips)
        completed_trips = sum(1 for t in all_trips if t.status == "Completed")
        total_distance = sum((t.distance or 0) for t in all_trips) / 1000.0  # km

        on_time_rate = round((completed_trips / total_trips) * 100, 1) if total_trips > 0 else 0.0

        # Get user name via relationship
        user = driver.user
        full_name = user.full_name if user else str(driver.driver_id)[:8]

        result.append({
            "driver_id": str(driver.driver_id),
            "full_name": full_name,
            "status": driver.status,
            "total_trips": total_trips,
            "completed_trips": completed_trips,
            "total_distance_km": round(total_distance, 1),
            "completion_rate_pct": on_time_rate,
        })

    # Sort by completed trips descending
    result.sort(key=lambda x: x["completed_trips"], reverse=True)

    return {
        "total_drivers": len(result),
        "drivers": result,
    }


# ============================================================
# FUEL TRENDS
# ============================================================

@router.get(
    "/fuel-trends",
)
def get_fuel_trends(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns fuel cost and consumption per vehicle.
    """
    vehicles = db.query(Vehicle).all()
    result = []

    for vehicle in vehicles:
        records = (
            db.query(FuelRecord)
            .filter(FuelRecord.vehicle_id == vehicle.vehicle_id)
            .all()
        )

        total_fuel = sum(r.fuel_amount or 0 for r in records)
        total_cost = sum(r.fuel_cost or 0 for r in records)

        # Distance from trips for this vehicle (in km)
        trips = (
            db.query(Trip)
            .filter(Trip.vehicle_id == vehicle.vehicle_id, Trip.status == "Completed")
            .all()
        )
        total_distance_km = sum((t.distance or 0) for t in trips) / 1000.0

        efficiency = round(total_distance_km / total_fuel, 2) if total_fuel > 0 else 0.0

        result.append({
            "vehicle_id": str(vehicle.vehicle_id),
            "registration_number": vehicle.registration_number,
            "vehicle_type": vehicle.vehicle_type,
            "total_fuel_liters": round(total_fuel, 2),
            "total_fuel_cost": round(total_cost, 2),
            "total_distance_km": round(total_distance_km, 2),
            "km_per_liter": efficiency,
            "refill_count": len(records),
        })

    # Sort by cost descending
    result.sort(key=lambda x: x["total_fuel_cost"], reverse=True)

    return {
        "total_vehicles": len(result),
        "vehicles": result,
    }


# ============================================================
# MAINTENANCE COSTS
# ============================================================

@router.get(
    "/maintenance-costs",
)
def get_maintenance_costs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns maintenance cost breakdown:
    - By maintenance type (total cost per type)
    - Per vehicle (total cost per vehicle)
    """
    records = db.query(VehicleMaintenance).all()

    # By type
    by_type: dict = {}
    by_vehicle: dict = {}

    for record in records:
        m_type = record.maintenance_type or "General Inspection"
        cost = record.cost or 0.0

        # Aggregate by type
        if m_type not in by_type:
            by_type[m_type] = {"maintenance_type": m_type, "total_cost": 0.0, "count": 0}
        by_type[m_type]["total_cost"] += cost
        by_type[m_type]["count"] += 1

        # Aggregate by vehicle
        v_id = str(record.vehicle_id) if record.vehicle_id else "unassigned"
        if v_id not in by_vehicle:
            # Get vehicle registration
            if record.vehicle_id:
                vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == record.vehicle_id).first()
                reg = vehicle.registration_number if vehicle else v_id[:8]
            else:
                reg = "Unassigned"
            by_vehicle[v_id] = {
                "vehicle_id": v_id,
                "registration_number": reg,
                "total_cost": 0.0,
                "record_count": 0,
            }
        by_vehicle[v_id]["total_cost"] += cost
        by_vehicle[v_id]["record_count"] += 1

    type_list = sorted(by_type.values(), key=lambda x: x["total_cost"], reverse=True)
    vehicle_list = sorted(by_vehicle.values(), key=lambda x: x["total_cost"], reverse=True)

    total_cost = sum(r.cost or 0 for r in records)

    return {
        "total_maintenance_cost": round(total_cost, 2),
        "total_records": len(records),
        "by_type": type_list,
        "by_vehicle": vehicle_list,
    }


# ============================================================
# SHIPMENT ALERTS (Delayed)
# ============================================================

@router.get(
    "/shipment-alerts",
)
def get_shipment_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns all delayed shipments as an alert list.
    """
    delayed = (
        db.query(Shipment)
        .filter(Shipment.status == "Delayed")
        .all()
    )

    result = []
    for s in delayed:
        result.append({
            "shipment_id": str(s.shipment_id),
            "tracking_number": s.tracking_number,
            "source": s.source,
            "destination": s.destination,
            "customer_name": s.customer_name,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "alert": "Shipment is delayed",
        })

    return {
        "total_delayed": len(result),
        "delayed_shipments": result,
    }
