import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { divIcon } from "leaflet";
import {
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import MainLayout from "../layouts/MainLayout";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./LiveTracking.css";

const RECONNECT_DELAY_MS = 3000;
const HEARTBEAT_INTERVAL_MS = 25000;
const SELECTED_VEHICLE_KEY = "selectedVehicle";

function getVehicleIcon(vehicleType = "") {
  const type = vehicleType.toLowerCase();
  const icon = type.includes("truck")
    ? "&#x1F69A;"
    : type.includes("car")
      ? "&#x1F697;"
      : type.includes("van")
        ? "&#x1F690;"
        : type.includes("bus")
          ? "&#x1F68C;"
          : "&#x1F699;";

  return divIcon({
    className: "tracking-vehicle-icon",
    html: `<span role="img" aria-label="${vehicleType || "Vehicle"}">${icon}</span>`,
    iconSize: [44, 44],
    iconAnchor: [22, 22],
  });
}

function MapController({ route, location, followVehicle, centerRequest }) {
  const map = useMap();
  const fittedRouteRef = useRef(null);

  useEffect(() => {
    const points = route?.map(([longitude, latitude]) => [latitude, longitude]) || [];
    const routeKey = points.length
      ? `${points[0]}-${points[points.length - 1]}-${points.length}`
      : "";

    if (points.length > 1 && routeKey !== fittedRouteRef.current) {
      map.fitBounds(points, { padding: [34, 34] });
      fittedRouteRef.current = routeKey;
    }
  }, [map, route]);

  useEffect(() => {
    if (location && followVehicle) {
      map.panTo([location.latitude, location.longitude], {
        animate: true,
        duration: 0.8,
      });
    }
  }, [followVehicle, location, map]);

  useEffect(() => {
    if (centerRequest && location) {
      map.setView(
        [location.latitude, location.longitude],
        Math.max(map.getZoom(), 14),
        { animate: true }
      );
    }
  }, [centerRequest, location, map]);

  return null;
}

function calculateRouteProgress(geometry, currentLocation) {
  if (!geometry?.length || !currentLocation) {
    return 0;
  }

  let closestIndex = 0;
  let closestDistance = Number.POSITIVE_INFINITY;

  geometry.forEach(([longitude, latitude], index) => {
    const distance =
      (latitude - Number(currentLocation.latitude)) ** 2 +
      (longitude - Number(currentLocation.longitude)) ** 2;

    if (distance < closestDistance) {
      closestDistance = distance;
      closestIndex = index;
    }
  });

  return geometry.length > 1
    ? (closestIndex / (geometry.length - 1)) * 100
    : 0;
}

function getHeading(previous, next) {
  if (!previous || !next) {
    return "-";
  }

  const longitudeDifference = ((next.longitude - previous.longitude) * Math.PI) / 180;
  const latitude1 = (previous.latitude * Math.PI) / 180;
  const latitude2 = (next.latitude * Math.PI) / 180;
  const bearing = Math.atan2(
    Math.sin(longitudeDifference) * Math.cos(latitude2),
    Math.cos(latitude1) * Math.sin(latitude2) -
      Math.sin(latitude1) * Math.cos(latitude2) * Math.cos(longitudeDifference)
  );

  return `${Math.round(((bearing * 180) / Math.PI + 360) % 360)}\u00B0`;
}

function relativeTime(recordedTime, now) {
  if (!recordedTime) {
    return "Waiting for GPS";
  }

  const locationTime = new Date(recordedTime).getTime();
  const referenceTime = now ?? locationTime;
  const seconds = Math.max(0, Math.floor((referenceTime - locationTime) / 1000));

  if (seconds < 5) return "Updated just now";
  if (seconds < 60) return `Updated ${seconds} seconds ago`;
  return `Updated ${Math.floor(seconds / 60)} minutes ago`;
}

function LiveTracking() {
  const { user } = useContext(AuthContext);
  const [vehicles, setVehicles] = useState([]);
  const [trips, setTrips] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [vehicleId, setVehicleId] = useState(
    () => localStorage.getItem(SELECTED_VEHICLE_KEY) || ""
  );
  const [location, setLocation] = useState(null);
  const [heading, setHeading] = useState("-");
  const [route, setRoute] = useState(null);
  const [connectionState, setConnectionState] = useState("Connecting");
  const [geofenceEvent, setGeofenceEvent] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [followVehicle, setFollowVehicle] = useState(true);
  const [centerRequest, setCenterRequest] = useState(0);
  const [now, setNow] = useState(null);

  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const heartbeatTimerRef = useRef(null);
  const previousLocationRef = useRef(null);
  const mapFrameRef = useRef(null);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date().getTime()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadTrackingData = async () => {
      try {
        const [vehicleResponse, tripResponse, driverResponse] = await Promise.all([
          api.get("/vehicles/"),
          api.get("/trips/"),
          api.get("/drivers/"),
        ]);

        if (cancelled) return;

        const loadedVehicles = vehicleResponse.data;
        const loadedTrips = tripResponse.data;
        const activeDriverVehicles = loadedVehicles.filter((vehicle) =>
          loadedTrips.some(
            (trip) => trip.vehicle_id === vehicle.vehicle_id && trip.status === "Active"
          )
        );
        const availableVehicles =
          user?.role === "Driver" ? activeDriverVehicles : loadedVehicles;
        const savedVehicleId = localStorage.getItem(SELECTED_VEHICLE_KEY);
        const initialVehicleId =
          availableVehicles.find((vehicle) => vehicle.vehicle_id === savedVehicleId)
            ?.vehicle_id ||
          availableVehicles[0]?.vehicle_id ||
          "";

        setVehicles(loadedVehicles);
        setTrips(loadedTrips);
        setDrivers(driverResponse.data);
        setVehicleId(initialVehicleId);

        if (initialVehicleId) {
          localStorage.setItem(SELECTED_VEHICLE_KEY, initialVehicleId);
        } else {
          localStorage.removeItem(SELECTED_VEHICLE_KEY);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(
            requestError.response?.data?.detail ||
              "Unable to load live tracking data."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadTrackingData();
    return () => {
      cancelled = true;
    };
  }, [user?.role]);

  const visibleVehicles = useMemo(() => {
    if (user?.role !== "Driver") {
      return vehicles;
    }

    return vehicles.filter((vehicle) =>
      trips.some(
        (trip) => trip.vehicle_id === vehicle.vehicle_id && trip.status === "Active"
      )
    );
  }, [trips, user?.role, vehicles]);

  const selectedTrip = useMemo(
    () =>
      trips.find(
        (trip) => trip.vehicle_id === vehicleId && trip.status === "Active"
      ) ||
      trips.find(
        (trip) => trip.vehicle_id === vehicleId && trip.status === "Scheduled"
      ),
    [trips, vehicleId]
  );
  const selectedVehicle = vehicles.find(
    (vehicle) => vehicle.vehicle_id === vehicleId
  );
  const selectedDriver = drivers.find(
    (driver) => driver.driver_id === selectedTrip?.driver_id
  );

  useEffect(() => {
    if (!selectedTrip) {
      const resetRouteTimer = window.setTimeout(() => setRoute(null), 0);
      return () => window.clearTimeout(resetRouteTimer);
    }

    let current = true;
    api
      .get(`/trips/${selectedTrip.trip_id}/route`)
      .then((response) => {
        if (current) setRoute(response.data);
      })
      .catch(() => {
        if (current) setRoute(null);
      });

    return () => {
      current = false;
    };
  }, [selectedTrip]);

  useEffect(() => {
    if (!vehicleId) {
      return undefined;
    }

    let active = true;
    const isTripActive = selectedTrip?.status === "Active";

    const closeTimers = () => {
      window.clearTimeout(reconnectTimerRef.current);
      window.clearInterval(heartbeatTimerRef.current);
    };

    const connect = () => {
      if (!active) return;

      const token = localStorage.getItem("token");
      const wsUrl = `${api.defaults.baseURL.replace(/^http/, "ws")}/gps/ws/${vehicleId}?token=${encodeURIComponent(token || "")}`;
      console.log("Opening WebSocket:", wsUrl);

      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;
      setConnectionState("Connecting");

      socket.onopen = () => {
        console.log("WebSocket connected");
        if (!active) {
          socket.close();
          return;
        }

        setConnectionState("Connected");
        window.clearInterval(heartbeatTimerRef.current);
        heartbeatTimerRef.current = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "heartbeat" }));
          }
        }, HEARTBEAT_INTERVAL_MS);
      };

      socket.onmessage = (event) => {
        let message;

        try {
          message = JSON.parse(event.data);
        } catch {
          return;
        }

        console.log("WS Message:", message);

        if (message.type === "location_update") {
          if (!isTripActive) {
            return;
          }
          const nextLocation = message.location;
          const nextHeading =
            nextLocation.heading !== undefined && nextLocation.heading !== null
              ? `${Math.round(nextLocation.heading)}\u00B0`
              : getHeading(previousLocationRef.current, nextLocation);

          setHeading(nextHeading);
          previousLocationRef.current = nextLocation;
          setLocation(nextLocation);
          if (message.trip_metrics) {
            setRoute((currentRoute) =>
              currentRoute
                ? { ...currentRoute, ...message.trip_metrics }
                : currentRoute
            );
          }
          setGeofenceEvent("");
        }

        if (message.type === "geofence_entered") {
          setGeofenceEvent("Vehicle entered the destination zone.");
        }

        if (message.type === "geofence_exited") {
          setGeofenceEvent("Vehicle exited the destination zone.");
        }

        if (message.type === "error") {
          setError("GPS update was rejected by the server.");
        }
      };

      socket.onerror = () => {
        if (active) setConnectionState("Reconnecting");
      };

      socket.onclose = () => {
        console.log("WebSocket closed");
        window.clearInterval(heartbeatTimerRef.current);

        if (active) {
          setConnectionState("Reconnecting");
          reconnectTimerRef.current = window.setTimeout(
            connect,
            RECONNECT_DELAY_MS
          );
        }
      };
    };

    const loadLatestLocationThenConnect = async () => {
      try {
        const response = await api.get(`/gps/latest/${vehicleId}`);
        if (!active) return;

        console.log("Latest GPS loaded:", response.data);
        previousLocationRef.current = response.data;
        setLocation(response.data);
        setHeading(
          response.data.heading !== undefined && response.data.heading !== null
            ? `${Math.round(response.data.heading)}\u00B0`
            : "-"
        );
        setError("");
      } catch (requestError) {
        if (!active) return;

        previousLocationRef.current = null;
        setLocation(null);
        setHeading("-");

        if (requestError.response?.status && requestError.response.status !== 404) {
          setError(
            requestError.response?.data?.detail ||
              "Unable to load the latest GPS location."
          );
        }
      } finally {
        if (active && isTripActive) {
          connect();
        } else if (active) {
          setConnectionState("Offline");
        }
      }
    };

    void loadLatestLocationThenConnect();

    return () => {
      active = false;
      closeTimers();
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
    };
  }, [vehicleId, selectedTrip?.status]);

  useEffect(() => {
    const updateFullscreen = () => {
      setIsFullscreen(document.fullscreenElement === mapFrameRef.current);
    };

    document.addEventListener("fullscreenchange", updateFullscreen);
    return () => document.removeEventListener("fullscreenchange", updateFullscreen);
  }, []);

  const selectVehicle = (nextVehicleId) => {
    previousLocationRef.current = null;
    setLocation(null);
    setHeading("-");
    setVehicleId(nextVehicleId);

    if (nextVehicleId) {
      localStorage.setItem(SELECTED_VEHICLE_KEY, nextVehicleId);
    } else {
      localStorage.removeItem(SELECTED_VEHICLE_KEY);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading Live Tracking Operations Center..." />
      </MainLayout>
    );
  }

  const routePositions =
    route?.geometry?.map(([longitude, latitude]) => [latitude, longitude]) || [];
  const mapCenter =
    routePositions[0] ||
    (location
      ? [location.latitude, location.longitude]
      : [11.0168, 76.9558]);
  const connectionLabel =
    connectionState === "Connected"
      ? "Connected"
      : connectionState === "Offline"
        ? "Offline"
        : "Reconnecting";
  const progress = Math.round(calculateRouteProgress(route?.geometry, location));
  const remainingSeconds = route?.remaining_duration ??
    (route?.estimated_duration
      ? Math.max(
          0,
          Math.round((route.estimated_duration * (100 - progress)) / 100)
        )
      : null);
  const liveEta =
    remainingSeconds === null
      ? "-"
      : remainingSeconds < 60
        ? "Arriving now"
        : `${Math.ceil(remainingSeconds / 60)} min remaining`;

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Operations / Live Tracking"
        title="Live Tracking Operations Center"
        description="Monitor vehicle location, route progress, GPS telemetry, and delivery status in real time."
      />

      {error && (
        <section className="tracking-saas-alert error">
          <span>!</span>
          <div>
            <strong>Tracking update issue</strong>
            <p>{error}</p>
          </div>
        </section>
      )}

      {geofenceEvent && (
        <section className="tracking-saas-alert geofence">
          <span>GPS</span>
          <div>
            <strong>Geofence event</strong>
            <p>{geofenceEvent}</p>
          </div>
        </section>
      )}

      <section className="tracking-overview-card">
        <div className="tracking-overview-heading">
          <div>
            <p>Vehicle overview</p>
            <h2>{selectedVehicle?.registration_number || "Select a vehicle"}</h2>
          </div>
          <div className={`tracking-connection ${connectionLabel.toLowerCase()}`}>
            <i />
            {connectionLabel}
          </div>
        </div>

        <div className="tracking-overview-grid">
          <label className="tracking-vehicle-select">
            <span>Active vehicle</span>
            <select
              value={vehicleId}
              onChange={(event) => selectVehicle(event.target.value)}
              disabled={!visibleVehicles.length}
            >
              <option value="">
                {visibleVehicles.length
                  ? "Select a vehicle"
                  : "No assigned active vehicle"}
              </option>
              {visibleVehicles.map((vehicle) => (
                <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                  {vehicle.registration_number} - {vehicle.vehicle_type}
                </option>
              ))}
            </select>
          </label>

          <div>
            <span>Driver</span>
            <strong>{selectedDriver?.full_name || "Assigned driver"}</strong>
          </div>

          <div>
            <span>Last GPS update</span>
            <strong>{relativeTime(location?.recorded_time, now)}</strong>
          </div>

          <div>
            <span>Trip status</span>
            {selectedTrip ? (
              <StatusBadge status={selectedTrip.status} />
            ) : (
              <strong>No active trip</strong>
            )}
          </div>
        </div>
      </section>

      <section className="tracking-telemetry-grid">
        <article>
          <span className="telemetry-icon">SPD</span>
          <p>Speed</p>
          <strong>
            {location?.speed ?? 0}
            <small> km/h</small>
          </strong>
        </article>
        <article>
          <span className="telemetry-icon">LAT</span>
          <p>Latitude</p>
          <strong>{location ? Number(location.latitude).toFixed(5) : "-"}</strong>
        </article>
        <article>
          <span className="telemetry-icon">LON</span>
          <p>Longitude</p>
          <strong>{location ? Number(location.longitude).toFixed(5) : "-"}</strong>
        </article>
        <article>
          <span className="telemetry-icon">HDG</span>
          <p>Heading</p>
          <strong>{heading}</strong>
        </article>
        <article>
          <span className="telemetry-icon">ETA</span>
          <p>Live ETA</p>
          <strong>{liveEta}</strong>
        </article>
      </section>

      <section className="tracking-map-card">
        <div className="tracking-map-heading">
          <div>
            <p>Live route map</p>
            <h2>
              {selectedTrip
                ? `${selectedTrip.source} to ${selectedTrip.destination}`
                : "Current vehicle position"}
            </h2>
          </div>
          <div className="tracking-map-controls">
            <span className="route-legend">
              <i /> Optimized route
            </span>
            <button type="button" onClick={() => setFollowVehicle((value) => !value)}>
              {followVehicle ? "Following vehicle" : "Follow vehicle"}
            </button>
            <button type="button" onClick={() => setCenterRequest((value) => value + 1)}>
              Center vehicle
            </button>
            <button
              type="button"
              onClick={() =>
                isFullscreen
                  ? document.exitFullscreen?.()
                  : mapFrameRef.current?.requestFullscreen?.()
              }
            >
              {isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            </button>
          </div>
        </div>

        <div ref={mapFrameRef} className="tracking-map-frame">
          <MapContainer center={mapCenter} zoom={7} scrollWheelZoom>
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {routePositions.length > 0 && (
              <Polyline
                positions={routePositions}
                pathOptions={{ color: "#7254d8", weight: 5 }}
              />
            )}
            {location && (
              <Marker
                position={[location.latitude, location.longitude]}
                icon={getVehicleIcon(selectedVehicle?.vehicle_type)}
                zIndexOffset={1000}
              />
            )}
            <MapController
              route={route?.geometry}
              location={location}
              followVehicle={followVehicle}
              centerRequest={centerRequest}
            />
          </MapContainer>

          {!location && (
            <div className="tracking-map-loading">
              <span className="tracking-map-spinner" />
              Waiting for an automatic GPS update...
            </div>
          )}
        </div>
      </section>

      <section className="tracking-progress-card">
        <div className="tracking-progress-heading">
          <div>
            <p>Trip progress</p>
            <strong>
              {selectedTrip?.source || "Source"} <span>to</span>{" "}
              {selectedTrip?.destination || "Destination"}
            </strong>
          </div>
          <b>{progress}%</b>
        </div>
        <div className="tracking-progress-track">
          <i style={{ width: `${progress}%` }} />
        </div>
        <div className="tracking-progress-labels">
          <span>Source</span>
          <span>Current position</span>
          <span>Destination</span>
        </div>
      </section>

      <section className="tracking-trip-summary">
        <div>
          <span>Trip ID</span>
          <strong>
            {selectedTrip?.trip_id
              ? selectedTrip.trip_id.slice(0, 8)
              : "No active trip"}
          </strong>
        </div>
        <div>
          <span>Source</span>
          <strong>{selectedTrip?.source || "-"}</strong>
        </div>
        <div>
          <span>Destination</span>
          <strong>{selectedTrip?.destination || "-"}</strong>
        </div>
        <div>
          <span>Distance</span>
          <strong>
            {route ? `${(route.planned_distance / 1000).toFixed(1)} km` : "-"}
          </strong>
        </div>
        <div>
          <span>ETA</span>
          <strong>{liveEta}</strong>
        </div>
        <div>
          <span>Estimated Duration</span>
          <strong>
            {route ? `${Math.round(route.estimated_duration / 60)} min` : "-"}
          </strong>
        </div>
        <div>
          <span>Route Type</span>
          <strong>{route?.route_type || selectedTrip?.route_type || "-"}</strong>
        </div>
      </section>
    </MainLayout>
  );
}

export default LiveTracking;
