import json
import hashlib
import httpx
import redis.asyncio as redis


OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

REDIS_URL = "redis://localhost:6379/0"


async def get_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
):
    """
    Get driving route from OSRM.

    Returns:
        distance_meters
        duration_seconds
        geometry
    """

    # --------------------------------------------------
    # Create deterministic cache key
    # --------------------------------------------------

    raw_key = (
        f"{start_lat:.6f}:"
        f"{start_lon:.6f}:"
        f"{end_lat:.6f}:"
        f"{end_lon:.6f}"
    )

    key_hash = hashlib.sha256(
        raw_key.encode()
    ).hexdigest()

    cache_key = f"fleetflow:route:{key_hash}"

    # --------------------------------------------------
    # Check Redis cache (optional, non-blocking fallback)
    # --------------------------------------------------
    redis_client = None
    try:
        redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
        )
        cached = await redis_client.get(cache_key)

        if cached:
            await redis_client.close()
            result = json.loads(cached)
            result["cached"] = True
            return result
    except Exception:
        if redis_client:
            try:
                await redis_client.close()
            except Exception:
                pass
        redis_client = None

    # --------------------------------------------------
    # Call OSRM
    # --------------------------------------------------

    coordinates = (
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
    )

    url = f"{OSRM_URL}/{coordinates}"

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
    }

    async with httpx.AsyncClient(timeout=15) as client:

        response = await client.get(
            url,
            params=params,
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"OSRM request failed: "
            f"{response.status_code}"
        )

    data = response.json()

    if data.get("code") != "Ok":
        raise RuntimeError(
            f"OSRM routing failed: "
            f"{data.get('code')}"
        )

    route = data["routes"][0]

    result = {
        "distance_meters": route["distance"],
        "duration_seconds": route["duration"],
        "geometry": route["geometry"],
        "cached": False,
    }

    # --------------------------------------------------
    # Store in Redis (optional)
    # --------------------------------------------------

    if redis_client is not None:
        try:
            await redis_client.setex(
                cache_key,
                300,
                json.dumps(result),
            )
            await redis_client.close()
        except Exception:
            pass

    return result