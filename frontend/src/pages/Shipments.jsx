import { useContext, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import SearchBar from "../components/SearchBar";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Shipments.css";

const managerRoles = ["Admin", "FleetManager"];

function Shipments() {
  const { user } = useContext(AuthContext);
  const [shipments, setShipments] = useState([]);
  const [alerts, setAlerts] = useState({ approaching: [], overdue: [] });
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const canManage = managerRoles.includes(user?.role);
  const canCreate = managerRoles.includes(user?.role);

  useEffect(() => {
    const loadShipments = async () => {
      try {
        const shipmentRequest = api.get("/shipments/");
        const alertsRequest = canManage
          ? api.get("/shipments/alerts")
          : Promise.resolve({ data: { approaching: [], overdue: [] } });

        const [shipmentResponse, alertsResponse] = await Promise.all([
          shipmentRequest,
          alertsRequest,
        ]);

        setShipments(shipmentResponse.data);
        setAlerts(alertsResponse.data);
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail ||
            "Unable to load shipments."
        );
      } finally {
        setLoading(false);
      }
    };

    const timer = window.setTimeout(loadShipments, 0);
    return () => window.clearTimeout(timer);
  }, [canManage]);

  const alertIds = useMemo(
    () =>
      new Set([
        ...alerts.approaching.map((shipment) => shipment.shipment_id),
        ...alerts.overdue.map((shipment) => shipment.shipment_id),
      ]),
    [alerts]
  );

  const filteredShipments = useMemo(() => {
    const query = search.trim().toLowerCase();

    return shipments.filter((shipment) => {
      const matchesSearch =
        !query ||
        shipment.tracking_number.toLowerCase().includes(query) ||
        shipment.customer_name.toLowerCase().includes(query);

      const matchesStatus =
        statusFilter === "All" || shipment.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [search, shipments, statusFilter]);

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading shipment records..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Shipment Management"
        title="Shipments"
        description="Track delivery progress, customer orders, assignments, and delivery windows."
        actionLabel={canCreate ? "Create Shipment" : undefined}
        actionTo={canCreate ? "/shipments/add" : undefined}
      />

      {error && <div className="shipment-saas-error">{error}</div>}

      {(alerts.overdue.length > 0 || alerts.approaching.length > 0) && (
        <section className="shipment-alert-banner">
          <div>
            <strong>Delivery-window alerts</strong>
            <p>
              {alerts.overdue.length} overdue and{" "}
              {alerts.approaching.length} approaching delivery deadlines.
            </p>
          </div>
          <span>!</span>
        </section>
      )}

      {alerts.overdue.length > 0 && (
        <section className="shipment-delayed-cards">
          {alerts.overdue.map((shipment) => (
            <Link
              key={shipment.shipment_id}
              to={`/shipments/${shipment.shipment_id}`}
            >
              <span>Delayed delivery</span>
              <strong>{shipment.tracking_number}</strong>
              <p>
                {shipment.source} to {shipment.destination}
              </p>
            </Link>
          ))}
        </section>
      )}

      <section className="shipment-saas-toolbar">
        <div>
          <h2>Shipment directory</h2>
          <p>
            {filteredShipments.length} of {shipments.length} records shown
          </p>
        </div>

        <div className="shipment-saas-controls">
          <SearchBar
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search tracking number or customer"
          />

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            aria-label="Filter shipments by status"
          >
            <option value="All">All statuses</option>
            <option value="Created">Created</option>
            <option value="Assigned">Assigned</option>
            <option value="In Transit">In Transit</option>
            <option value="Delayed">Delayed</option>
            <option value="Delivered">Delivered</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>
      </section>

      {filteredShipments.length === 0 ? (
        <EmptyState
          title={shipments.length ? "No matching shipments" : "No shipments yet"}
          description={
            shipments.length
              ? "Try a different search term or status filter."
              : "Shipment records will appear here after they are created."
          }
          action={
            canCreate ? (
              <Link className="primary-button" to="/shipments/add">
                Create Shipment
              </Link>
            ) : null
          }
        />
      ) : (
        <section className="shipment-saas-table-card">
          <div className="shipment-saas-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Tracking</th>
                  <th>Customer</th>
                  <th>Route</th>
                  <th>Expected Delivery</th>
                  <th>Status</th>
                  <th className="shipment-actions-column">Actions</th>
                </tr>
              </thead>

              <tbody>
                {filteredShipments.map((shipment) => (
                  <tr key={shipment.shipment_id}>
                    <td>
                      <strong>{shipment.tracking_number}</strong>
                      <span>{shipment.shipment_weight} kg</span>
                    </td>
                    <td>{shipment.customer_name}</td>
                    <td>
                      <strong>{shipment.source}</strong>
                      <span>to {shipment.destination}</span>
                    </td>
                    <td>
                      {shipment.expected_delivery_at
                        ? new Date(
                            shipment.expected_delivery_at
                          ).toLocaleString()
                        : "Not set"}
                    </td>
                    <td>
                      <StatusBadge status={shipment.status} />
                      {(shipment.status === "Delayed" ||
                        alertIds.has(shipment.shipment_id)) && (
                        <small className="shipment-attention">
                          Attention needed
                        </small>
                      )}
                    </td>
                    <td className="shipment-row-actions">
                      <Link to={`/shipments/${shipment.shipment_id}`}>
                        View
                      </Link>
                      {canManage && (
                        <Link
                          className="shipment-edit-action"
                          to={`/shipments/${shipment.shipment_id}/edit`}
                        >
                          Edit
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </MainLayout>
  );
}

export default Shipments;
