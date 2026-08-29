import { useContext, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatsCard from "../components/StatsCard";
import StatusBadge from "../components/StatusBadge";
import { AnalyticsBarChart, AnalyticsDonutChart } from "../components/AnalyticsCharts";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Analytics.css";

const hours = (seconds) => seconds == null ? "Not calculated" : `${(Number(seconds) / 3600).toFixed(1)} h`;
const kilometres = (meters) => meters == null ? "Not calculated" : `${(Number(meters) / 1000).toFixed(1)} km`;

function LogisticsAnalytics() {
  const { user } = useContext(AuthContext);
  const [data, setData] = useState(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const allowed = ["Admin", "FleetManager", "Dispatcher"].includes(user?.role);
  const load = async () => { setLoading(true); setError(""); try { const [shipments, trips, delivery] = await Promise.all([api.get("/shipments/"), api.get("/trips/"), api.get("/analytics/delivery-performance")]); const activeTrips = trips.data.filter((trip) => trip.status === "Active"); const routeResults = await Promise.allSettled(activeTrips.map((trip) => api.get(`/trips/${trip.trip_id}/route`))); setData({ shipments: shipments.data, trips: trips.data, delivery: delivery.data, routes: routeResults.filter((result) => result.status === "fulfilled").map((result) => result.value.data) }); } catch (requestError) { setError(requestError.response?.data?.detail || "Unable to load logistics analytics."); } finally { setLoading(false); } };
  useEffect(() => { if (!allowed) return undefined; const timer = window.setTimeout(() => { void load(); }, 0); return () => window.clearTimeout(timer); }, [allowed]);
  if (!allowed && user) return <Navigate to="/dashboard" replace />;
  if (loading) return <MainLayout><LoadingCard message="Loading logistics analytics..." /></MainLayout>;
  if (error) return <MainLayout><PageHeader eyebrow="Analytics" title="Logistics Analytics" description="Delivery performance, routes, and ETA visibility." /><div className="analytics-error">{error}<button onClick={() => void load()}>Try again</button></div></MainLayout>;
  const statusCounts = data.shipments.reduce((counts, shipment) => ({ ...counts, [shipment.status]: (counts[shipment.status] || 0) + 1 }), {});
  const active = (statusCounts.Created || 0) + (statusCounts.Assigned || 0) + (statusCounts["In Transit"] || 0) + (statusCounts.Delayed || 0);
  const calculatedTrips = data.trips.filter((trip) => trip.planned_distance != null || trip.estimated_duration != null);
  const averageDistance = calculatedTrips.length ? calculatedTrips.reduce((sum, trip) => sum + Number(trip.planned_distance || 0), 0) / calculatedTrips.length : null;
  const averageDuration = calculatedTrips.length ? calculatedTrips.reduce((sum, trip) => sum + Number(trip.estimated_duration || 0), 0) / calculatedTrips.length : null;
  const remainingDistance = data.routes.reduce((sum, route) => sum + Number(route.remaining_distance || 0), 0);
  const remainingDuration = data.routes.reduce((sum, route) => sum + Number(route.remaining_duration || 0), 0);
  const shipmentById = new Map(data.shipments.map((item) => [item.shipment_id, item]));
  const groups = {};
  data.trips.filter((trip) => trip.status === "Completed" && trip.ended_at).forEach((trip) => { const shipment = shipmentById.get(trip.shipment_id); if (!shipment?.expected_delivery_at) return; const label = new Date(trip.ended_at).toLocaleDateString(); const group = groups[label] || { label, onTime: 0, total: 0 }; group.total += 1; if (new Date(trip.ended_at) <= new Date(shipment.expected_delivery_at)) group.onTime += 1; groups[label] = group; });
  const onTimeTrend = Object.values(groups).sort((a, b) => new Date(a.label) - new Date(b.label)).map((item) => ({ label: item.label, value: Math.round((item.onTime / item.total) * 100) }));
  return <MainLayout><PageHeader eyebrow="Analytics" title="Logistics Analytics" description="Delivery health, route performance, and data-backed on-time metrics." /><div className="analytics-refresh"><span>ETA accuracy requires persisted ETA history, which is not available yet.</span><button className="primary-button" onClick={() => void load()}>Refresh data</button></div><section className="analytics-kpis"><StatsCard label="Active Shipments" value={active} detail="Created to delayed" icon="▣" /><StatsCard label="Completed" value={statusCounts.Delivered || 0} detail="Delivered shipments" icon="✓" tone="green" /><StatsCard label="Delayed" value={statusCounts.Delayed || 0} detail="Needs attention" icon="!" tone="red" /><StatsCard label="In Transit" value={statusCounts["In Transit"] || 0} detail="Currently moving" icon="⌁" tone="purple" /><StatsCard label="On-time Rate" value={`${data.delivery.on_time_rate || 0}%`} detail={`${data.delivery.on_time_deliveries || 0} verified on time`} icon="◔" tone="green" /></section><section className="analytics-grid two"><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>Delivery composition</p><h2>Shipment status breakdown</h2></div></div><AnalyticsDonutChart data={Object.entries(statusCounts).map(([label, value]) => ({ label, value }))} /></article><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>On-time delivery</p><h2>Verified on-time percentage</h2></div></div><AnalyticsBarChart data={onTimeTrend} dataKey="value" name="On-time rate (%)" /></article></section><section className="analytics-grid two"><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>OSRM routes</p><h2>Route performance</h2></div></div><div className="analytics-summary-list"><div><span>Average calculated distance</span><b>{kilometres(averageDistance)}</b></div><div><span>Average calculated duration</span><b>{hours(averageDuration)}</b></div><div><span>Active remaining distance</span><b>{data.routes.length ? kilometres(remainingDistance) : "No route data"}</b></div><div><span>Active remaining duration</span><b>{data.routes.length ? hours(remainingDuration) : "No route data"}</b></div></div></article><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>ETA accuracy</p><h2>Historical comparison</h2></div></div><div className="analytics-no-data"><strong>No ETA accuracy data available</strong><p>FleetFlow updates current ETAs but does not persist historical ETA snapshots for an accurate final-versus-predicted comparison.</p></div></article></section><section className="analytics-panel"><div className="analytics-panel-heading"><div><p>Route directory</p><h2>Calculated trips</h2></div></div>{calculatedTrips.length ? <div className="analytics-table-wrap"><table><thead><tr><th>Route</th><th>Type</th><th>Distance</th><th>Duration</th><th>ETA</th><th>Status</th></tr></thead><tbody>{calculatedTrips.map((trip) => <tr key={trip.trip_id}><td>{trip.source} <small>to</small> {trip.destination}</td><td>{trip.route_type}</td><td>{kilometres(trip.planned_distance)}</td><td>{hours(trip.estimated_duration)}</td><td>{trip.eta ? new Date(trip.eta).toLocaleString() : "Not calculated"}</td><td><StatusBadge status={trip.status} /></td></tr>)}</tbody></table></div> : <EmptyState title="No calculated routes" description="Route distance and duration appear here after a trip route is calculated." />}</section></MainLayout>;
}
export default LogisticsAnalytics;
