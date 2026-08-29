import { useContext, useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Shipments.css";

const emptyShipment = {
  tracking_number: "",
  source: "",
  destination: "",
  customer_name: "",
  shipment_weight: "",
  vehicle_id: "",
  driver_id: "",
  expected_delivery_at: "",
};

function ShipmentForm() {
  const { user } = useContext(AuthContext);
  const { shipmentId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(shipmentId);

  const [shipment, setShipment] = useState(emptyShipment);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const canCreate = ["Admin", "FleetManager"].includes(user?.role);
  const canAssign = ["Admin", "FleetManager"].includes(user?.role);
  const canEditDetails = ["Admin", "FleetManager"].includes(user?.role);

  useEffect(() => {
    const loadFormData = async () => {
      try {
        const requests = [api.get("/vehicles/"), api.get("/drivers/")];

        if (isEditing) {
          requests.push(api.get(`/shipments/${shipmentId}`));
        }

        const responses = await Promise.all(requests);

        setVehicles(responses[0].data);
        setDrivers(responses[1].data);

        if (isEditing) {
          const existing = responses[2].data;

          setShipment({
            ...existing,
            shipment_weight: String(existing.shipment_weight),
            vehicle_id: existing.vehicle_id || "",
            driver_id: existing.driver_id || "",
            expected_delivery_at: existing.expected_delivery_at
              ? existing.expected_delivery_at.slice(0, 16)
              : "",
          });
        }
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail ||
            "Unable to load shipment form data."
        );
      } finally {
        setLoading(false);
      }
    };

    if (canCreate || (isEditing && canAssign)) {
      const timer = window.setTimeout(loadFormData, 0);
      return () => window.clearTimeout(timer);
    }

    setLoading(false);
    return undefined;
  }, [canAssign, canCreate, isEditing, shipmentId]);

  if ((!isEditing && user && !canCreate) || (isEditing && user && !canAssign)) {
    return <Navigate to="/shipments" replace />;
  }

  const handleChange = (event) => {
    const { name, value } = event.target;
    setShipment((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    const assignmentPayload = {
      vehicle_id: shipment.vehicle_id || null,
      driver_id: shipment.driver_id || null,
    };

    try {
      if (isEditing) {
        const payload = canEditDetails
          ? {
              ...shipment,
              shipment_weight: Number(shipment.shipment_weight),
              expected_delivery_at: shipment.expected_delivery_at || null,
            }
          : assignmentPayload;

        await api.put(`/shipments/${shipmentId}`, payload);
        navigate(`/shipments/${shipmentId}`);
      } else {
        await api.post("/shipments/", {
          ...shipment,
          shipment_weight: Number(shipment.shipment_weight),
          vehicle_id: shipment.vehicle_id || null,
          driver_id: shipment.driver_id || null,
          expected_delivery_at: shipment.expected_delivery_at || null,
        });

        navigate("/shipments");
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || "Unable to save shipment."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading shipment form..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Shipment Management"
        title={isEditing ? "Assign or Edit Shipment" : "Create Shipment"}
        description={
          canEditDetails
            ? "Enter customer, route, and delivery details."
            : "Update the vehicle and driver assignment."
        }
      />

      <form className="shipment-form-saas-card" onSubmit={handleSubmit}>
        {error && <div className="shipment-saas-error">{error}</div>}

        <div className="shipment-form-saas-grid">
          <label className="shipment-floating-field">
            <input
              name="tracking_number"
              value={shipment.tracking_number}
              onChange={handleChange}
              placeholder=" "
              disabled={isEditing || !canEditDetails}
              required
            />
            <span>Tracking Number</span>
          </label>

          <label className="shipment-floating-field">
            <input
              name="customer_name"
              value={shipment.customer_name}
              onChange={handleChange}
              placeholder=" "
              disabled={isEditing && !canEditDetails}
              required
            />
            <span>Customer Name</span>
          </label>

          <label className="shipment-floating-field">
            <input
              name="source"
              value={shipment.source}
              onChange={handleChange}
              placeholder=" "
              disabled={isEditing && !canEditDetails}
              required
            />
            <span>Pickup Location</span>
          </label>

          <label className="shipment-floating-field">
            <input
              name="destination"
              value={shipment.destination}
              onChange={handleChange}
              placeholder=" "
              disabled={isEditing && !canEditDetails}
              required
            />
            <span>Delivery Location</span>
          </label>

          <label className="shipment-floating-field">
            <input
              name="shipment_weight"
              type="number"
              min="0.01"
              step="0.01"
              value={shipment.shipment_weight}
              onChange={handleChange}
              placeholder=" "
              disabled={isEditing && !canEditDetails}
              required
            />
            <span>Shipment Weight (kg)</span>
          </label>

          <label className="shipment-floating-field">
            <input
              name="expected_delivery_at"
              type="datetime-local"
              value={shipment.expected_delivery_at}
              onChange={handleChange}
              placeholder=" "
              disabled={isEditing && !canEditDetails}
            />
            <span>Expected Delivery</span>
          </label>

          <label className="shipment-select-field">
            <span>Assigned Vehicle</span>
            <select
              name="vehicle_id"
              value={shipment.vehicle_id}
              onChange={handleChange}
            >
              <option value="">Unassigned</option>
              {vehicles.map((vehicle) => (
                <option
                  key={vehicle.vehicle_id}
                  value={vehicle.vehicle_id}
                >
                  {vehicle.registration_number} · {vehicle.vehicle_type}
                </option>
              ))}
            </select>
          </label>

          <label className="shipment-select-field">
            <span>Assigned Driver</span>
            <select
              name="driver_id"
              value={shipment.driver_id}
              onChange={handleChange}
            >
              <option value="">Unassigned</option>
              {drivers.map((driver) => (
                <option key={driver.driver_id} value={driver.driver_id}>
                  {driver.full_name || "Unnamed driver"}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="shipment-form-saas-actions">
          <Link
            to={isEditing ? `/shipments/${shipmentId}` : "/shipments"}
            className="shipment-cancel-button"
          >
            Cancel
          </Link>

          <button type="submit" disabled={submitting}>
            {submitting
              ? "Saving Shipment..."
              : isEditing
                ? "Save Assignment"
                : "Create Shipment"}
          </button>
        </div>
      </form>
    </MainLayout>
  );
}

export default ShipmentForm;
