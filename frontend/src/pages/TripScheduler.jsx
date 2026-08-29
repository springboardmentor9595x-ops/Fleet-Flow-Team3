import { useContext, useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Trip.css";

const initialTrip = {
  shipment_id: "",
  vehicle_id: "",
  driver_id: "",
  source: "",
  destination: "",
  route_type: "Fastest",
  planned_distance: "",
  estimated_duration: "",
};

function TripScheduler() {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();

  const [trip, setTrip] = useState(initialTrip);
  const [options, setOptions] = useState({
    shipments: [],
    vehicles: [],
    drivers: [],
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const allowed = ["Admin", "FleetManager"].includes(user?.role);

  useEffect(() => {
    if (!allowed) {
      return;
    }

    const loadOptions = async () => {
      try {
        const [shipments, vehicles, drivers] = await Promise.all([
          api.get("/shipments/"),
          api.get("/vehicles/"),
          api.get("/drivers/"),
        ]);

        setOptions({
          shipments: shipments.data.filter(
            (shipment) =>
              !["Delivered", "Cancelled"].includes(shipment.status)
          ),
          vehicles: vehicles.data,
          drivers: drivers.data,
        });
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail ||
            "Unable to load trip scheduling data."
        );
      } finally {
        setLoading(false);
      }
    };

    const timer = window.setTimeout(loadOptions, 0);
    return () => window.clearTimeout(timer);
  }, [allowed]);

  if (user && !allowed) {
    return <Navigate to="/trips" replace />;
  }

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading trip scheduler..." />
      </MainLayout>
    );
  }

  const change = (event) => {
    setTrip((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const selectShipment = (event) => {
    const shipment = options.shipments.find(
      (item) => item.shipment_id === event.target.value
    );

    setTrip((current) => ({
      ...current,
      shipment_id: event.target.value,
      source: shipment?.source || current.source,
      destination: shipment?.destination || current.destination,
      vehicle_id: shipment?.vehicle_id || current.vehicle_id,
      driver_id: shipment?.driver_id || current.driver_id,
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const response = await api.post("/trips/", {
        ...trip,
        planned_distance: null,
        estimated_duration: null,
        eta: null,
      });

      navigate(`/trips/${response.data.trip_id}`);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to schedule the trip."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Trip Management"
        title="Schedule Trip"
        description="Assign a shipment, vehicle, driver, and preferred route type."
      />

      <form className="trip-form-saas-card" onSubmit={submit}>
        {error && <div className="trip-saas-error">{error}</div>}

        <div className="trip-form-saas-grid">
          <label className="trip-select-field">
            <span>Shipment</span>
            <select
              value={trip.shipment_id}
              onChange={selectShipment}
              required
            >
              <option value="">Select shipment</option>
              {options.shipments.map((shipment) => (
                <option
                  key={shipment.shipment_id}
                  value={shipment.shipment_id}
                >
                  {shipment.tracking_number} · {shipment.source} to{" "}
                  {shipment.destination}
                </option>
              ))}
            </select>
          </label>

          <label className="trip-select-field">
            <span>Vehicle</span>
            <select
              name="vehicle_id"
              value={trip.vehicle_id}
              onChange={change}
              required
            >
              <option value="">Select vehicle</option>
              {options.vehicles.map((vehicle) => (
                <option
                  key={vehicle.vehicle_id}
                  value={vehicle.vehicle_id}
                >
                  {vehicle.registration_number}
                </option>
              ))}
            </select>
          </label>

          <label className="trip-select-field">
            <span>Driver</span>
            <select
              name="driver_id"
              value={trip.driver_id}
              onChange={change}
              required
            >
              <option value="">Select driver</option>
              {options.drivers.map((driver) => (
                <option key={driver.driver_id} value={driver.driver_id}>
                  {driver.full_name}
                </option>
              ))}
            </select>
          </label>

          <label className="trip-select-field">
            <span>Route Type</span>
            <select
              name="route_type"
              value={trip.route_type}
              onChange={change}
            >
              <option value="Fastest">Fastest</option>
              <option value="Shortest">Shortest</option>
              <option value="Eco">Eco</option>
              <option value="Balanced">Balanced</option>
            </select>
          </label>

          <label className="trip-floating-field">
            <input
              name="source"
              value={trip.source}
              onChange={change}
              placeholder=" "
              required
            />
            <span>Source</span>
          </label>

          <label className="trip-floating-field">
            <input
              name="destination"
              value={trip.destination}
              onChange={change}
              placeholder=" "
              required
            />
            <span>Destination</span>
          </label>

          <label className="trip-floating-field">
            <input
              name="planned_distance"
              type="number"
              min="0"
              value={trip.planned_distance}
              onChange={change}
              placeholder=" "
            />
            <span>Planned Distance (metres)</span>
          </label>

          <label className="trip-floating-field">
            <input
              name="estimated_duration"
              type="number"
              min="0"
              value={trip.estimated_duration}
              onChange={change}
              placeholder=" "
            />
            <span>Estimated Duration (seconds)</span>
          </label>
        </div>

        <div className="trip-form-saas-actions">
          <Link to="/trips" className="trip-cancel-button">
            Cancel
          </Link>

          <button type="submit" disabled={saving}>
            {saving ? "Scheduling..." : "Schedule Trip"}
          </button>
        </div>
      </form>
    </MainLayout>
  );
}

export default TripScheduler;
