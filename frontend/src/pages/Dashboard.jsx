import { useContext, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatsCard from "../components/StatsCard";
import { AuthContext } from "../context/auth-context";
import api from "../services/api";
import "./Dashboard.css";

function FleetOverviewDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const response = await api.get("/dashboard/fleet");
        setData(response.data);
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail ||
            "Failed to load dashboard."
        );
      }
    };

    const timer = window.setTimeout(loadDashboard, 0);
    return () => window.clearTimeout(timer);
  }, []);

  if (error) {
    return (
      <MainLayout>
        <div className="dashboard-error">{error}</div>
      </MainLayout>
    );
  }

  if (!data) {
    return (
      <MainLayout>
        <LoadingCard message="Loading fleet overview..." />
      </MainLayout>
    );
  }

  const totalVehicles = data.total_vehicles || 0;
  const percentage = (count) =>
    totalVehicles ? Math.round((count / totalVehicles) * 100) : 0;

  const statuses = [
    { label: "Available", value: data.available || 0, tone: "available" },
    { label: "Assigned", value: data.assigned || 0, tone: "assigned" },
    {
      label: "Maintenance",
      value: data.maintenance || 0,
      tone: "maintenance",
    },
    {
      label: "In Transit",
      value: data.in_transit || 0,
      tone: "in-transit",
    },
  ];

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Dashboard"
        title="Fleet Monitoring Dashboard"
        description="A live overview of vehicle availability and operational health."
      />

      <section className="dashboard-hero">
        <div>
          <p>FLEETFLOW COMMAND CENTER</p>
          <h2>Move every delivery with confidence.</h2>
          <span>
            Monitor fleet readiness, dispatch work, and keep your operations
            moving from one place.
          </span>
        </div>

        <nav>
          <Link to="/vehicles">Manage Vehicles</Link>
          <Link to="/shipments">Manage Shipments</Link>
          <Link to="/trips">Manage Trips</Link>
          <Link to="/live-tracking">Live Tracking</Link>
        </nav>
      </section>

      <section className="dashboard-stats" aria-label="Fleet statistics">
        <StatsCard
          label="Total Vehicles"
          value={totalVehicles}
          detail="Registered in FleetFlow"
          icon="▤"
        />
        <StatsCard
          label="Available"
          value={data.available || 0}
          detail={`${percentage(data.available || 0)}% of fleet`}
          icon="✓"
          tone="green"
        />
        <StatsCard
          label="Assigned"
          value={data.assigned || 0}
          detail={`${percentage(data.assigned || 0)}% of fleet`}
          icon="↗"
          tone="amber"
        />
        <StatsCard
          label="Maintenance"
          value={data.maintenance || 0}
          detail={`${percentage(data.maintenance || 0)}% of fleet`}
          icon="⚑"
          tone="red"
        />
        <StatsCard
          label="In Transit"
          value={data.in_transit || 0}
          detail={`${percentage(data.in_transit || 0)}% of fleet`}
          icon="⌁"
          tone="purple"
        />
        <StatsCard
          label="Upcoming Services"
          value={data.upcoming_services || 0}
          detail="Due within 7 days"
          icon="◷"
          tone="amber"
        />
        <StatsCard
          label="Overdue Services"
          value={data.overdue_services || 0}
          detail="Require attention"
          icon="!"
          tone="red"
        />
        <StatsCard
          label="Maintenance Cost"
          value={`₹${Number(data.maintenance_cost_summary || 0).toLocaleString()}`}
          detail="Completed service total"
          icon="₹"
          tone="purple"
        />
      </section>

      <section className="dashboard-lower">
        <article className="dashboard-card distribution-card">
          <div className="dashboard-card-heading">
            <div>
              <p>Fleet distribution</p>
              <h2>Operational availability</h2>
            </div>
            <Link to="/vehicles">View vehicles</Link>
          </div>

          <div className="distribution-list">
            {statuses.map((item) => (
              <div className="distribution-row" key={item.label}>
                <div>
                  <span className={`distribution-dot ${item.tone}`} />
                  <strong>{item.label}</strong>
                </div>

                <b>
                  {item.value} <small>{percentage(item.value)}%</small>
                </b>

                <div className="distribution-track">
                  <span
                    className={item.tone}
                    style={{ width: `${percentage(item.value)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="dashboard-card activity-card">
          <div className="dashboard-card-heading">
            <div>
              <p>Live activity</p>
              <h2>Recent activity</h2>
            </div>
            <span className="placeholder-label">Placeholder</span>
          </div>

          <div className="placeholder-copy">
            <span>◌</span>
            <p>
              Recent operational events will appear here when activity
              analytics is connected.
            </p>
          </div>
        </article>
      </section>

      <section className="dashboard-insights">
        <article className="dashboard-card">
          <p>Delivery performance</p>
          <h2>Performance analytics</h2>

          <div className="dashboard-placeholder-chart">
            <span>Placeholder</span>
            <i />
            <i />
            <i />
            <i />
            <i />
          </div>

          <small>
            Delivery metrics will appear when performance reporting is
            connected.
          </small>
        </article>

        <article className="dashboard-card">
          <p>Fleet health</p>
          <h2>Maintenance readiness</h2>

          <div className="health-placeholder">
            <b>—</b>
            <span>Placeholder health score</span>
          </div>

          <small>
            Health insights will appear when maintenance analytics is
            connected.
          </small>
        </article>

        <article className="dashboard-card quick-actions">
          <p>Quick actions</p>
          <h2>Keep work moving</h2>
          <Link to="/shipments/add">Create Shipment</Link>
          <Link to="/trips/schedule">Schedule Trip</Link>
          <Link to="/drivers">View Drivers</Link>
          <Link to="/maintenance">Manage Maintenance</Link>
        </article>
      </section>
    </MainLayout>
  );
}

function DriverDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      const results = await Promise.allSettled([
        api.get("/drivers/"),
        api.get("/trips/"),
        api.get("/shipments/"),
        api.get("/notifications", { params: { unread_only: true, limit: 100 } }),
      ]);
      if (!active) return;

      const responseData = (index, fallback) => results[index].status === "fulfilled" ? results[index].value.data : fallback;
      setData({
        drivers: responseData(0, []),
        trips: responseData(1, []),
        shipments: responseData(2, []),
        notifications: responseData(3, []),
      });
      if (results.every((result) => result.status === "rejected")) setError("Unable to load your driver dashboard.");
    };
    void load();
    return () => { active = false; };
  }, []);

  if (error) return <MainLayout><div className="dashboard-error">{error}</div></MainLayout>;
  if (!data) return <MainLayout><LoadingCard message="Loading your driver dashboard..." /></MainLayout>;

  const driver = data.drivers[0];
  const assignedVehicle = driver?.assigned_vehicle;
  const currentTrip = driver?.current_trip;
  const activeTrips = data.trips.filter((trip) => ["Scheduled", "Active", "In Transit"].includes(trip.status)).length;
  const activeShipments = data.shipments.filter((shipment) => !["Delivered", "Cancelled"].includes(shipment.status)).length;

  return <MainLayout>
    <PageHeader eyebrow="Driver Workspace" title="My Dashboard" description="Your assignments, delivery work, and live operational updates." />
    <section className="dashboard-hero"><div><p>FLEETFLOW DRIVER WORKSPACE</p><h2>Stay focused on your next delivery.</h2><span>Review your assignment, active work, and relevant tracking information from one place.</span></div><nav><Link to="/drivers">My Profile</Link><Link to="/trips">My Trips</Link><Link to="/shipments">My Shipments</Link><Link to="/live-tracking">Live Tracking</Link></nav></section>
    <section className="dashboard-stats" aria-label="Driver statistics"><StatsCard label="Assigned Vehicle" value={assignedVehicle?.registration_number || "—"} detail={assignedVehicle?.status || "No vehicle assigned"} icon="▤" /><StatsCard label="Current Trip" value={currentTrip?.status || "No active trip"} detail={currentTrip ? `${currentTrip.source} to ${currentTrip.destination}` : "No trip assigned"} icon="⌁" tone="purple" /><StatsCard label="Open Trips" value={activeTrips} detail="Scheduled or active" icon="↗" tone="amber" /><StatsCard label="Open Shipments" value={activeShipments} detail="Your assigned delivery work" icon="▣" tone="green" /><StatsCard label="Unread Alerts" value={data.notifications.length} detail="Your notifications" icon="◌" tone="purple" /></section>
    <section className="dashboard-lower"><article className="dashboard-card"><div className="dashboard-card-heading"><div><p>Current assignment</p><h2>{assignedVehicle?.registration_number || "No vehicle assigned"}</h2></div><Link to="/drivers">View profile</Link></div><div className="dashboard-driver-summary"><div><span>Vehicle status</span><b>{assignedVehicle?.status || "Not assigned"}</b></div><div><span>Current route</span><b>{currentTrip ? `${currentTrip.source} to ${currentTrip.destination}` : "No active route"}</b></div><div><span>Trip status</span><b>{currentTrip?.status || "—"}</b></div></div></article><article className="dashboard-card activity-card"><div className="dashboard-card-heading"><div><p>Notifications</p><h2>Your unread alerts</h2></div></div><div className="placeholder-copy"><span>{data.notifications.length ? "◌" : "✓"}</span><p>{data.notifications.length ? `You have ${data.notifications.length} unread notification${data.notifications.length === 1 ? "" : "s"}. Open the notification bell for details.` : "You have no unread notifications."}</p></div></article></section>
    {!driver && <EmptyState title="No driver profile found" description="Your account is not linked to a driver record yet. Please contact a Fleet Manager." />}
  </MainLayout>;
}

function Dashboard() {
  const { user } = useContext(AuthContext);

  if (!user) return <MainLayout><LoadingCard message="Loading your workspace..." /></MainLayout>;
  if (user.role === "Admin") return <Navigate to="/analytics/admin" replace />;
  if (user.role === "Dispatcher") return <Navigate to="/analytics/logistics" replace />;
  if (user.role === "Driver") return <DriverDashboard />;
  if (user.role === "FleetManager") return <FleetOverviewDashboard />;
  return <Navigate to="/login" replace />;
}

export default Dashboard;
