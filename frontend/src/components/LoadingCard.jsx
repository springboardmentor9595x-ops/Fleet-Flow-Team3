function LoadingCard({ message = "Loading..." }) {
  return <div className="loading-card"><span className="loading-spinner" /><p>{message}</p></div>;
}

export default LoadingCard;
