import { useContext, useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./VehicleForm.css";

const emptyVehicle = {
  registration_number: "",
  vehicle_type: "",
  brand: "",
  model: "",
  manufacture_year: "",
  fuel_type: "",
  capacity: "",
  status: "Available",
};

function VehicleForm() {
  const { user } = useContext(AuthContext);
  const { vehicleId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(vehicleId);

  const [vehicle, setVehicle] = useState(emptyVehicle);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(isEditing);
  const [submitting, setSubmitting] = useState(false);

  const canManageVehicles = ["Admin", "FleetManager"].includes(user?.role);

  useEffect(() => {
    if (!isEditing) {
      return;
    }

    const loadVehicle = async () => {
      try {
        const response = await api.get(`/vehicles/${vehicleId}`);

        setVehicle({
          ...response.data,
          manufacture_year: String(response.data.manufacture_year),
          capacity: String(response.data.capacity),
        });
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail || "Unable to load vehicle."
        );
      } finally {
        setLoading(false);
      }
    };

    const timer = window.setTimeout(loadVehicle, 0);
    return () => window.clearTimeout(timer);
  }, [isEditing, vehicleId]);

  if (user && !canManageVehicles) {
    return <Navigate to="/vehicles" replace />;
  }

  const handleChange = (event) => {
    const { name, value } = event.target;
    setVehicle((currentVehicle) => ({
      ...currentVehicle,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    const payload = {
      ...vehicle,
      manufacture_year: Number(vehicle.manufacture_year),
      capacity: Number(vehicle.capacity),
    };

    try {
      if (isEditing) {
        await api.put(`/vehicles/${vehicleId}`, payload);
      } else {
        await api.post("/vehicles/", {
          registration_number: payload.registration_number,
          vehicle_type: payload.vehicle_type,
          brand: payload.brand,
          model: payload.model,
          manufacture_year: payload.manufacture_year,
          fuel_type: payload.fuel_type,
          capacity: payload.capacity,
        });
      }

      navigate("/vehicles");
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || "Unable to save vehicle."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <LoadingCard message="Loading vehicle details..." />
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageHeader
        eyebrow="Fleet Management"
        title={isEditing ? "Edit Vehicle" : "Add Vehicle"}
        description="Enter the vehicle details used for fleet monitoring and trip assignments."
      />

      <form className="vehicle-form-saas-card" onSubmit={handleSubmit}>
        {error && <div className="vehicle-form-error">{error}</div>}

        <div className="vehicle-form-saas-grid">
          <label className="vehicle-floating-field">
            <input
              name="registration_number"
              value={vehicle.registration_number}
              onChange={handleChange}
              placeholder=" "
              maxLength="20"
              required
            />
            <span>Registration Number</span>
          </label>

          <label className="vehicle-floating-field">
            <input
              name="vehicle_type"
              value={vehicle.vehicle_type}
              onChange={handleChange}
              placeholder=" "
              maxLength="50"
              required
            />
            <span>Vehicle Type</span>
          </label>

          <label className="vehicle-floating-field">
            <input
              name="brand"
              value={vehicle.brand}
              onChange={handleChange}
              placeholder=" "
              maxLength="50"
              required
            />
            <span>Brand</span>
          </label>

          <label className="vehicle-floating-field">
            <input
              name="model"
              value={vehicle.model}
              onChange={handleChange}
              placeholder=" "
              maxLength="50"
              required
            />
            <span>Model</span>
          </label>

          <label className="vehicle-floating-field">
            <input
              name="manufacture_year"
              type="number"
              value={vehicle.manufacture_year}
              onChange={handleChange}
              placeholder=" "
              min="1900"
              max="2100"
              required
            />
            <span>Manufacture Year</span>
          </label>

          <label className="vehicle-floating-field">
            <input
              name="fuel_type"
              value={vehicle.fuel_type}
              onChange={handleChange}
              placeholder=" "
              maxLength="30"
              required
            />
            <span>Fuel Type</span>
          </label>

          <label className="vehicle-floating-field">
            <input
              name="capacity"
              type="number"
              value={vehicle.capacity}
              onChange={handleChange}
              placeholder=" "
              min="1"
              required
            />
            <span>Capacity</span>
          </label>

          {isEditing && (
            <label className="vehicle-select-field">
              <span>Status</span>
              <select
                name="status"
                value={vehicle.status}
                onChange={handleChange}
              >
                <option value="Available">Available</option>
                <option value="Assigned">Assigned</option>
                <option value="Maintenance">Maintenance</option>
                <option value="In Transit">In Transit</option>
              </select>
            </label>
          )}
        </div>

        <div className="vehicle-form-saas-actions">
          <Link to="/vehicles" className="vehicle-cancel-button">
            Cancel
          </Link>

          <button type="submit" disabled={submitting}>
            {submitting
              ? "Saving Vehicle..."
              : isEditing
                ? "Save Changes"
                : "Add Vehicle"}
          </button>
        </div>
      </form>
    </MainLayout>
  );
}

export default VehicleForm;