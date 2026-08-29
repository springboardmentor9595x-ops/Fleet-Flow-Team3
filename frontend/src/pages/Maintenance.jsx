import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import SearchBar from "../components/SearchBar";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Maintenance.css";

const types = ["Oil Change", "Tire Replacement", "Engine Service", "Brake Service", "General Inspection"];
const emptyForm = { vehicle_id: "", maintenance_type: "Oil Change", service_date: "", next_service_date: "", cost: "", remarks: "" };

function alertLabel(record) {
  const due = new Date(record.service_date);
  const today = new Date();
  due.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  const days = Math.round((due - today) / 86400000);
  if (days === 5) return "Due in 5 days";
  if (days === 1) return "Due tomorrow";
  if (days === 0) return "Due today";
  if (days < 0) return "Overdue";
  return "Upcoming";
}

function Maintenance() {
  const { user } = useContext(AuthContext);
  const [records, setRecords] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [alerts, setAlerts] = useState({ upcoming: [], overdue: [] });
  const [form, setForm] = useState(emptyForm);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const canManage = ["Admin", "FleetManager"].includes(user?.role);
  const isDriver = user?.role === "Driver";

  const load = useCallback(async () => {
    try {
      const requests = [api.get("/maintenance/"), api.get("/maintenance/upcoming")];
      if (canManage) requests.push(api.get("/vehicles/"));
      const [maintenanceResponse, alertResponse, vehicleResponse] = await Promise.all(requests);
      setRecords(maintenanceResponse.data);
      setAlerts(alertResponse.data);
      setVehicles(vehicleResponse?.data || []);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to load maintenance records.");
    } finally {
      setLoading(false);
    }
  }, [canManage]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const vehicleName = useCallback((id) => vehicles.find((vehicle) => vehicle.vehicle_id === id)?.registration_number || id?.slice(0, 8) || "Assigned vehicle", [vehicles]);
  const overdueIds = useMemo(() => new Set(alerts.overdue.map((item) => item.maintenance_id)), [alerts]);
  const upcomingIds = useMemo(() => new Set(alerts.upcoming.map((item) => item.maintenance_id)), [alerts]);
  const activeAlerts = useMemo(() => [...alerts.upcoming, ...alerts.overdue].filter((item) => !["Completed", "Cancelled", "Resolved"].includes(item.status)), [alerts]);
  const filtered = useMemo(() => records.filter((record) => {
    const matchesQuery = !query || record.maintenance_type.toLowerCase().includes(query.toLowerCase()) || vehicleName(record.vehicle_id).toLowerCase().includes(query.toLowerCase());
    return matchesQuery && (filter === "All" || record.status === filter);
  }), [records, query, filter, vehicleName]);

  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError("");
    try {
      await api.post("/maintenance/", { ...form, service_date: new Date(form.service_date).toISOString(), next_service_date: form.next_service_date ? new Date(form.next_service_date).toISOString() : null, cost: form.cost === "" ? null : Number(form.cost), remarks: form.remarks || null });
      setForm(emptyForm); await load();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to schedule maintenance.");
    } finally { setSaving(false); }
  };

  const changeStatus = async (record, status) => {
    setSaving(true); setError("");
    try { await api.put(`/maintenance/${record.maintenance_id}`, { status }); await load(); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Unable to update maintenance status."); }
    finally { setSaving(false); }
  };

  const deleteCompletedRecord = async (record) => {
    const confirmed = window.confirm(
      `Delete the completed ${record.maintenance_type} record for ${vehicleName(record.vehicle_id)}? This cannot be undone.`
    );
    if (!confirmed) return;

    setSaving(true);
    setError("");
    try {
      await api.delete(`/maintenance/${record.maintenance_id}`);
      await load();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to delete the completed maintenance record.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <MainLayout><LoadingCard message="Loading maintenance schedule..." /></MainLayout>;
  return <MainLayout>
    <PageHeader eyebrow={isDriver ? "Driver Workspace" : "Fleet Management"} title={isDriver ? "My Vehicle Maintenance" : "Maintenance Schedule"} description={isDriver ? "Read-only maintenance for your currently assigned vehicle." : "Schedule service work, monitor due dates, and keep vehicle health current."} />
    {error && <div className="maintenance-error">{error}</div>}
    {activeAlerts.length > 0 && <section className="maintenance-alerts"><strong>Maintenance alerts</strong>{activeAlerts.map((item) => <span key={item.maintenance_id}>{alertLabel(item)}: {vehicleName(item.vehicle_id)}</span>)}</section>}
    {canManage && <form className="maintenance-form" onSubmit={submit}><h2>Schedule Maintenance</h2><div className="maintenance-form-grid"><label>Vehicle<select required value={form.vehicle_id} onChange={(event) => setForm({ ...form, vehicle_id: event.target.value })}><option value="">Select vehicle</option>{vehicles.map((vehicle) => <option key={vehicle.vehicle_id} value={vehicle.vehicle_id}>{vehicle.registration_number}</option>)}</select></label><label>Maintenance Type<select value={form.maintenance_type} onChange={(event) => setForm({ ...form, maintenance_type: event.target.value })}>{types.map((type) => <option key={type}>{type}</option>)}</select></label><label>Service Date<input required type="datetime-local" value={form.service_date} onChange={(event) => setForm({ ...form, service_date: event.target.value })} /></label><label>Next Service Date<input type="datetime-local" value={form.next_service_date} onChange={(event) => setForm({ ...form, next_service_date: event.target.value })} /></label><label>Cost<input min="0" step="0.01" type="number" value={form.cost} onChange={(event) => setForm({ ...form, cost: event.target.value })} /></label><label>Remarks<input value={form.remarks} onChange={(event) => setForm({ ...form, remarks: event.target.value })} /></label></div><button className="primary-button" disabled={saving}>{saving ? "Saving..." : "Schedule Maintenance"}</button></form>}
    <section className="maintenance-toolbar"><SearchBar value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search vehicle or maintenance type" /><select value={filter} onChange={(event) => setFilter(event.target.value)}><option value="All">All statuses</option><option value="Scheduled">Scheduled</option><option value="InProgress">In Progress</option><option value="Completed">Completed</option><option value="Resolved">Resolved</option><option value="Cancelled">Cancelled</option></select></section>
    {!filtered.length ? <EmptyState title="No maintenance records" description="Scheduled vehicle service will appear here." /> : <section className="maintenance-table"><table><thead><tr><th>Vehicle</th><th>Type</th><th>Service Date</th><th>Next Service</th><th>Cost</th><th>Status</th>{canManage && <th>Actions</th>}</tr></thead><tbody>{filtered.map((record) => <tr key={record.maintenance_id}><td>{vehicleName(record.vehicle_id)}</td><td>{record.maintenance_type}</td><td>{new Date(record.service_date).toLocaleString()}</td><td>{record.next_service_date ? new Date(record.next_service_date).toLocaleDateString() : "Not set"}</td><td>{record.cost == null ? "—" : `₹${record.cost}`}</td><td><StatusBadge status={record.status} /> {overdueIds.has(record.maintenance_id) && <small>🔴 Overdue</small>}{!overdueIds.has(record.maintenance_id) && upcomingIds.has(record.maintenance_id) && <small>🟡 {alertLabel(record)}</small>}</td>{canManage && <td className="maintenance-actions">{record.status === "Scheduled" && <button type="button" onClick={() => void changeStatus(record, "InProgress")} disabled={saving}>Start</button>}{record.status === "InProgress" && <><button type="button" onClick={() => void changeStatus(record, "Completed")} disabled={saving}>Complete</button><button type="button" onClick={() => void changeStatus(record, "Resolved")} disabled={saving}>Resolve</button></>}{record.status === "Completed" && <button type="button" className="maintenance-delete" onClick={() => void deleteCompletedRecord(record)} disabled={saving}>Delete</button>}</td>}</tr>)}</tbody></table></section>}
  </MainLayout>;
}

export default Maintenance;
