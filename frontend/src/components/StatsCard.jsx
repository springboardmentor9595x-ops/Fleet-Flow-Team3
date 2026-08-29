function StatsCard({ label, value, detail, icon = "•", tone = "purple" }) {
  return <article className={`stats-card ${tone}`}><span className="stats-icon">{icon}</span><p>{label}</p><strong>{value}</strong>{detail && <small>{detail}</small>}</article>;
}

export default StatsCard;
