"""Read-only operational analytics calculated from existing FleetFlow tables."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceActivityType
from app.models.driver import Driver
from app.models.fuel_record import FuelRecord
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip, TripStatus
from app.models.vehicle import Vehicle, VehicleStatus


VEHICLE_STATUSES = (
    VehicleStatus.Available,
    VehicleStatus.Assigned,
    VehicleStatus.InTransit,
    VehicleStatus.Maintenance,
)


def _value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _percentage(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0


def _apply_completed_trip_dates(query, start_date: datetime | None, end_date: datetime | None):
    if start_date is not None:
        query = query.filter(Trip.ended_at >= start_date)
    if end_date is not None:
        query = query.filter(Trip.ended_at <= end_date)
    return query


def fleet_utilization(db: Session) -> dict:
    total_fleet = db.query(Vehicle).count()
    statuses = {}
    for vehicle_status in VEHICLE_STATUSES:
        label = _value(vehicle_status)
        count = db.query(Vehicle).filter(Vehicle.status == vehicle_status).count()
        statuses[label] = {"count": count, "percentage": _percentage(count, total_fleet)}
    return {"total_fleet": total_fleet, "statuses": statuses}


def driver_performance(
    db: Session,
    driver_id: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    drivers_query = db.query(Driver)
    if driver_id is not None:
        drivers_query = drivers_query.filter(Driver.driver_id == driver_id)
    drivers = drivers_query.order_by(Driver.full_name.asc(), Driver.driver_id.asc()).all()
    driver_ids = [driver.driver_id for driver in drivers]

    if not driver_ids:
        return {
            "summary": {
                "total_drivers": 0,
                "completed_trips": 0,
                "deliveries_with_expected_time": 0,
                "on_time_deliveries": 0,
                "on_time_delivery_rate": 0.0,
                "drivers_with_check_in": 0,
                "attendance_rate": 0.0,
            },
            "drivers": [],
        }

    trip_query = (
        db.query(Trip.driver_id, Trip.ended_at, Shipment.expected_delivery_at)
        .join(Shipment, Shipment.shipment_id == Trip.shipment_id)
        .filter(Trip.status == TripStatus.Completed, Trip.driver_id.in_(driver_ids))
    )
    completed_trips = _apply_completed_trip_dates(trip_query, start_date, end_date).all()

    attendance_query = db.query(Attendance.driver_id).filter(
        Attendance.driver_id.in_(driver_ids),
        Attendance.activity_type == AttendanceActivityType.CheckIn,
    )
    if start_date is not None:
        attendance_query = attendance_query.filter(Attendance.occurred_at >= start_date)
    if end_date is not None:
        attendance_query = attendance_query.filter(Attendance.occurred_at <= end_date)
    checked_in_driver_ids = {row[0] for row in attendance_query.distinct().all()}

    trips_by_driver = {item: [] for item in driver_ids}
    for trip in completed_trips:
        trips_by_driver.setdefault(trip.driver_id, []).append(trip)

    items = []
    total_evaluable = 0
    total_on_time = 0
    for driver in drivers:
        driver_trips = trips_by_driver.get(driver.driver_id, [])
        evaluable = [
            trip
            for trip in driver_trips
            if trip.ended_at is not None and trip.expected_delivery_at is not None
        ]
        on_time = [trip for trip in evaluable if trip.ended_at <= trip.expected_delivery_at]
        total_evaluable += len(evaluable)
        total_on_time += len(on_time)
        check_ins = 1 if driver.driver_id in checked_in_driver_ids else 0
        items.append(
            {
                "driver_id": driver.driver_id,
                "full_name": driver.full_name,
                "status": _value(driver.status),
                "trips_completed": len(driver_trips),
                "deliveries_with_expected_time": len(evaluable),
                "on_time_deliveries": len(on_time),
                "on_time_delivery_rate": _percentage(len(on_time), len(evaluable)),
                "attendance_check_ins": check_ins,
                "attendance_rate": 100.0 if check_ins else 0.0,
            }
        )

    return {
        "summary": {
            "total_drivers": len(drivers),
            "completed_trips": len(completed_trips),
            "deliveries_with_expected_time": total_evaluable,
            "on_time_deliveries": total_on_time,
            "on_time_delivery_rate": _percentage(total_on_time, total_evaluable),
            "drivers_with_check_in": len(checked_in_driver_ids),
            "attendance_rate": _percentage(len(checked_in_driver_ids), len(drivers)),
        },
        "drivers": items,
    }


def delivery_performance(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    trip_query = (
        db.query(Trip, Shipment)
        .join(Shipment, Shipment.shipment_id == Trip.shipment_id)
        .filter(Trip.status == TripStatus.Completed, Shipment.status == ShipmentStatus.Delivered)
        .order_by(Trip.ended_at.desc(), Trip.trip_id.desc())
    )
    rows = _apply_completed_trip_dates(trip_query, start_date, end_date).all()

    # A shipment is counted once. If historical data contains multiple completed
    # trips for the same shipment, the most recently completed trip represents it.
    latest_trip_by_shipment = {}
    for trip, shipment in rows:
        latest_trip_by_shipment.setdefault(shipment.shipment_id, (trip, shipment))
    completed = list(latest_trip_by_shipment.values())

    evaluable = [
        (trip, shipment)
        for trip, shipment in completed
        if trip.ended_at is not None and shipment.expected_delivery_at is not None
    ]
    on_time = [
        item
        for item in evaluable
        if item[0].ended_at <= item[1].expected_delivery_at
    ]
    delayed = [
        item
        for item in evaluable
        if item[0].ended_at > item[1].expected_delivery_at
    ]
    durations = [
        (trip.ended_at - trip.started_at).total_seconds()
        for trip, _ in completed
        if trip.started_at is not None and trip.ended_at is not None and trip.ended_at >= trip.started_at
    ]

    return {
        "completed_deliveries": len(completed),
        "deliveries_with_expected_time": len(evaluable),
        "on_time_deliveries": len(on_time),
        "delayed_deliveries": len(delayed),
        "on_time_rate": _percentage(len(on_time), len(evaluable)),
        "delayed_rate": _percentage(len(delayed), len(evaluable)),
        "deliveries_with_duration": len(durations),
        "average_delivery_time_seconds": round(sum(durations) / len(durations), 2) if durations else None,
    }


def maintenance_analytics(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    maintenance_query = db.query(Maintenance).filter(
        Maintenance.status.in_([MaintenanceStatus.Completed, MaintenanceStatus.Resolved])
    )
    if start_date is not None:
        maintenance_query = maintenance_query.filter(Maintenance.service_date >= start_date)
    if end_date is not None:
        maintenance_query = maintenance_query.filter(Maintenance.service_date <= end_date)
    records = maintenance_query.all()

    vehicles = {
        vehicle.vehicle_id: vehicle.registration_number
        for vehicle in db.query(Vehicle).filter(Vehicle.vehicle_id.in_([record.vehicle_id for record in records] or [None])).all()
    }
    costs_by_vehicle: dict[UUID, dict] = {}
    frequency_by_type: dict[str, int] = {}
    total_cost = Decimal("0")

    for record in records:
        cost = record.cost or Decimal("0")
        total_cost += cost
        item = costs_by_vehicle.setdefault(
            record.vehicle_id,
            {
                "vehicle_id": record.vehicle_id,
                "registration_number": vehicles.get(record.vehicle_id),
                "total_maintenance_cost": Decimal("0"),
                "maintenance_count": 0,
            },
        )
        item["total_maintenance_cost"] += cost
        item["maintenance_count"] += 1
        frequency_by_type[record.maintenance_type] = frequency_by_type.get(record.maintenance_type, 0) + 1

    return {
        "completed_maintenance_count": len(records),
        "total_maintenance_cost": float(total_cost),
        "cost_by_vehicle": [
            {**item, "total_maintenance_cost": float(item["total_maintenance_cost"])}
            for _, item in sorted(costs_by_vehicle.items(), key=lambda pair: str(pair[0]))
        ],
        "frequency_by_type": [
            {"maintenance_type": maintenance_type, "maintenance_count": count}
            for maintenance_type, count in sorted(frequency_by_type.items())
        ],
    }


def _fuel_records_for_period(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[FuelRecord]:
    query = db.query(FuelRecord).filter(
        FuelRecord.vehicle_id.isnot(None),
        FuelRecord.fuel_amount.isnot(None),
        FuelRecord.fuel_amount > 0,
        FuelRecord.refill_date.isnot(None),
    )
    if start_date is not None:
        query = query.filter(FuelRecord.refill_date >= start_date)
    if end_date is not None:
        query = query.filter(FuelRecord.refill_date <= end_date)
    return query.order_by(FuelRecord.refill_date.asc(), FuelRecord.fuel_id.asc()).all()


def _registration_numbers(db: Session, vehicle_ids) -> dict:
    if not vehicle_ids:
        return {}
    return {
        vehicle.vehicle_id: vehicle.registration_number
        for vehicle in db.query(Vehicle).filter(Vehicle.vehicle_id.in_(vehicle_ids)).all()
    }


def fuel_efficiency(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    vehicle_id: UUID | None = None,
) -> dict:
    records = _fuel_records_for_period(db, start_date, end_date)
    if vehicle_id is not None:
        records = [record for record in records if record.vehicle_id == vehicle_id]

    fuel_by_vehicle: dict[UUID, Decimal] = {}
    for record in records:
        fuel_by_vehicle[record.vehicle_id] = fuel_by_vehicle.get(record.vehicle_id, Decimal("0")) + record.fuel_amount

    vehicle_ids = list(fuel_by_vehicle)
    registrations = _registration_numbers(db, vehicle_ids)
    trips_query = db.query(Trip).filter(
        Trip.status == TripStatus.Completed,
        Trip.vehicle_id.in_(vehicle_ids or [None]),
    )
    trips = _apply_completed_trip_dates(trips_query, start_date, end_date).all()

    distances = {
        identifier: {"actual": 0.0, "estimated": 0.0, "trips": 0}
        for identifier in vehicle_ids
    }
    for trip in trips:
        if trip.actual_distance_meters is not None and (
            trip.planned_distance is None or trip.actual_distance_meters != trip.planned_distance
        ):
            distances[trip.vehicle_id]["actual"] += float(trip.actual_distance_meters)
        elif trip.planned_distance is not None:
            # The current trip lifecycle can copy planned distance into
            # actual_distance_meters. Equal values are conservatively estimated.
            distances[trip.vehicle_id]["estimated"] += float(trip.planned_distance)
        elif trip.actual_distance_meters is not None:
            distances[trip.vehicle_id]["actual"] += float(trip.actual_distance_meters)
        else:
            continue
        distances[trip.vehicle_id]["trips"] += 1

    vehicles = []
    for identifier in sorted(vehicle_ids, key=str):
        fuel_consumed = float(fuel_by_vehicle[identifier])
        distance = distances[identifier]
        distance_used = distance["actual"] + distance["estimated"]
        vehicles.append(
            {
                "vehicle_id": identifier,
                "registration_number": registrations.get(identifier),
                "fuel_consumed": fuel_consumed,
                "completed_trips": distance["trips"],
                "actual_distance_meters": round(distance["actual"], 2),
                "estimated_distance_meters": round(distance["estimated"], 2),
                "distance_used_meters": round(distance_used, 2),
                "fuel_efficiency_km_per_fuel_unit": round(distance_used / 1000 / fuel_consumed, 4)
                if fuel_consumed > 0 and distance_used > 0
                else None,
            }
        )

    total_fuel = sum(item["fuel_consumed"] for item in vehicles)
    total_actual = sum(item["actual_distance_meters"] for item in vehicles)
    total_estimated = sum(item["estimated_distance_meters"] for item in vehicles)
    total_distance = total_actual + total_estimated
    return {
        "total_fuel_consumed": round(total_fuel, 3),
        "actual_distance_meters": round(total_actual, 2),
        "estimated_distance_meters": round(total_estimated, 2),
        "distance_used_meters": round(total_distance, 2),
        "fuel_efficiency_km_per_fuel_unit": round(total_distance / 1000 / total_fuel, 4)
        if total_fuel > 0 and total_distance > 0
        else None,
        "vehicles": vehicles,
    }


def fuel_cost_trends(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    vehicle_id: UUID | None = None,
) -> dict:
    records = _fuel_records_for_period(db, start_date, end_date)
    if vehicle_id is not None:
        records = [record for record in records if record.vehicle_id == vehicle_id]

    registrations = _registration_numbers(db, {record.vehicle_id for record in records})
    costs_by_vehicle: dict[UUID, dict] = {}
    costs_by_date: dict[str, dict] = {}
    for record in records:
        fuel_amount = float(record.fuel_amount)
        fuel_cost = float(record.fuel_cost or 0)
        vehicle = costs_by_vehicle.setdefault(
            record.vehicle_id,
            {
                "vehicle_id": record.vehicle_id,
                "registration_number": registrations.get(record.vehicle_id),
                "refill_count": 0,
                "total_fuel_consumed": 0.0,
                "total_fuel_cost": 0.0,
            },
        )
        vehicle["refill_count"] += 1
        vehicle["total_fuel_consumed"] += fuel_amount
        vehicle["total_fuel_cost"] += fuel_cost

        date_key = record.refill_date.date().isoformat()
        period = costs_by_date.setdefault(
            date_key,
            {"date": date_key, "refill_count": 0, "total_fuel_consumed": 0.0, "total_fuel_cost": 0.0},
        )
        period["refill_count"] += 1
        period["total_fuel_consumed"] += fuel_amount
        period["total_fuel_cost"] += fuel_cost

    def rounded(item: dict) -> dict:
        return {
            **item,
            "total_fuel_consumed": round(item["total_fuel_consumed"], 3),
            "total_fuel_cost": round(item["total_fuel_cost"], 2),
        }

    return {
        "total_refills": len(records),
        "total_fuel_consumed": round(sum(float(record.fuel_amount) for record in records), 3),
        "total_fuel_cost": round(sum(float(record.fuel_cost or 0) for record in records), 2),
        "cost_by_vehicle": [rounded(item) for _, item in sorted(costs_by_vehicle.items(), key=lambda pair: str(pair[0]))],
        "cost_over_time": [rounded(item) for _, item in sorted(costs_by_date.items())],
    }


def operational_summary(
    db: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    drivers = driver_performance(db, start_date=start_date, end_date=end_date)
    return {
        "fleet_utilization": fleet_utilization(db),
        "driver_performance": drivers["summary"],
        "delivery_performance": delivery_performance(db, start_date=start_date, end_date=end_date),
        "maintenance_summary": maintenance_analytics(db, start_date=start_date, end_date=end_date),
    }
