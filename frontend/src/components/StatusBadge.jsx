function StatusBadge({ status = "Unknown" }) {
  const tone = String(status).toLowerCase().replaceAll(" ", "-");
  return <span className={`status-badge ${tone}`}>{status}</span>;
}

export default StatusBadge;
