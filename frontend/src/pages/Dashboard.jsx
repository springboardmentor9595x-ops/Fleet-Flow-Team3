import Sidebar from "../components/layout/Sidebar";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";

export default function Dashboard() {
  const { user } = useAuth();

  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [trips, setTrips] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [maintenanceAlerts, setMaintenanceAlerts] = useState(null);
  const [fuel, setFuel] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [attendance, setAttendance] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        setError("");

        const responses = await Promise.allSettled([
          api.get("/vehicles/"),
          api.get("/drivers/"),
          api.get("/shipments/"),
          api.get("/trips/"),
          api.get("/maintenance/"),
          api.get("/fuel/"),
          api.get("/notifications/"),
          api.get("/attendance/"),
        ]);

        const [
          vehiclesResponse,
          driversResponse,
          shipmentsResponse,
          tripsResponse,
          maintenanceResponse,
          fuelResponse,
          notificationsResponse,
          attendanceResponse,
        ] = responses;

        if (vehiclesResponse.status === "fulfilled") {
          setVehicles(vehiclesResponse.value.data);
        }

        if (driversResponse.status === "fulfilled") {
          setDrivers(driversResponse.value.data);
        }

        if (shipmentsResponse.status === "fulfilled") {
          setShipments(shipmentsResponse.value.data);
        }

        if (tripsResponse.status === "fulfilled") {
          setTrips(tripsResponse.value.data);
        }

        if (maintenanceResponse.status === "fulfilled") {
          setMaintenance(maintenanceResponse.value.data);
        }

        if (fuelResponse.status === "fulfilled") {
          setFuel(fuelResponse.value.data);
        }

        if (notificationsResponse.status === "fulfilled") {
          setNotifications(notificationsResponse.value.data);
        }

        if (attendanceResponse.status === "fulfilled") {
          setAttendance(attendanceResponse.value.data);
        }

        const failedRequests = responses.filter(
          (response) => response.status === "rejected"
        );

        if (failedRequests.length > 0) {
          console.error("Some dashboard requests failed:", failedRequests);
          setError("Some dashboard data could not be loaded.");
        }
      } catch (error) {
        console.error("Dashboard loading error:", error);
        setError("Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();

    // Load maintenance alerts separately (non-blocking)
    api.get("/maintenance/alerts")
      .then((res) => setMaintenanceAlerts(res.data))
      .catch(() => {});
  }, []);

  return (
    <div style={styles.app}>
      <Sidebar />

      <div style={styles.content}>
        <header style={styles.header}>
          <div>
            <h1 style={styles.title}>FleetFlow Dashboard</h1>

            <p style={styles.welcome}>
              Welcome, <strong>{user?.full_name || "User"}</strong>
            </p>
          </div>
        </header>

        <main style={styles.main}>
          {error && (
            <div style={styles.error}>
              {error}
            </div>
          )}

          {/* Maintenance Alerts Banner */}
          {maintenanceAlerts && maintenanceAlerts.total_alerts > 0 && (
            <a
              href="/maintenance"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "14px 20px",
                background: "#fff7ed",
                border: "1px solid #fed7aa",
                borderRadius: "10px",
                marginBottom: "20px",
                color: "#c2410c",
                fontWeight: "600",
                textDecoration: "none",
                fontSize: "14px",
              }}
            >
              <span style={{ fontSize: "20px" }}>⚠️</span>
              <span>
                {maintenanceAlerts.total_alerts} vehicle maintenance alert{maintenanceAlerts.total_alerts > 1 ? "s" : ""}:{" "}
                {maintenanceAlerts.alerts.filter(a => a.alert_level === "overdue").length} overdue,{" "}
                {maintenanceAlerts.alerts.filter(a => a.alert_level === "upcoming").length} upcoming within 7 days.
                <strong style={{ marginLeft: "8px" }}>→ View Maintenance</strong>
              </span>
            </a>
          )}

          {/* Dashboard Cards */}
          <div style={styles.cards}>
            <DashboardCard
              title="Vehicles"
              value={loading ? "..." : vehicles.length}
            />

            <DashboardCard
              title="Drivers"
              value={loading ? "..." : drivers.length}
            />

            <DashboardCard
              title="Shipments"
              value={loading ? "..." : shipments.length}
            />

            <DashboardCard
              title="Trips"
              value={loading ? "..." : trips.length}
            />

            <DashboardCard
              title="Maintenance"
              value={loading ? "..." : maintenance.length}
            />

            <DashboardCard
              title="Fuel Records"
              value={loading ? "..." : fuel.length}
            />

            <DashboardCard
              title="Notifications"
              value={loading ? "..." : notifications.length}
            />

            <DashboardCard
              title="Attendance"
              value={loading ? "..." : attendance.length}
            />
          </div>

          {/* Recent Vehicles */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Vehicles</h2>

            {loading ? (
              <p>Loading vehicles...</p>
            ) : vehicles.length === 0 ? (
              <p>No vehicles found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Registration</th>
                      <th>Type</th>
                      <th>Brand</th>
                      <th>Model</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {vehicles.slice(0, 5).map((vehicle) => (
                      <tr key={vehicle.vehicle_id}>
                        <td>{vehicle.registration_number}</td>
                        <td>{vehicle.vehicle_type}</td>
                        <td>{vehicle.brand}</td>
                        <td>{vehicle.model}</td>
                        <td>
                          <span style={styles.status}>
                            {vehicle.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Recent Drivers */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Drivers</h2>

            {loading ? (
              <p>Loading drivers...</p>
            ) : drivers.length === 0 ? (
              <p>No drivers found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Driver ID</th>
                      <th>User ID</th>
                    </tr>
                  </thead>

                  <tbody>
                    {drivers.slice(0, 5).map((driver) => (
                      <tr key={driver.driver_id}>
                        <td>{driver.driver_id}</td>
                        <td>
                          {driver.user_id || "Not assigned"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Recent Shipments */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Shipments</h2>

            {loading ? (
              <p>Loading shipments...</p>
            ) : shipments.length === 0 ? (
              <p>No shipments found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Shipment ID</th>
                    </tr>
                  </thead>

                  <tbody>
                    {shipments.slice(0, 5).map((shipment) => (
                      <tr key={shipment.shipment_id}>
                        <td>{shipment.shipment_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Recent Trips */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Trips</h2>

            {loading ? (
              <p>Loading trips...</p>
            ) : trips.length === 0 ? (
              <p>No trips found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Trip ID</th>
                    </tr>
                  </thead>

                  <tbody>
                    {trips.slice(0, 5).map((trip) => (
                      <tr key={trip.trip_id}>
                        <td>{trip.trip_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Recent Maintenance */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Maintenance</h2>

            {loading ? (
              <p>Loading maintenance records...</p>
            ) : maintenance.length === 0 ? (
              <p>No maintenance records found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Maintenance ID</th>
                    </tr>
                  </thead>

                  <tbody>
                    {maintenance.slice(0, 5).map((record) => (
                      <tr key={record.maintenance_id}>
                        <td>{record.maintenance_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Recent Fuel Records */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Fuel Records</h2>

            {loading ? (
              <p>Loading fuel records...</p>
            ) : fuel.length === 0 ? (
              <p>No fuel records found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Fuel Record ID</th>
                    </tr>
                  </thead>

                  <tbody>
                    {fuel.slice(0, 5).map((record) => (
                      <tr key={record.fuel_id}>
                        <td>{record.fuel_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Recent Notifications */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Notifications</h2>

            {loading ? (
              <p>Loading notifications...</p>
            ) : notifications.length === 0 ? (
              <p>No notifications found.</p>
            ) : (
              <div style={styles.notificationList}>
                {notifications.slice(0, 5).map((notification) => (
                  <div
                    key={notification.notification_id}
                    style={styles.notification}
                  >
                    <span style={styles.notificationIcon}>
                      🔔
                    </span>

                    <div>
                      <p style={styles.notificationMessage}>
                        {notification.message || "Notification"}
                      </p>

                      <small style={styles.notificationId}>
                        {notification.notification_id}
                      </small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Recent Attendance */}
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Recent Attendance</h2>

            {loading ? (
              <p>Loading attendance records...</p>
            ) : attendance.length === 0 ? (
              <p>No attendance records found.</p>
            ) : (
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th>Attendance ID</th>
                      <th>Driver ID</th>
                    </tr>
                  </thead>

                  <tbody>
                    {attendance.slice(0, 5).map((record) => (
                      <tr key={record.attendance_id}>
                        <td>{record.attendance_id}</td>
                        <td>
                          {record.driver_id || "Not assigned"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

function DashboardCard({ title, value }) {
  return (
    <div style={styles.card}>
      <h2 style={styles.cardTitle}>{title}</h2>

      <div style={styles.number}>
        {value}
      </div>
    </div>
  );
}

const styles = {
  app: {
    minHeight: "100vh",
    background: "#f4f7fb",
  },

  content: {
    marginLeft: "250px",
    minHeight: "100vh",
  },

  header: {
    padding: "30px 50px",
    background: "white",
    borderBottom: "1px solid #e5e7eb",
  },

  title: {
    margin: 0,
    fontSize: "32px",
    color: "#172554",
  },

  welcome: {
    fontSize: "17px",
    color: "#475569",
    marginTop: "10px",
  },

  main: {
    padding: "35px 50px",
  },

  error: {
    marginBottom: "25px",
    padding: "15px 20px",
    background: "#fee2e2",
    color: "#991b1b",
    borderRadius: "8px",
    fontSize: "14px",
  },

  cards: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "22px",
    marginBottom: "35px",
  },

  card: {
    background: "white",
    padding: "25px",
    borderRadius: "12px",
    boxShadow: "0 4px 15px rgba(0,0,0,0.06)",
  },

  cardTitle: {
    margin: 0,
    fontSize: "18px",
    color: "#334155",
  },

  number: {
    fontSize: "38px",
    fontWeight: "700",
    color: "#2563eb",
    marginTop: "15px",
  },

  section: {
    background: "white",
    padding: "25px",
    borderRadius: "12px",
    marginBottom: "25px",
    boxShadow: "0 4px 15px rgba(0,0,0,0.06)",
  },

  sectionTitle: {
    marginTop: 0,
    color: "#172554",
  },

  tableWrapper: {
    overflowX: "auto",
  },

  table: {
    width: "100%",
    borderCollapse: "collapse",
    marginTop: "15px",
  },

  status: {
    display: "inline-block",
    padding: "5px 10px",
    borderRadius: "20px",
    background: "#dcfce7",
    color: "#166534",
    fontSize: "13px",
    fontWeight: "600",
  },

  notificationList: {
    marginTop: "15px",
  },

  notification: {
    display: "flex",
    alignItems: "center",
    gap: "15px",
    padding: "15px 0",
    borderBottom: "1px solid #e5e7eb",
  },

  notificationIcon: {
    fontSize: "20px",
  },

  notificationMessage: {
    margin: 0,
    color: "#334155",
    fontWeight: "500",
  },

  notificationId: {
    color: "#94a3b8",
    fontSize: "11px",
  },
};