import { Link } from "react-router-dom";

function PageHeader({ eyebrow = "FleetFlow", title, description, actionLabel, actionTo }) {
  return <header className="page-header"><div><p className="page-eyebrow">{eyebrow}</p><h1>{title}</h1>{description && <p className="page-description">{description}</p>}</div>{actionLabel && actionTo && <Link className="primary-button" to={actionTo}>{actionLabel}</Link>}</header>;
}

export default PageHeader;
