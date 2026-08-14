import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../../api/axios";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
} from "react-leaflet";

import L from "leaflet";
import "leaflet/dist/leaflet.css";

const DESTINATION = [28.4744, 77.5040];
const GEOFENCE_RADIUS = 500;

// ============================================================
// VEHICLE ICON
// ============================================================

const vehicleIcon = new L.Icon({
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",

  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",

  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

// ============================================================
// MAP UPDATER
// ============================================================

function MapUpdater({ gpsData }) {
  const map = useMap();

  useEffect(() => {
    if (
      gpsData?.latitude !== undefined &&
      gpsData?.longitude !== undefined &&
      gpsData?.latitude !== null &&
      gpsData?.longitude !== null
    ) {
      map.setView(
        [gpsData.latitude, gpsData.longitude],
        16,
        {
          animate: true,
        }
      );
    }
  }, [gpsData, map]);

  return null;
}

// ============================================================
// LIVE TRACKING
// ============================================================

export default function LiveTracking() {
  const [searchParams] = useSearchParams();

  const vehicleId = searchParams.get("vehicle_id");

  const socketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(true);

  const [gpsData, setGpsData] = useState(null);

  const [connectionStatus, setConnectionStatus] =
    useState("Connecting...");

  const [error, setError] = useState("");
  const [vehicle, setVehicle] = useState(null);

  useEffect(() => {
    if (vehicleId) {
      api.get(`/vehicles/${vehicleId}`)
        .then((res) => {
          setVehicle(res.data);
        })
        .catch((err) => {
          console.error("Failed to fetch vehicle:", err);
        });
    }
  }, [vehicleId]);

  // ==========================================================
  // WEBSOCKET
  // ==========================================================

  useEffect(() => {
    mountedRef.current = true;

    if (!vehicleId) {
      setConnectionStatus("Vehicle ID missing");
      setError("No vehicle was selected.");
      return;
    }

    let cancelled = false;

    const connectWebSocket = () => {
      if (cancelled || !mountedRef.current) {
        return;
      }

      // Prevent duplicate connections
      if (
        socketRef.current &&
        (
          socketRef.current.readyState === WebSocket.OPEN ||
          socketRef.current.readyState === WebSocket.CONNECTING
        )
      ) {
        console.log(
          "WebSocket already connected/connecting"
        );

        return;
      }

      const host =
        window.location.hostname || "127.0.0.1";

      const wsUrl =
        `ws://${host}:8000/ws/tracking/${vehicleId}`;

      console.log(
        "===================================="
      );

      console.log(
        "Connecting to FleetFlow WebSocket"
      );

      console.log(
        "Vehicle ID:",
        vehicleId
      );

      console.log(
        "WebSocket URL:",
        wsUrl
      );

      console.log(
        "===================================="
      );

      setConnectionStatus("Connecting...");

      const socket = new WebSocket(wsUrl);

      socketRef.current = socket;

      // ------------------------------------------------------
      // OPEN
      // ------------------------------------------------------

      socket.onopen = () => {
        if (
          cancelled ||
          !mountedRef.current
        ) {
          return;
        }

        console.log(
          "✅ FleetFlow WebSocket connected"
        );

        console.log(
          "Tracking vehicle:",
          vehicleId
        );

        setConnectionStatus("Connected");

        // Remove old connection error
        setError("");
      };

      // ------------------------------------------------------
      // MESSAGE
      // ------------------------------------------------------

      socket.onmessage = (event) => {
        if (
          cancelled ||
          !mountedRef.current
        ) {
          return;
        }

        console.log(
          "📡 Live GPS update:",
          event.data
        );

        try {
          const data = JSON.parse(
            event.data
          );

          // Backend error
          if (data.error) {
            console.error(
              "FleetFlow server error:",
              data.error
            );

            setError(data.error);

            return;
          }

          console.log(
            "Vehicle position:",
            data.latitude,
            data.longitude
          );

          console.log(
            "Vehicle speed:",
            data.speed
          );

          console.log(
            "Distance:",
            data.distance_to_destination
          );

          console.log(
            "Geofence:",
            data.inside_geofence
          );

          setGpsData(data);

          // Successful GPS data means
          // the connection is working.
          setConnectionStatus("Connected");

          setError("");

        } catch (err) {
          console.error(
            "Invalid WebSocket data:",
            err
          );
        }
      };

      // ------------------------------------------------------
      // ERROR
      // ------------------------------------------------------

      socket.onerror = (event) => {
        if (
          cancelled ||
          !mountedRef.current
        ) {
          return;
        }

        console.error(
          "❌ FleetFlow WebSocket error:",
          event
        );

        /*
         * Do NOT immediately show
         * "Unable to connect".
         *
         * WebSocket can fire error before
         * the close event.
         */

        setConnectionStatus(
          "Connection error"
        );
      };

      // ------------------------------------------------------
      // CLOSE
      // ------------------------------------------------------

      socket.onclose = (event) => {
        if (
          cancelled ||
          !mountedRef.current
        ) {
          return;
        }

        console.log(
          "🔴 FleetFlow WebSocket disconnected"
        );

        console.log(
          "Close code:",
          event.code
        );

        console.log(
          "Close reason:",
          event.reason
        );

        setConnectionStatus(
          "Disconnected"
        );

        socketRef.current = null;

        /*
         * Automatically reconnect.
         *
         * This is important because the
         * backend may restart when using
         * uvicorn --reload.
         */

        if (!cancelled) {
          reconnectTimerRef.current =
            setTimeout(() => {
              console.log(
                "🔄 Reconnecting to FleetFlow..."
              );

              connectWebSocket();
            }, 2000);
        }
      };
    };

    // First connection
    connectWebSocket();

    // ------------------------------------------------------
    // CLEANUP
    // ------------------------------------------------------

    return () => {
      console.log(
        "Cleaning up vehicle WebSocket"
      );

      cancelled = true;

      mountedRef.current = false;

      if (reconnectTimerRef.current) {
        clearTimeout(
          reconnectTimerRef.current
        );

        reconnectTimerRef.current = null;
      }

      if (socketRef.current) {
        const socket =
          socketRef.current;

        socketRef.current = null;

        /*
         * Remove handlers before closing
         * so React cleanup does not trigger
         * unnecessary reconnect logic.
         */

        socket.onopen = null;
        socket.onmessage = null;
        socket.onerror = null;
        socket.onclose = null;

        if (
          socket.readyState ===
            WebSocket.OPEN ||
          socket.readyState ===
            WebSocket.CONNECTING
        ) {
          socket.close();
        }
      }
    };

  }, [vehicleId]);

  // ==========================================================
  // HELPERS
  // ==========================================================

  const hasLocation =
    gpsData &&
    gpsData.latitude !== null &&
    gpsData.longitude !== null &&
    gpsData.latitude !== undefined &&
    gpsData.longitude !== undefined;

  const isInsideGeofence =
    gpsData?.inside_geofence === true;

  const status =
    gpsData?.status || "Waiting";

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div style={styles.page}>

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <div style={styles.header}>

        <div>
          <h1 style={styles.title}>
            Live Vehicle Tracking
          </h1>

          <p style={styles.subtitle}>
            Real-time GPS monitoring and geofence tracking
          </p>
        </div>

        <div
          style={{
            ...styles.connectionBadge,

            ...(connectionStatus === "Connected"
              ? styles.connected
              : connectionStatus === "Connecting..."
              ? styles.connecting
              : styles.disconnected),
          }}
        >
          <span style={styles.statusDot} />

          {connectionStatus}
        </div>

      </div>

      {/* ================================================== */}
      {/* VEHICLE INFORMATION */}
      {/* ================================================== */}

      <div style={styles.vehicleCard}>

        <div>

          <div style={styles.cardLabel}>
            REGISTRATION NUMBER
          </div>

          <div style={styles.vehicleId}>
            {vehicle?.registration_number || vehicleId || "Not selected"}
          </div>

        </div>

        <div>

          <div style={styles.cardLabel}>
            STATUS
          </div>

          <div
            style={{
              ...styles.statusBadge,

              ...(status === "Arrived"
                ? styles.arrived
                : styles.enRoute),
            }}
          >
            {status}
          </div>

        </div>

      </div>

      {/* ================================================== */}
      {/* ERROR */}
      {/* ================================================== */}

      {error && (
        <div style={styles.errorBox}>
          {error}
        </div>
      )}

      {/* ================================================== */}
      {/* LIVE STATISTICS */}
      {/* ================================================== */}

      <div style={styles.statsGrid}>

        <StatCard
          label="Speed"
          value={
            gpsData?.speed !== undefined
              ? `${gpsData.speed} km/h`
              : "--"
          }
        />

        <StatCard
          label="Distance to Destination"
          value={
            gpsData?.distance_to_destination !==
            undefined
              ? `${gpsData.distance_to_destination} m`
              : "--"
          }
        />

        <StatCard
          label="Geofence Radius"
          value={`${GEOFENCE_RADIUS} m`}
        />

        <StatCard
          label="Geofence"
          value={
            gpsData
              ? gpsData.inside_geofence
                ? "Inside"
                : "Outside"
              : "--"
          }
        />

      </div>

      {/* ================================================== */}
      {/* MAP */}
      {/* ================================================== */}

      <div style={styles.mapCard}>

        <div style={styles.mapHeader}>

          <div>

            <h2 style={styles.mapTitle}>
              Live Vehicle Map
            </h2>

            <p style={styles.mapSubtitle}>
              Vehicle position updates automatically
            </p>

          </div>

          {gpsData && (
            <div
              style={{
                ...styles.eventBadge,

                ...(isInsideGeofence
                  ? styles.eventArrived
                  : styles.eventEnRoute),
              }}
            >
              {gpsData.event || "GPS update"}
            </div>
          )}

        </div>

        <MapContainer
          center={DESTINATION}
          zoom={15}
          style={styles.map}
        >

          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapUpdater
            gpsData={gpsData}
          />

          {/* DESTINATION / GEOFENCE */}

          <Circle
            center={DESTINATION}
            radius={GEOFENCE_RADIUS}
            pathOptions={{
              color: "blue",
              fillColor: "blue",
              fillOpacity: 0.08,
              weight: 2,
            }}
          />

          {/* DESTINATION MARKER */}

          <Marker
            position={DESTINATION}
          >
            <Popup>
              <strong>
                FleetFlow Destination
              </strong>

              <br />

              Geofence:
              {" "}
              {GEOFENCE_RADIUS} m
            </Popup>
          </Marker>

          {/* VEHICLE */}

          {hasLocation && (
            <Marker
              position={[
                gpsData.latitude,
                gpsData.longitude,
              ]}
              icon={vehicleIcon}
            >

              <Popup>

                <div style={styles.popup}>

                  <h3>
                    FleetFlow Vehicle
                  </h3>

                  <p>
                    <strong>
                      Registration:
                    </strong>{" "}
                    {vehicle?.registration_number || gpsData.vehicle_id}
                  </p>

                  <p>
                    <strong>
                      Speed:
                    </strong>{" "}
                    {gpsData.speed} km/h
                  </p>

                  <p>
                    <strong>
                      Distance:
                    </strong>{" "}
                    {gpsData.distance_to_destination} m
                  </p>

                  <p>
                    <strong>
                      Status:
                    </strong>{" "}
                    {gpsData.status}
                  </p>

                  <p>
                    <strong>
                      Geofence:
                    </strong>{" "}
                    {gpsData.inside_geofence
                      ? "Inside"
                      : "Outside"}
                  </p>

                  <p>
                    <strong>
                      Latitude:
                    </strong>{" "}
                    {gpsData.latitude}
                  </p>

                  <p>
                    <strong>
                      Longitude:
                    </strong>{" "}
                    {gpsData.longitude}
                  </p>

                </div>

              </Popup>

            </Marker>
          )}

        </MapContainer>

      </div>

      {/* ================================================== */}
      {/* GPS DETAILS */}
      {/* ================================================== */}

      <div style={styles.detailsCard}>

        <h2 style={styles.detailsTitle}>
          Vehicle GPS Details
        </h2>

        {!gpsData ? (

          <div style={styles.waiting}>

            {connectionStatus ===
            "Connected"
              ? "Connected. Waiting for GPS data..."
              : "Waiting for FleetFlow tracking connection..."}

          </div>

        ) : (

          <div style={styles.detailsGrid}>

            <Detail
              label="Registration"
              value={vehicle?.registration_number || gpsData.vehicle_id}
            />

            <Detail
              label="Latitude"
              value={gpsData.latitude}
            />

            <Detail
              label="Longitude"
              value={gpsData.longitude}
            />

            <Detail
              label="Speed"
              value={`${gpsData.speed} km/h`}
            />

            <Detail
              label="Distance"
              value={`${gpsData.distance_to_destination} m`}
            />

            <Detail
              label="Geofence"
              value={
                gpsData.inside_geofence
                  ? "Inside"
                  : "Outside"
              }
            />

            <Detail
              label="Status"
              value={gpsData.status}
            />

            <Detail
              label="Recorded Time"
              value={gpsData.recorded_time}
            />

          </div>

        )}

      </div>

    </div>
  );
}

// ============================================================
// STAT CARD
// ============================================================

function StatCard({
  label,
  value,
}) {
  return (
    <div style={styles.statCard}>

      <div style={styles.statLabel}>
        {label}
      </div>

      <div style={styles.statValue}>
        {value}
      </div>

    </div>
  );
}

// ============================================================
// DETAIL
// ============================================================

function Detail({
  label,
  value,
}) {
  return (
    <div style={styles.detailItem}>

      <div style={styles.detailLabel}>
        {label}
      </div>

      <div style={styles.detailValue}>
        {value}
      </div>

    </div>
  );
}

// ============================================================
// STYLES
// ============================================================

const styles = {

  page: {
    minHeight: "100vh",
    padding: "30px 40px",
    background: "#f4f7fb",
    boxSizing: "border-box",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "25px",
  },

  title: {
    margin: 0,
    fontSize: "30px",
    fontWeight: "700",
    color: "#172554",
  },

  subtitle: {
    marginTop: "7px",
    color: "#64748b",
  },

  connectionBadge: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px 14px",
    borderRadius: "20px",
    fontSize: "13px",
    fontWeight: "600",
  },

  connected: {
    background: "#dcfce7",
    color: "#166534",
  },

  connecting: {
    background: "#dbeafe",
    color: "#1d4ed8",
  },

  disconnected: {
    background: "#fee2e2",
    color: "#991b1b",
  },

  statusDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "currentColor",
  },

  vehicleCard: {
    background: "white",
    padding: "20px 25px",
    borderRadius: "12px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow:
      "0 4px 15px rgba(0,0,0,0.05)",
    marginBottom: "20px",
  },

  cardLabel: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#64748b",
    marginBottom: "5px",
    letterSpacing: "0.5px",
  },

  vehicleId: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#334155",
  },

  statusBadge: {
    display: "inline-block",
    padding: "7px 14px",
    borderRadius: "20px",
    fontSize: "13px",
    fontWeight: "700",
  },

  arrived: {
    background: "#dcfce7",
    color: "#166534",
  },

  enRoute: {
    background: "#dbeafe",
    color: "#1d4ed8",
  },

  errorBox: {
    background: "#fee2e2",
    color: "#991b1b",
    padding: "14px 18px",
    borderRadius: "8px",
    marginBottom: "20px",
  },

  statsGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(4, 1fr)",
    gap: "18px",
    marginBottom: "20px",
  },

  statCard: {
    background: "white",
    padding: "20px",
    borderRadius: "12px",
    boxShadow:
      "0 4px 15px rgba(0,0,0,0.05)",
  },

  statLabel: {
    fontSize: "13px",
    color: "#64748b",
    marginBottom: "8px",
  },

  statValue: {
    fontSize: "23px",
    fontWeight: "700",
    color: "#172554",
  },

  mapCard: {
    background: "white",
    borderRadius: "12px",
    overflow: "hidden",
    boxShadow:
      "0 4px 15px rgba(0,0,0,0.05)",
    marginBottom: "20px",
  },

  mapHeader: {
    padding: "20px 25px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom:
      "1px solid #e5e7eb",
  },

  mapTitle: {
    margin: 0,
    fontSize: "20px",
    color: "#172554",
  },

  mapSubtitle: {
    margin: "5px 0 0",
    fontSize: "13px",
    color: "#64748b",
  },

  eventBadge: {
    padding: "8px 12px",
    borderRadius: "8px",
    fontSize: "12px",
    fontWeight: "600",
  },

  eventArrived: {
    background: "#dcfce7",
    color: "#166534",
  },

  eventEnRoute: {
    background: "#dbeafe",
    color: "#1d4ed8",
  },

  map: {
    height: "500px",
    width: "100%",
  },

  popup: {
    minWidth: "190px",
  },

  detailsCard: {
    background: "white",
    padding: "25px",
    borderRadius: "12px",
    boxShadow:
      "0 4px 15px rgba(0,0,0,0.05)",
  },

  detailsTitle: {
    marginTop: 0,
    color: "#172554",
  },

  detailsGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(4, 1fr)",
    gap: "20px",
  },

  detailItem: {
    padding: "15px",
    background: "#f8fafc",
    borderRadius: "8px",
  },

  detailLabel: {
    fontSize: "12px",
    color: "#64748b",
    marginBottom: "6px",
  },

  detailValue: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#334155",
    wordBreak: "break-word",
  },

  waiting: {
    padding: "30px",
    textAlign: "center",
    color: "#64748b",
  },
};