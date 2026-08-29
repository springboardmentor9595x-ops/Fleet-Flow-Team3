"""Nominatim and OSRM integration for non-traffic-aware trip routing."""
import json
from datetime import datetime, timedelta, timezone
from math import atan2, cos, radians, sin, sqrt
from urllib.parse import urlencode
from urllib.request import Request, urlopen

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
ROUTE_TYPES = {"Fastest", "Shortest", "Eco", "Balanced"}


def _get_json(url: str) -> dict | list:
    request = Request(url, headers={"User-Agent": "FleetFlow-Internship/1.0 (route planning)"})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def geocode(address: str) -> tuple[float, float] | None:
    try:
        results = _get_json(f"{NOMINATIM_URL}?{urlencode({'q': address, 'format': 'jsonv2', 'limit': 1})}")
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        return None
    return None


def haversine_meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (*a, *b))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6_371_000 * 2 * atan2(sqrt(value), sqrt(1 - value))


def _select_route(routes: list[dict], route_type: str) -> dict:
    if route_type == "Fastest":
        return min(routes, key=lambda item: item["duration"])
    if route_type == "Shortest":
        return min(routes, key=lambda item: item["distance"])
    if route_type == "Eco":
        return min(routes, key=lambda item: item["distance"] * 0.7 + item["duration"] * 8)
    shortest = min(item["distance"] for item in routes)
    fastest = min(item["duration"] for item in routes)
    return min(routes, key=lambda item: item["distance"] / shortest + item["duration"] / fastest)


def build_route(source: str, destination: str, route_type: str) -> dict:
    if route_type not in ROUTE_TYPES:
        raise ValueError("Unsupported route type")
    start, end = geocode(source), geocode(destination)
    if start is None or end is None:
        return {"error": "Unable to find the source or destination location."}
    try:
        url = f"{OSRM_URL}/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson&alternatives=true"
        routes = _get_json(url).get("routes", [])
        if not routes:
            raise ValueError("OSRM did not return a route")
        selected = _select_route(routes, route_type)
        return {"distance_meters": selected["distance"], "duration_seconds": selected["duration"], "geometry": selected["geometry"]["coordinates"], "fallback": False}
    except Exception:
        distance = haversine_meters(start, end)
        return {"distance_meters": distance, "duration_seconds": distance / (45_000 / 3600), "geometry": [[start[1], start[0]], [end[1], end[0]]], "fallback": True}


def route_eta(duration_seconds: float | None) -> datetime | None:
    return datetime.now(timezone.utc) + timedelta(seconds=duration_seconds) if duration_seconds is not None else None


def route_remaining_metrics(
    geometry: list[list[float]] | None,
    current_latitude: float,
    current_longitude: float,
    planned_distance: float | None,
    estimated_duration: float | None,
) -> tuple[float | None, float | None]:
    """Estimate remaining route values from the GPS point nearest to the route.

    OSRM geometry is stored as ``[longitude, latitude]`` points.  The route
    shape provides a stable, traffic-independent progress estimate without
    changing the GPS database schema or calling another external service.
    """
    if not geometry or len(geometry) < 2:
        return planned_distance, estimated_duration

    route_points = [(point[1], point[0]) for point in geometry]
    current_point = (current_latitude, current_longitude)
    segment_lengths = [
        haversine_meters(route_points[index], route_points[index + 1])
        for index in range(len(route_points) - 1)
    ]
    total_shape_distance = sum(segment_lengths)

    # Project onto every route segment so the ETA changes smoothly even when
    # the fallback route only contains its start and destination coordinates.
    nearest_segment = 0
    nearest_fraction = 0.0
    nearest_distance = float("inf")
    for index, ((lat1, lon1), (lat2, lon2)) in enumerate(
        zip(route_points, route_points[1:])
    ):
        longitude_scale = cos(radians((lat1 + lat2) / 2))
        segment_x = (lon2 - lon1) * longitude_scale
        segment_y = lat2 - lat1
        point_x = (current_longitude - lon1) * longitude_scale
        point_y = current_latitude - lat1
        segment_size = segment_x**2 + segment_y**2
        fraction = (
            max(0.0, min(1.0, (point_x * segment_x + point_y * segment_y) / segment_size))
            if segment_size > 0
            else 0.0
        )
        projected_point = (
            lat1 + (lat2 - lat1) * fraction,
            lon1 + (lon2 - lon1) * fraction,
        )
        distance_to_segment = haversine_meters(current_point, projected_point)
        if distance_to_segment < nearest_distance:
            nearest_segment = index
            nearest_fraction = fraction
            nearest_distance = distance_to_segment

    remaining_shape_distance = (
        segment_lengths[nearest_segment] * (1 - nearest_fraction)
        + sum(segment_lengths[nearest_segment + 1 :])
    )
    progress_ratio = (
        max(0.0, min(1.0, remaining_shape_distance / total_shape_distance))
        if total_shape_distance > 0
        else 1.0
    )

    remaining_distance = (
        max(0.0, planned_distance * progress_ratio)
        if planned_distance is not None
        else None
    )
    remaining_duration = (
        max(0.0, estimated_duration * progress_ratio)
        if estimated_duration is not None
        else None
    )
    return remaining_distance, remaining_duration
