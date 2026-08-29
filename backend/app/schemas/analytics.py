from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StatusDistribution(BaseModel):
    count: int
    percentage: float


class FleetUtilizationResponse(BaseModel):
    total_fleet: int
    statuses: dict[str, StatusDistribution]


class DriverPerformanceItem(BaseModel):
    driver_id: UUID
    full_name: str | None
    status: str
    trips_completed: int
    deliveries_with_expected_time: int
    on_time_deliveries: int
    on_time_delivery_rate: float
    attendance_check_ins: int
    attendance_rate: float


class DriverPerformanceSummary(BaseModel):
    total_drivers: int
    completed_trips: int
    deliveries_with_expected_time: int
    on_time_deliveries: int
    on_time_delivery_rate: float
    drivers_with_check_in: int
    attendance_rate: float


class DriverPerformanceResponse(BaseModel):
    summary: DriverPerformanceSummary
    drivers: list[DriverPerformanceItem]


class DeliveryPerformanceResponse(BaseModel):
    completed_deliveries: int
    deliveries_with_expected_time: int
    on_time_deliveries: int
    delayed_deliveries: int
    on_time_rate: float
    delayed_rate: float
    deliveries_with_duration: int
    average_delivery_time_seconds: float | None


class MaintenanceVehicleCost(BaseModel):
    vehicle_id: UUID
    registration_number: str | None = None
    total_maintenance_cost: float
    maintenance_count: int


class MaintenanceTypeFrequency(BaseModel):
    maintenance_type: str
    maintenance_count: int


class MaintenanceAnalyticsResponse(BaseModel):
    completed_maintenance_count: int
    total_maintenance_cost: float
    cost_by_vehicle: list[MaintenanceVehicleCost]
    frequency_by_type: list[MaintenanceTypeFrequency]


class AnalyticsPeriod(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None


class OperationalSummaryResponse(BaseModel):
    fleet_utilization: FleetUtilizationResponse
    driver_performance: DriverPerformanceSummary
    delivery_performance: DeliveryPerformanceResponse
    maintenance_summary: MaintenanceAnalyticsResponse


class FuelEfficiencyVehicle(BaseModel):
    vehicle_id: UUID
    registration_number: str | None = None
    fuel_consumed: float
    completed_trips: int
    actual_distance_meters: float
    estimated_distance_meters: float
    distance_used_meters: float
    fuel_efficiency_km_per_fuel_unit: float | None


class FuelEfficiencyResponse(BaseModel):
    total_fuel_consumed: float
    actual_distance_meters: float
    estimated_distance_meters: float
    distance_used_meters: float
    fuel_efficiency_km_per_fuel_unit: float | None
    vehicles: list[FuelEfficiencyVehicle]


class FuelCostByVehicle(BaseModel):
    vehicle_id: UUID
    registration_number: str | None = None
    refill_count: int
    total_fuel_consumed: float
    total_fuel_cost: float


class FuelCostOverTime(BaseModel):
    date: str
    refill_count: int
    total_fuel_consumed: float
    total_fuel_cost: float


class FuelCostTrendsResponse(BaseModel):
    total_refills: int
    total_fuel_consumed: float
    total_fuel_cost: float
    cost_by_vehicle: list[FuelCostByVehicle]
    cost_over_time: list[FuelCostOverTime]
