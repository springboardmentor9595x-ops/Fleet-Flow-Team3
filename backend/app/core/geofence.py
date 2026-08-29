from math import radians, sin, cos, sqrt, atan2


def calculate_distance(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    """
    Calculate distance between two GPS coordinates in meters.
    """

    earth_radius = 6371000

    lat1 = radians(latitude1)
    lat2 = radians(latitude2)

    delta_lat = radians(latitude2 - latitude1)
    delta_lon = radians(longitude2 - longitude1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def is_inside_zone(
    vehicle_latitude: float,
    vehicle_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
    radius_meters: float = 500,
) -> bool:

    distance = calculate_distance(
        vehicle_latitude,
        vehicle_longitude,
        destination_latitude,
        destination_longitude,
    )

    return distance <= radius_meters


def get_geofence_event(
    was_inside: bool | None,
    is_inside: bool,
) -> str | None:
    if was_inside is None and is_inside:
        return "geofence_entered"
    if was_inside is False and is_inside:
        return "geofence_entered"
    if was_inside is True and not is_inside:
        return "geofence_exited"
    return None
