import { useContext, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatsCard from "../components/StatsCard";
import StatusBadge from "../components/StatusBadge";
import { AnalyticsBarChart, AnalyticsDonutChart, AnalyticsLineChart } from "../components/AnalyticsCharts";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Analytics.css";

const money = (value) => `₹${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
const shortDate = (value) => value ? new Date(value).toLocaleDateString() : "Not scheduled";

function FleetAnalytics() {
  const { user } = useContext(AuthContext);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const allowed = ["Admin", "FleetManager"].includes(user?.role);

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [fleet, fuel, upcoming, maintenance] = await Promise.all([
        api.get("/analytics/fleet-utilization"), api.get("/analytics/fuel-cost-trends"), api.get("/maintenance/upcoming"), api.get("/maintenance/"),
      ]);
      setData({ fleet: fleet.data, fuel: fuel.data, upcoming: upcoming.data, maintenance: maintenance.data });
    } catch (requestError) { setError(requestError.response?.data?.detail || "Unable to load fleet analytics."); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (!allowed) return undefined; const timer = window.setTimeout(() => { void load(); }, 0); return () => window.clearTimeout(timer); }, [allowed]);
  if (!allowed && user) return <Navigate to="/dashboard" replace />;
  if (loading) return <MainLayout><LoadingCard message="Loading fleet analytics..." /></MainLayout>;
  if (error) return <MainLayout><PageHeader eyebrow="Analytics" title="Fleet Analytics" description="Operational fleet performance and service readiness." /><div className="analytics-error">{error}<button onClick={() => void load()}>Try again</button></div></MainLayout>;

  const statuses = data.fleet.statuses || {};
  const get = (name) => statuses[name]?.count || 0;
  const active = get("Assigned") + get("In Transit");
  const utilization = data.fleet.total_fleet ? Math.round((active / data.fleet.total_fleet) * 100) : 0;
  const donut = Object.entries(statuses).map(([label, details]) => ({ label, value: details.count }));
  const maintenanceCost = Object.values(data.maintenance || []).filter((record) => record.status === "Completed").reduce((sum, record) => sum + Number(record.cost || 0), 0);
  const costByType = Object.entries(Object.values(data.maintenance || []).filter((record) => record.status === "Completed").reduce((groups, record) => ({ ...groups, [record.maintenance_type]: (groups[record.maintenance_type] || 0) + Number(record.cost || 0) }), {})).map(([label, value]) => ({ label, value }));
  const upcoming = [...(data.upcoming.upcoming || []), ...(data.upcoming.overdue || [])].sort((a, b) => new Date(a.next_service_date || a.service_date) - new Date(b.next_service_date || b.service_date));

  return <MainLayout><PageHeader eyebrow="Analytics" title="Fleet Analytics" description="Live fleet capacity, fuel spending, and service readiness." />
    <div className="analytics-refresh"><span>Updated from current FleetFlow records.</span><button className="primary-button" onClick={() => void load()}>Refresh data</button></div>
    <section className="analytics-kpis"><StatsCard label="Active Vehicles" value={active} detail="Assigned or in transit" icon="⌁" tone="purple" /><StatsCard label="Fleet Utilization" value={`${utilization}%`} detail={`${data.fleet.total_fleet} total vehicles`} icon="◔" tone="green" /><StatsCard label="In Transit" value={get("In Transit")} detail="Currently delivering" icon="↗" tone="purple" /><StatsCard label="Available" value={get("Available")} detail="Ready for work" icon="✓" tone="green" /><StatsCard label="Maintenance" value={get("Maintenance")} detail="Out of service" icon="⚑" tone="red" /></section>
    <section className="analytics-grid two"><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>Fleet composition</p><h2>Vehicle status breakdown</h2></div></div><AnalyticsDonutChart data={donut} /></article><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>Fuel records</p><h2>Fuel cost trend</h2></div><strong>{money(data.fuel.total_fuel_cost)}</strong></div><AnalyticsLineChart data={(data.fuel.cost_over_time || []).map((item) => ({ label: item.date, value: item.total_fuel_cost }))} dataKey="value" name="Fuel cost" valueFormatter={money} /></article></section>
    <section className="analytics-grid two"><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>Maintenance spend</p><h2>Completed cost by type</h2></div><strong>{money(maintenanceCost)}</strong></div><AnalyticsBarChart data={costByType} dataKey="value" name="Cost" valueFormatter={money} /></article><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>Fuel summary</p><h2>Consumption and refills</h2></div></div><div className="analytics-summary-list"><div><span>Total fuel consumed</span><b>{Number(data.fuel.total_fuel_consumed || 0).toLocaleString()} units</b></div><div><span>Recorded refills</span><b>{data.fuel.total_refills || 0}</b></div><div><span>Fuel cost</span><b>{money(data.fuel.total_fuel_cost)}</b></div></div></article></section>
    <section className="analytics-panel"><div className="analytics-panel-heading"><div><p>Service planning</p><h2>Upcoming maintenance</h2></div><span className="analytics-standin">{data.upcoming.overdue?.length || 0} overdue</span></div>{upcoming.length ? <div className="analytics-table-wrap"><table><thead><tr><th>Vehicle</th><th>Maintenance type</th><th>Scheduled date</th><th>Status</th><th>Cost</th></tr></thead><tbody>{upcoming.map((record) => <tr key={record.maintenance_id}><td>{record.vehicle_id.slice(0, 8)}</td><td>{record.maintenance_type}</td><td>{shortDate(record.next_service_date || record.service_date)}</td><td><StatusBadge status={record.status} /></td><td>{record.cost == null ? "—" : money(record.cost)}</td></tr>)}</tbody></table></div> : <EmptyState title="No maintenance due" description="There are no upcoming or overdue maintenance records." />}</section>
  </MainLayout>;
}

export default FleetAnalytics;
