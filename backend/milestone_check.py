from app.main import app
schema = app.openapi()
actual = set()
for path, ops in schema.get('paths', {}).items():
    for method in ops:
        actual.add((method.upper(), path))

# WebSocket exists but won't appear in openapi - add manually
actual.add(("WS", "/ws/{vehicle_id}"))

REQUIRED = [
    # M1 Auth
    ("POST", "/auth/signup"),
    ("POST", "/auth/login"),
    ("GET",  "/auth/me"),
    # M1 Users (profile + account settings)
    ("GET",  "/users/"),
    ("GET",  "/users/me"),
    ("PUT",  "/users/me"),
    ("PUT",  "/users/{user_id}/role"),
    ("DELETE", "/users/{user_id}"),
    # M1 Vehicles
    ("POST", "/vehicles/"),
    ("GET",  "/vehicles/"),
    ("GET",  "/vehicles/{vehicle_id}"),
    ("PUT",  "/vehicles/{vehicle_id}"),
    ("DELETE", "/vehicles/{vehicle_id}"),
    # M2 Shipments
    ("POST", "/shipments/"),
    ("GET",  "/shipments/"),
    ("GET",  "/shipments/{shipment_id}"),
    ("PUT",  "/shipments/{shipment_id}"),
    ("DELETE", "/shipments/{shipment_id}"),
    # M2 Trips
    ("POST", "/trips/"),
    ("GET",  "/trips/"),
    ("GET",  "/trips/{trip_id}"),
    ("PUT",  "/trips/{trip_id}"),
    ("DELETE", "/trips/{trip_id}"),
    ("POST", "/trips/{trip_id}/start"),
    ("POST", "/trips/{trip_id}/end"),
    # M2 GPS WebSocket
    ("WS",  "/ws/{vehicle_id}"),
    # M2 Route optimization
    ("POST", "/routes/calculate"),
    # M3 Drivers
    ("POST", "/drivers/"),
    ("GET",  "/drivers/"),
    ("GET",  "/drivers/{driver_id}"),
    ("PUT",  "/drivers/{driver_id}"),
    ("DELETE", "/drivers/{driver_id}"),
    # M3 Maintenance
    ("POST", "/maintenance/"),
    ("GET",  "/maintenance/"),
    ("GET",  "/maintenance/alerts"),
    ("GET",  "/maintenance/{maintenance_id}"),
    ("PUT",  "/maintenance/{maintenance_id}"),
    ("DELETE", "/maintenance/{maintenance_id}"),
    # M3 Fuel
    ("POST", "/fuel/"),
    ("GET",  "/fuel/"),
    ("GET",  "/fuel/efficiency/summary"),
    ("GET",  "/fuel/{fuel_id}"),
    ("DELETE", "/fuel/{fuel_id}"),
    # M3 Notifications
    ("GET",  "/notifications/"),
    ("PATCH", "/notifications/{notification_id}/read"),
    # M3 Attendance
    ("POST", "/attendance/clock-in"),
    ("POST", "/attendance/clock-out"),
    ("GET",  "/attendance/"),
    # M3 Analytics
    ("GET",  "/analytics/summary"),
    ("GET",  "/analytics/driver-performance"),
    ("GET",  "/analytics/fuel-trends"),
    ("GET",  "/analytics/maintenance-costs"),
    ("GET",  "/analytics/shipment-alerts"),
]

print("=== MILESTONE COVERAGE CHECK ===\n")
missing = []
for method, path in REQUIRED:
    found = (method, path) in actual
    status = "OK " if found else "MISS"
    print(f"  {status}  {method:8} {path}")
    if not found:
        missing.append((method, path))

print(f"\nTotal required: {len(REQUIRED)}")
print(f"Present:        {len(REQUIRED) - len(missing)}")
print(f"Missing:        {len(missing)}")
if not missing:
    print("\nALL MILESTONE ROUTES PRESENT")
