function EmptyState({ title = "Nothing here yet", description = "There are no records to display.", action }) {
  return <div className="empty-state"><span className="empty-state-icon">○</span><h2>{title}</h2><p>{description}</p>{action}</div>;
}

export default EmptyState;
