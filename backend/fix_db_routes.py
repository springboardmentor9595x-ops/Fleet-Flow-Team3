import asyncio
import os
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from app.services.routing import get_route

DATABASE_URL = "postgresql://postgres:4973@localhost:5432/fleetflow_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

KNOWN_COORDS = {
    "greater noida": (28.4744, 77.5040),
    "delhi": (28.6139, 77.2090),
    "gujarat": (23.0225, 72.5714),
    "mumbai": (19.0760, 72.8777),
}

async def backfill_routes():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT trip_id, start_location, destination FROM trips"))
        trips = result.fetchall()
        
        for trip in trips:
            trip_id = trip[0]
            start_loc = trip[1].lower()
            dest_loc = trip[2].lower()
            
            print(f"Fixing trip {trip_id}: {start_loc} -> {dest_loc}")
            try:
                start_coords = KNOWN_COORDS.get(start_loc, (28.6139, 77.2090))
                dest_coords = KNOWN_COORDS.get(dest_loc, (28.6139, 77.2090))
                
                route_data = await get_route(start_coords[0], start_coords[1], dest_coords[0], dest_coords[1], "Fastest")
                if route_data:
                    geom = json.dumps(route_data["geometry"])
                    dist = route_data["distance_meters"] / 1000
                    dur_str = f"{int(route_data['duration_seconds'] // 60)}h {int(route_data['duration_seconds'] % 60)}m"
                    
                    db.execute(text("UPDATE trips SET route_geometry = :geom, distance = :dist, estimated_duration = :dur WHERE trip_id = :tid"),
                               {"geom": geom, "dist": dist, "dur": dur_str, "tid": trip_id})
                    db.commit()
                    print(f"Updated {trip_id}")
            except Exception as e:
                print(f"Failed to fix {trip_id}: {e}")
                
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(backfill_routes())
