"""Read-only reports assembled from the existing FleetFlow models/services."""
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.fuel_record import FuelRecord
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.services.analytics import delivery_performance, driver_performance, fleet_utilization
from app.services.report_date_range import ReportPeriod


def _value(value):
    return value.value if hasattr(value, "value") else str(value)


def _base(report_type: str, period: ReportPeriod, summary: dict, data: list, limitations: list[str] | None = None):
    return {"report_type": report_type, "period": period.as_dict(), "summary": summary, "data": data, "limitations": limitations or []}


def fleet_utilization_report(db: Session, period: ReportPeriod) -> dict:
    current = fleet_utilization(db)
    statuses = current["statuses"]
    active = statuses[VehicleStatus.Assigned.value]["count"] + statuses[VehicleStatus.InTransit.value]["count"]
    summary = {
        "total_vehicles": current["total_fleet"], "available_vehicles": statuses[VehicleStatus.Available.value]["count"],
        "assigned_vehicles": statuses[VehicleStatus.Assigned.value]["count"], "in_transit_vehicles": statuses[VehicleStatus.InTransit.value]["count"],
        "maintenance_vehicles": statuses[VehicleStatus.Maintenance.value]["count"], "active_vehicles": active,
        "utilization_percentage": round((active / current["total_fleet"]) * 100, 2) if current["total_fleet"] else 0.0,
    }
    return _base("fleet_utilization", period, summary, [{"status": key, **value} for key, value in statuses.items()], ["Vehicle status history is not stored; the selected period does not change this current-status breakdown."])


def fuel_consumption_report(db: Session, period: ReportPeriod) -> dict:
    records = db.query(FuelRecord).filter(FuelRecord.refill_date >= period.start_datetime, FuelRecord.refill_date <= period.end_datetime).all()
    vehicle_ids = {record.vehicle_id for record in records if record.vehicle_id}
    vehicles = {item.vehicle_id: item.registration_number for item in db.query(Vehicle).filter(Vehicle.vehicle_id.in_(vehicle_ids or [None])).all()}
    groups = defaultdict(lambda: {"fuel_amount": Decimal("0"), "fuel_cost": Decimal("0"), "mileages": [], "refuels": 0})
    for record in records:
        if record.vehicle_id is None:
            continue
        group = groups[record.vehicle_id]; group["fuel_amount"] += record.fuel_amount or Decimal("0"); group["fuel_cost"] += record.fuel_cost or Decimal("0"); group["refuels"] += 1
        if record.mileage is not None: group["mileages"].append(float(record.mileage))
    data = [{"vehicle_id": str(vehicle_id), "registration_number": vehicles.get(vehicle_id), "total_fuel_amount": float(group["fuel_amount"]), "total_fuel_cost": float(group["fuel_cost"]), "number_of_refuels": group["refuels"], "average_mileage": round(sum(group["mileages"]) / len(group["mileages"]), 2) if group["mileages"] else None} for vehicle_id, group in sorted(groups.items(), key=lambda item: str(item[0]))]
    return _base("fuel_consumption", period, {"total_fuel_consumed": round(sum(row["total_fuel_amount"] for row in data), 3), "total_fuel_cost": round(sum(row["total_fuel_cost"] for row in data), 2), "total_refuels": sum(row["number_of_refuels"] for row in data), "number_of_vehicles": len(data)}, data)


def driver_performance_report(db: Session, period: ReportPeriod) -> dict:
    metrics = driver_performance(db, start_date=period.start_datetime, end_date=period.end_datetime)
    data = [{"driver_id": str(item["driver_id"]), "driver": item["full_name"], "status": item["status"], "trips_completed": item["trips_completed"], "on_time_trips": item["on_time_deliveries"], "delayed_trips": max(0, item["deliveries_with_expected_time"] - item["on_time_deliveries"]), "on_time_rate": item["on_time_delivery_rate"], "attendance": {"check_ins": item["attendance_check_ins"], "rate": item["attendance_rate"]}} for item in metrics["drivers"]]
    return _base("driver_performance", period, metrics["summary"], data, ["On-time performance is calculated only for completed trips whose shipment has expected_delivery_at. Attendance is derived from recorded Check-in activity."])


def delivery_performance_report(db: Session, period: ReportPeriod) -> dict:
    shipments = db.query(Shipment).filter(Shipment.created_at >= period.start_datetime, Shipment.created_at <= period.end_datetime).all()
    status_counts = Counter(_value(item.status) for item in shipments)
    completed_metrics = delivery_performance(db, start_date=period.start_datetime, end_date=period.end_datetime)
    summary = {"total_shipments": len(shipments), "delivered_shipments": status_counts[ShipmentStatus.Delivered.value], "delayed_shipments": status_counts[ShipmentStatus.Delayed.value], "cancelled_shipments": status_counts[ShipmentStatus.Cancelled.value], "on_time_deliveries": completed_metrics["on_time_deliveries"], "delayed_deliveries": completed_metrics["delayed_deliveries"], "on_time_percentage": completed_metrics["on_time_rate"], "average_delivery_time_seconds": completed_metrics["average_delivery_time_seconds"]}
    data = [{"shipment_id": str(item.shipment_id), "tracking_number": item.tracking_number, "source": item.source, "destination": item.destination, "status": _value(item.status), "expected_delivery_at": item.expected_delivery_at.isoformat() if item.expected_delivery_at else None} for item in shipments]
    return _base("delivery_performance", period, summary, data, ["Delivery duration and on-time metrics use completed Trip timestamps; shipments without a completed trip or expected_delivery_at are not evaluated for those metrics."])


def maintenance_report(db: Session, period: ReportPeriod) -> dict:
    records = db.query(Maintenance).filter(Maintenance.service_date >= period.start_datetime, Maintenance.service_date <= period.end_datetime).all()
    vehicle_ids = {item.vehicle_id for item in records}; registration = {item.vehicle_id: item.registration_number for item in db.query(Vehicle).filter(Vehicle.vehicle_id.in_(vehicle_ids or [None])).all()}
    costs = defaultdict(lambda: {"cost": Decimal("0"), "count": 0}); frequency = Counter(); status_counts = Counter(); today = date.today()
    upcoming, overdue = [], []
    for item in records:
        name = _value(item.status); status_counts[name] += 1; frequency[item.maintenance_type] += 1; costs[item.vehicle_id]["cost"] += item.cost or Decimal("0"); costs[item.vehicle_id]["count"] += 1
        row = {"maintenance_id": str(item.maintenance_id), "vehicle_id": str(item.vehicle_id), "registration_number": registration.get(item.vehicle_id), "maintenance_type": item.maintenance_type, "service_date": item.service_date.isoformat(), "status": name, "cost": float(item.cost or 0)}
        if item.service_date.date() < today and name not in {MaintenanceStatus.Completed.value, MaintenanceStatus.Cancelled.value, MaintenanceStatus.Resolved.value}: overdue.append(row)
        elif item.service_date.date() >= today and name in {MaintenanceStatus.Scheduled.value, MaintenanceStatus.InProgress.value}: upcoming.append(row)
    summary = {"total_maintenance_records": len(records), "total_maintenance_cost": round(sum(float(item.cost or 0) for item in records), 2), "scheduled_count": status_counts[MaintenanceStatus.Scheduled.value], "in_progress_count": status_counts[MaintenanceStatus.InProgress.value], "completed_count": status_counts[MaintenanceStatus.Completed.value], "cancelled_count": status_counts[MaintenanceStatus.Cancelled.value], "resolved_count": status_counts[MaintenanceStatus.Resolved.value], "upcoming_maintenance_count": len(upcoming), "overdue_maintenance_count": len(overdue)}
    data = [{"section": "cost_by_vehicle", "items": [{"vehicle_id": str(vehicle_id), "registration_number": registration.get(vehicle_id), "total_cost": float(values["cost"]), "maintenance_count": values["count"]} for vehicle_id, values in costs.items()]}, {"section": "frequency_by_type", "items": [{"maintenance_type": key, "maintenance_count": value} for key, value in sorted(frequency.items())]}, {"section": "upcoming_maintenance", "items": upcoming}, {"section": "overdue_maintenance", "items": overdue}]
    return _base("maintenance", period, summary, data)
