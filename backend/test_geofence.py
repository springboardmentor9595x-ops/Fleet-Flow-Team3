from app.core.geofence import is_inside_zone


vehicle_lat = 11.0168
vehicle_lon = 76.9558

destination_lat = 11.0168
destination_lon = 76.9558

result = is_inside_zone(
    vehicle_lat,
    vehicle_lon,
    destination_lat,
    destination_lon,
)

if result:
    print("ARRIVED_AT_DESTINATION")
else:
    print("Vehicle is outside destination zone")