import { useContext, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatsCard from "../components/StatsCard";
import MainLayout from "../layouts/MainLayout";
import { AuthContext } from "../context/auth-context";
import api from "../services/api";
import "./Reports.css";

const REPORTS = [
  { id: "fleet-utilization", title: "Fleet Utilization", description: "Current fleet status and utilization overview.", roles: ["Admin", "FleetManager"] },
  { id: "fuel-consumption", title: "Fuel Consumption", description: "Fuel usage, cost, mileage, and refill totals by vehicle.", roles: ["Admin", "FleetManager"] },
  { id: "driver-performance", title: "Driver Performance", description: "Completed trips, delivery outcomes, and attendance data.", roles: ["Admin", "FleetManager"] },
  { id: "delivery-performance", title: "Delivery Performance", description: "Shipment delivery, delay, and on-time performance metrics.", roles: ["Admin", "FleetManager", "Dispatcher"] },
  { id: "maintenance", title: "Maintenance", description: "Maintenance cost, frequency, upcoming work, and overdue records.", roles: ["Admin", "FleetManager"] },
];

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const labelize = (value) => String(value || "").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const formatValue = (value) => {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (typeof value === "object") return Object.entries(value).map(([key, item]) => `${labelize(key)}: ${formatValue(item)}`).join(" · ");
  return String(value);
};
const requestError = (error, fallback) => {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(" ");
  if (typeof detail === "string") return detail;
  if (error.response?.status === 403) return "You are not authorised to access this report.";
  if (error.response?.status === 401) return "Your session has expired. Please sign in again.";
  return fallback;
};

function Reports() {
  const { user } = useContext(AuthContext);
  const allowedReports = useMemo(() => REPORTS.filter((report) => report.roles.includes(user?.role)), [user?.role]);
  const [selectedId, setSelectedId] = useState("fleet-utilization");
  const [period, setPeriod] = useState("previous_week");
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState("");
  const [error, setError] = useState("");
  const selectedReport = allowedReports.find((item) => item.id === selectedId) || allowedReports[0];
  const yearOptions = Array.from({ length: 7 }, (_, index) => new Date().getFullYear() - 3 + index);

  const buildParams = () => {
    const params = { period };
    if (period === "monthly") { params.month = month; params.year = year; }
    if (period === "custom") {
      if (!startDate || !endDate) { setError("Choose both a start date and an end date."); return null; }
      if (startDate > endDate) { setError("Start date must be on or before end date."); return null; }
      params.start_date = startDate; params.end_date = endDate;
    }
    return params;
  };
  const generateReport = async () => {
    if (!selectedReport) return;
    const params = buildParams(); if (!params) return;
    setLoading(true); setError("");
    try { const response = await api.get(`/reports/${selectedReport.id}`, { params }); setReport(response.data); }
    catch (requestFailure) { setReport(null); setError(requestError(requestFailure, "Unable to generate this report.")); }
    finally { setLoading(false); }
  };
  const downloadReport = async (format) => {
    if (!selectedReport) return;
    const params = buildParams(); if (!params) return;
    setExporting(format); setError("");
    try {
      const response = await api.get(`/reports/${selectedReport.id}/export/${format}`, { params, responseType: "blob" });
      const extension = format === "pdf" ? "pdf" : "xlsx";
      const mimeType = format === "pdf" ? "application/pdf" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
      const url = window.URL.createObjectURL(new Blob([response.data], { type: mimeType }));
      const link = document.createElement("a"); link.href = url; link.download = `${selectedReport.id}-report.${extension}`;
      document.body.appendChild(link); link.click(); link.remove(); window.URL.revokeObjectURL(url);
    } catch (requestFailure) { setError(requestError(requestFailure, `Unable to export the ${format.toUpperCase()} report.`)); }
    finally { setExporting(""); }
  };
  const rows = useMemo(() => {
    if (!report?.data) return [];
    return report.data.flatMap((item) => Array.isArray(item.items) ? item.items.map((entry) => ({ section: item.section, ...entry })) : [item]);
  }, [report]);
  const columns = useMemo(() => Array.from(new Set(rows.flatMap((row) => Object.keys(row)))), [rows]);

  if (user && allowedReports.length === 0) return <Navigate to="/dashboard" replace />;

  return <MainLayout>
    <PageHeader eyebrow="Analytics" title="Reports & Export" description="Generate, preview and export fleet reports." />
    <section className="reports-controls" aria-label="Report controls">
      <div className="reports-control-group"><label htmlFor="report-type">Report type</label><select id="report-type" value={selectedReport?.id || ""} onChange={(event) => { setSelectedId(event.target.value); setReport(null); setError(""); }}>{allowedReports.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></div>
      <div className="reports-control-group"><label htmlFor="report-period">Date range</label><select id="report-period" value={period} onChange={(event) => { setPeriod(event.target.value); setError(""); }}><option value="previous_week">Previous Week</option><option value="monthly">Monthly</option><option value="custom">Custom</option></select></div>
      {period === "monthly" && <><div className="reports-control-group"><label htmlFor="report-month">Month</label><select id="report-month" value={month} onChange={(event) => setMonth(Number(event.target.value))}>{MONTHS.map((name, index) => <option key={name} value={index + 1}>{name}</option>)}</select></div><div className="reports-control-group"><label htmlFor="report-year">Year</label><select id="report-year" value={year} onChange={(event) => setYear(Number(event.target.value))}>{yearOptions.map((item) => <option key={item} value={item}>{item}</option>)}</select></div></>}
      {period === "custom" && <><div className="reports-control-group"><label htmlFor="report-start-date">Start date</label><input id="report-start-date" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></div><div className="reports-control-group"><label htmlFor="report-end-date">End date</label><input id="report-end-date" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></div></>}
      <button className="primary-button reports-generate" onClick={() => void generateReport()} disabled={loading || !selectedReport}>{loading ? "Generating..." : "Generate report"}</button>
    </section>
    <section className="reports-catalog" aria-label="Available reports">{allowedReports.map((item) => <article className={`reports-catalog-card ${selectedReport?.id === item.id ? "selected" : ""}`} key={item.id}><h2>{item.title}</h2><p>{item.description}</p><button onClick={() => { setSelectedId(item.id); setReport(null); setError(""); }}>Generate / View</button></article>)}</section>
    {error && <div className="reports-error" role="alert">{error}</div>}
    {loading && <LoadingCard message="Generating report from FleetFlow records..." />}
    {!loading && report && <section className="reports-preview"><header className="reports-preview-heading"><div><p>{labelize(report.report_type)}</p><h2>{selectedReport?.title} report</h2><span>{report.period.start_date} to {report.period.end_date}</span></div><div className="reports-export-actions"><button onClick={() => void downloadReport("pdf")} disabled={Boolean(exporting)}>{exporting === "pdf" ? "Exporting PDF..." : "Export PDF"}</button><button className="primary-button" onClick={() => void downloadReport("excel")} disabled={Boolean(exporting)}>{exporting === "excel" ? "Exporting Excel..." : "Export Excel"}</button></div></header><div className="reports-summary-grid">{Object.entries(report.summary || {}).map(([key, value]) => <StatsCard key={key} label={labelize(key)} value={formatValue(value)} icon="▦" tone="purple" />)}</div>{report.limitations?.length > 0 && <div className="reports-limitations"><strong>Data notes</strong><ul>{report.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>}{rows.length ? <div className="reports-table-wrap"><table><thead><tr>{columns.map((column) => <th key={column}>{labelize(column)}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.vehicle_id || row.driver_id || row.shipment_id || row.maintenance_id || row.section || "row"}-${index}`}>{columns.map((column) => <td key={column}>{formatValue(row[column])}</td>)}</tr>)}</tbody></table></div> : <EmptyState title="No report data" description="No records match the selected report period." />}</section>}
    {!loading && !report && !error && <EmptyState title="Choose a report" description="Select an authorised report and generate a preview for the chosen period." />}
  </MainLayout>;
}

export default Reports;
