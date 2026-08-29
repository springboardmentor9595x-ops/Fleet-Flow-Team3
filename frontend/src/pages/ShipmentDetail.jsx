import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Shipments.css";

const steps = ["Created", "Assigned", "In Transit", "Delivered"];

const roleActions = {
  Admin: {
    Created: ["Assigned", "Cancelled"],
    Assigned: ["In Transit", "Cancelled"],
    "In Transit": ["Delayed", "Delivered"],
    Delayed: ["In Transit"],
  },
  FleetManager: {
    Created: ["Assigned", "Cancelled"],
    Assigned: ["Cancelled"],
  },
  Dispatcher: {
    Created: ["Assigned"],
    "In Transit": ["Delayed"],
  },
  Driver: {
    Assigned: ["In Transit"],
    "In Transit": ["Delivered"],
  },
};

function ShipmentDetail() {
  const { user } = useContext(AuthContext);
  const { shipmentId } = useParams();

  const [shipment, setShipment] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [history, setHistory] = useState({ customer: [], vehicle: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const isManager = ["Admin", "FleetManager"].includes(user?.role);

  const loadShipment = useCallback(async () => {
    try {
      const response = await api.get(`/shipments/${shipmentId}`);
      setShipment(response.data);

      if (isManager) {
        const requests = [
          api.get("/drivers/"),
          api.get("/vehicles/"),
          api.get(
            `/shipments/history/customer/${encodeURIComponent(
              response.data.customer_name
            )}`
          ),
        ];

        if (response.data.vehicle_id) {
          requests.push(
            api.get(`/shipments/history/vehicle/${response.data.vehicle_id}`)
          );
        }

        const results = await Promise.all(requests);

        setDrivers(results[0].data);
        setVehicles(results[1].data);
        setHistory({
          customer: results[2].data,
          vehicle: response.data.vehicle_id ? results[3].data : [],
        });
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to load shipment details."
      );
    } finally {
      setLoading(false);
    }
  }, [isManager, shipmentId]);

  useEffect(() => {
    const timer = window.setTimeout(loadShipment, 0);
    return () => window.clearTimeout(timer);
  }, [loadShipment]);

  const driver = useMemo(
    () => drivers.find((item) => item.driver_id === shipment?.driver_id),
    [drivers, shipment]
  );

  const vehicle = useMemo(
    () => vehicles.find((item) => item.vehicle_id === shipment?.vehicle_id),
    [vehicles, shipment]
  );

  const actions = shipment
    ? roleActions[user?.role]?.[shipment.status] || []
    : [];

  const updateStatus = async (nextStatus) => {
    setUpdating(true);
    setError("");

    try {
      if (nextStatus === "Cancelled") {
        await api.delete(`/shipments/${shipmentId}`);
      } else {
        await api.patch(`/shipments/${shipmentId}/status`, {
          status: nextStatus,
        });
      }

      await loadShipment();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to update shipment status."
      );
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading shipment details..." />
      </MainLayout>
    );
  }

  if (!shipment) {
    return (
      <MainLayout>
        <div className="shipment-saas-error">
          {error || "Shipment not found."}
        </div>
      </MainLayout>
    );
  }

  const currentStep =
    shipment.status === "Delayed"
      ? 2
      : steps.indexOf(shipment.status);

  return (
    <MainLayout>
      <PageHeader
        eyebrow={`Shipment ${shipment.tracking_number}`}
        title={`${shipment.source} to ${shipment.destination}`}
        description={`Customer: ${shipment.customer_name}`}
      />

      {error && <div className="shipment-saas-error">{error}</div>}

      {shipment.status === "Delayed" && (
        <div className="shipment-detail-alert">
          <strong>Delayed shipment</strong>
          <span>
            Review the delivery timeline and coordinate the next status update.
          </span>
        </div>
      )}

      <section className="shipment-detail-hero">
        <div>
          <StatusBadge status={shipment.status} />
          <h2>{shipment.tracking_number}</h2>
          <p>
            Created {new Date(shipment.created_at).toLocaleString()}
          </p>
        </div>

        {isManager && (
          <Link
            className="primary-button"
            to={`/shipments/${shipmentId}/edit`}
          >
            Assign / Edit Shipment
          </Link>
        )}
      </section>

      <section className="shipment-progress-card">
        <div className="shipment-progress-heading">
          <div>
            <p>Delivery progress</p>
            <h2>Shipment lifecycle</h2>
          </div>
          <span>{shipment.status}</span>
        </div>

        <div className="shipment-progress-timeline">
          {steps.map((step, index) => {
            const completed =
              shipment.status !== "Cancelled" && index <= currentStep;

            return (
              <div
                className={`shipment-timeline-step ${
                  completed ? "complete" : ""
                }`}
                key={step}
              >
                <span>{index + 1}</span>
                <strong>{step}</strong>
              </div>
            );
          })}
        </div>
      </section>

      <section className="shipment-detail-grid">
        <article>
          <p>Customer details</p>
          <h2>{shipment.customer_name}</h2>
          <div>
            <span>Shipment weight</span>
            <strong>{shipment.shipment_weight} kg</strong>
          </div>
          <div>
            <span>Expected delivery</span>
            <strong>
              {shipment.expected_delivery_at
                ? new Date(shipment.expected_delivery_at).toLocaleString()
                : "Not set"}
            </strong>
          </div>
        </article>

        <article>
          <p>Assignment</p>
          <h2>Vehicle and driver</h2>
          <div>
            <span>Assigned vehicle</span>
            <strong>
              {vehicle
                ? `${vehicle.registration_number} · ${vehicle.vehicle_type}`
                : "Unassigned"}
            </strong>
          </div>
          <div>
            <span>Assigned driver</span>
            <strong>{driver?.full_name || "Unassigned"}</strong>
          </div>
        </article>

        <article>
          <p>Route</p>
          <h2>Delivery path</h2>
          <div>
            <span>Pickup</span>
            <strong>{shipment.source}</strong>
          </div>
          <div>
            <span>Destination</span>
            <strong>{shipment.destination}</strong>
          </div>
        </article>
      </section>

      {actions.length > 0 && (
        <section className="shipment-lifecycle-actions">
          <div>
            <p>Available status updates</p>
            <h2>Manage shipment lifecycle</h2>
          </div>

          <div>
            {actions.map((nextStatus) => (
              <button
                key={nextStatus}
                className={
                  nextStatus === "Cancelled"
                    ? "shipment-danger-action"
                    : "shipment-primary-action"
                }
                onClick={() => updateStatus(nextStatus)}
                disabled={updating}
              >
                {updating ? "Updating..." : nextStatus}
              </button>
            ))}
          </div>
        </section>
      )}

      {isManager && (
        <section className="shipment-history-cards">
          <article>
            <span>Customer history</span>
            <strong>{history.customer.length}</strong>
            <p>Shipment record(s) for {shipment.customer_name}</p>
          </article>

          <article>
            <span>Vehicle history</span>
            <strong>{history.vehicle.length}</strong>
            <p>Shipment record(s) for this assigned vehicle</p>
          </article>
        </section>
      )}
    </MainLayout>
  );
}

export default ShipmentDetail;
