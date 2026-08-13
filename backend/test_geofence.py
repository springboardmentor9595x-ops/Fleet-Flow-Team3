from app.core.geofence import (
    calculate_distance,
    is_inside_geofence,
)


# Example destination
destination_latitude = 28.4744
destination_longitude = 77.5040


# Vehicle GPS position
vehicle_latitude = 28.4744
vehicle_longitude = 77.5040


distance = calculate_distance(
    vehicle_latitude,
    vehicle_longitude,
    destination_latitude,
    destination_longitude,
)

print(f"Distance from destination: {distance:.2f} meters")


if is_inside_geofence(
    vehicle_latitude,
    vehicle_longitude,
    destination_latitude,
    destination_longitude,
    radius_meters=500,
):
    print("EVENT: Vehicle arrived at destination")
else:
    print("Vehicle is outside destination zone")